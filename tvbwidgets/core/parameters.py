"""
A collection of parameter related classes and functions.
"""

from copy import deepcopy
from typing import List, Any, Optional
from dataclasses import dataclass, field
import numpy as np
from tvb.analyzers import compute_variance_global_metric
from tvb.datatypes.connectivity import Connectivity
from tvb.datatypes.time_series import TimeSeriesRegion
from tvb.simulator.simulator import Simulator
import os
from dask.distributed import Client
from tvb.basic.neotraits.api import Range

import logging

from tvbwidgets.core.pse.pse_data import PSEData, PSEStorage

log = logging.getLogger(__name__)


class ParamGetter:
    pass


@dataclass
class SimSeq:
    "A sequence of simulator configurations."
    template: Simulator
    params: List[str]
    values: List[List[Any]]
    getters: Optional[List[Optional[ParamGetter]]] = None  # is the first Optional needed?

    # TODO consider transpose, so a param can have a remote data source
    # to load when constructing the sequence

    def __iter__(self):
        self.pos = 0
        return self

    def __post_init__(self):
        self.template.configure()  # deepcopy doesn't work on un-configured simulator o_O
        if self.getters is None:
            self.getters = [None] * len(self.params)
        else:
            assert len(self.getters) == len(self.params)

    def __next__(self):
        if self.pos >= len(self.values):
            raise StopIteration
        obj = deepcopy(self.template)
        updates = zip(self.params, self.getters, self.values[self.pos])
        for key, getter, val in updates:
            if getter is not None:
                val = getter(val)
            exec(f'obj.{key} = val',
                 {'obj': obj, 'val': val})
        self.pos += 1
        return obj


class Metric:
    "A summary statistic for a simulation."

    def __call__(self, t, y) -> np.ndarray:  # what about multi metric returning dict of statistics? Also, chaining?
        pass


class NodeVariability(Metric):
    "A simplistic simulation statistic."

    def __call__(self, t, y):
        return np.std(y[t > (t[-1] / 2), 0, :, 0], axis=0)


class Variability(Metric):
    "A simplistic simulation statistic."

    def __call__(self, t, y):
        a = np.std(y[t > (t[-1] / 2), 0, :, 0], axis=0)
        return np.mean(a)


class GlobalVariance(Metric):
    "A simplistic simulation statistic."

    def __init__(self, simulator):
        self.sim = simulator

    def __call__(self, t, y):
        ts = TimeSeriesRegion(connectivity=self.sim.connectivity, sample_period=self.sim.period)
        ts.data = y
        return compute_variance_global_metric(ts)


class Reduction:
    pass


@dataclass
class SaveMetricsToDisk(Reduction):
    filename: str

    def __call__(self, metrics_mat: np.ndarray) -> None:
        np.save(self.filename, metrics_mat)


# or save to a bucket or do SNPE then to a bucket, etc.

@dataclass
class SaveDataToDisk(Reduction):
    param1: str
    param2: str
    range1: list
    range2: list
    metrics: list
    file_name: str

    def __call__(self, metric_data: np.ndarray) -> None:
        metrics_data_np = np.array(metric_data)
        # nmb_elems1 = int((self.range1[1] - self.range1[0]) / self.range1[2])
        # nmb_elems2 = int((self.range2[1] - self.range2[0]) / self.range2[2])
        # if self.range1[1] % self.range1[2] != 0:
        #     nmb_elems1 += 1
        # if self.range2[1] % self.range2[2] != 0:
        #     nmb_elems2 += 1
        nmb_elems1 = 0
        nmb_elems2 = 0
        for _ in np.arange(self.range1[0], self.range1[1], self.range1[2]):
            nmb_elems1 += 1
        for _ in np.arange(self.range2[0], self.range2[1], self.range2[2]):
            nmb_elems2 += 1

        pse_result = PSEData()
        pse_result.x_title = self.param1
        pse_result.y_title = self.param2
        pse_result.x_value = Range(lo=self.range1[0], hi=self.range1[1], step=self.range1[2])
        pse_result.y_value = Range(lo=self.range2[0], hi=self.range2[1], step=self.range2[2])
        pse_result.metrics_names = self.metrics
        pse_result.results = metrics_data_np.reshape(nmb_elems1, nmb_elems2)
        self.file_name += ".h5"

        f = PSEStorage(self.file_name)
        f.store(pse_result)
        f.close()


@dataclass
class PostProcess:
    metrics: List[Metric]
    reduction: Reduction


class Exec:
    pass


@dataclass
class JobLibExec:
    seq: SimSeq
    post: PostProcess
    backend: Optional[Any]
    checkpoint_dir: Optional[str]

    def _checkpoint(self, result, i):
        if self.checkpoint_dir is not None:
            np.save(os.path.join(self.checkpoint_dir, f'{i}.npy'), result)

    def _load_checkpoint(self, i):
        if self.checkpoint_dir is None:
            return None
        checkpoint_file = os.path.join(self.checkpoint_dir, f'{i}.npy')
        if not os.path.exists(checkpoint_file):
            return None
        result = np.load(checkpoint_file, allow_pickle=True)
        return result

    def _init_checkpoint(self):
        if self.checkpoint_dir is not None:
            if os.path.exists(self.checkpoint_dir):
                log.info(f"Reusing existing checkpoint dir {self.checkpoint_dir}")
                # TODO consistency check
            else:
                os.mkdir(self.checkpoint_dir)
                np.savetxt(os.path.join(self.checkpoint_dir, 'params.txt'), self.seq.params, fmt='%s')
                np.save(os.path.join(self.checkpoint_dir, 'param_vals.npy'), self.seq.values)

    def __call__(self, n_jobs=-1):
        self._init_checkpoint()
        from joblib import Parallel, delayed
        pool = Parallel(n_jobs)

        @delayed
        def job(sim, i):
            result = self._load_checkpoint(i)
            if result is None:
                if self.backend is not None:
                    runner = self.backend()
                    (t, y), = runner.run_sim(sim.configure())
                else:
                    (t, y), = sim.configure().run()
                result = np.hstack([m(t, y) for m in self.post.metrics])
                self._checkpoint(result, i)
            return result

        metrics = pool(job(_, i) for i, _ in enumerate(self.seq))
        self.post.reduction(metrics)


@dataclass
class DaskExec(JobLibExec):

    def __call__(self, client: Client):
        self._init_checkpoint()

        checkpoint_dir = self.checkpoint_dir
        if checkpoint_dir is not None:
            checkpoint_dir = os.path.abspath(checkpoint_dir)

        def _checkpoint(result, i):
            if checkpoint_dir is not None:
                np.save(os.path.join(checkpoint_dir, f'{i}.npy'), result)

        def _load_checkpoint(i):
            if checkpoint_dir is None:
                return None
            checkpoint_file = os.path.join(checkpoint_dir, f'{i}.npy')
            if not os.path.exists(checkpoint_file):
                return None
            result = np.load(checkpoint_file, allow_pickle=True)
            return result

        def job(i, sim):
            result = _load_checkpoint(i)
            if result is None:
                if self.backend is not None:
                    runner = self.backend()
                    (t, y), = runner.run_sim(sim.configure())
                else:
                    (t, y), = sim.configure().run()
                result = np.hstack([m(t, y) for m in self.post.metrics])
                _checkpoint(result, i)
            return result

        def reduction(vals):
            return self.post.reduction(vals)

        metrics = client.map(job, *list(zip(*enumerate(self.seq))))

        if self.post.reduction is not None:
            reduced = client.submit(reduction, metrics)
            return reduced.result()
        else:
            return metrics


def launch_local_param(param1, param2, range1, range2, metrics, file_name):
    # TODO instead of receiving the ranges as parameters, we will receive the lists already computed for both parameters
    input_values = []
    for elem1 in np.arange(range1[0], range1[1], range1[2]):
        for elem2 in np.arange(range2[0], range2[1], range2[2]):
            input_values.append([np.array([elem1]), np.array([elem2])])

    # TODO simulator will be given as a parameter to the function, we do not need to create a new one
    sim = Simulator(
        connectivity=Connectivity.from_file()).configure()  # deepcopy doesn't work on un-configured simulator o_O
    seq = SimSeq(
        template=sim,
        params=[param1, param2],
        values=input_values
    )
    pp = PostProcess(
        # TODO a particular class for every METRIC(instead of Variability class)
        metrics=[Variability()],
        reduction=SaveDataToDisk(param1, param2, range1, range2, metrics, file_name),
    )
    exe = JobLibExec(seq=seq, post=pp, backend=None, checkpoint_dir="C:\\Users\\teodora.misan\\Documents\\localLaunch")
    exe(n_jobs=4)
