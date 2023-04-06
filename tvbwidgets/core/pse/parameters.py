# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#
"""
A collection of parameter related classes and functions.
- Temporary copy from tvb-inversion package

.. moduleauthor:: Fousek Jan <jan.fousek@univ-amu.fr>
"""

from copy import deepcopy
from typing import List, Any, Optional
from dataclasses import dataclass
import numpy as np
from tvb.analyzers.metric_variance_global import compute_variance_global_metric
from tvb.analyzers.metric_kuramoto_index import compute_kuramoto_index_metric
from tvb.analyzers.metric_proxy_metastability import compute_proxy_metastability_metric
from tvb.analyzers.metric_variance_of_node_variance import compute_variance_of_node_variance_metric
from tvb.datatypes.time_series import TimeSeries
from tvb.simulator.simulator import Simulator
import os
from joblib import Parallel, delayed
import logging
from tvbwidgets.core.pse.pse_data import PSEData, PSEStorage
log = logging.getLogger(__name__)

try:
    from dask.distributed import Client
except ImportError:
    log.info("ImportError: Dask dependency is not included, so this functionality won't be available")
    Client = object


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


class GlobalVariance(Metric):

    def __init__(self, sample_period, start_point=500, segment=4):
        self.sample_period = sample_period
        self.start_point = start_point
        self.segment = segment

    def __call__(self, t, y):
        ts = TimeSeries(sample_period=self.sample_period)
        ts.data = y
        return compute_variance_global_metric({"time_series": ts, "start_point": self.start_point,
                                               "segment": self.segment})


class KuramotoIndex(Metric):

    def __init__(self, sample_period):
        self.sample_period = sample_period

    def __call__(self, t, y):
        ts = TimeSeries(sample_period=self.sample_period)
        ts.data = y
        return compute_kuramoto_index_metric({"time_series": ts})


class ProxyMetastabilitySynchrony(Metric):

    def __init__(self, mode, sample_period, start_point=500, segment=4):
        self.mode = mode
        self.sample_period = sample_period
        self.start_point = start_point
        self.segment = segment

    def __call__(self, t, y):
        ts = TimeSeries(sample_period=self.sample_period)
        ts.data = y
        return compute_proxy_metastability_metric({"time_series": ts, "start_point": self.start_point,
                                                   "segment": self.segment})[self.mode]


class VarianceNodeVariance(Metric):

    def __init__(self, sample_period, start_point=500, segment=4):
        self.sample_period = sample_period
        self.start_point = start_point
        self.segment = segment

    def __call__(self, t, y):
        ts = TimeSeries(sample_period=self.sample_period)
        ts.data = y
        return compute_variance_of_node_variance_metric({"time_series": ts, "start_point": self.start_point,
                                                         "segment": self.segment})


METRICS = ['GlobalVariance', 'KuramotoIndex', 'ProxyMetastabilitySynchrony Metastability',
           'ProxyMetastabilitySynchrony Synchrony', 'VarianceNodeVariance']


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
    x_values: list
    y_values: list
    metrics: list
    file_name: str

    def __call__(self, metric_data: np.ndarray) -> None:
        metrics_data_np = np.array(metric_data)
        pse_result = PSEData()
        pse_result.x_title = self.param1
        pse_result.y_title = self.param2

        if self.param1 == "connectivity":
            id_values = [val.title[0:25] + "..." for val in self.x_values]
            pse_result.x_value = id_values
        else:
            pse_result.x_value = self.x_values
        if self.param2 == "connectivity":
            id_values = [val.title[0:25] + "..." for val in self.y_values]
            pse_result.y_value = id_values
        else:
            pse_result.y_value = self.y_values

        pse_result.metrics_names = self.metrics
        pse_result.results = metrics_data_np.reshape(len(self.metrics), len(self.x_values), len(self.y_values))
        if ".h5" not in self.file_name:
            self.file_name += ".h5"

        f = PSEStorage(self.file_name)
        f.store(pse_result)
        log.info(str(self.file_name) + " file created")
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
        log.info("Simulation starts")
        self._init_checkpoint()
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
        log.info("Local launch finished")


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


def compute_metrics(sim, metrics):
    computed_metrics = []

    for metric in metrics:
        if metric == "GlobalVariance":
            resulted_metric = (GlobalVariance(sim.monitors[0].period))
        elif metric == "KuramotoIndex":
            resulted_metric = (KuramotoIndex(sim.monitors[0].period))
        elif metric == "ProxyMetastabilitySynchrony Metastability":
            resulted_metric = (ProxyMetastabilitySynchrony("Metastability", sim.monitors[0].period))
        elif metric == "ProxyMetastabilitySynchrony Synchrony":
            resulted_metric = (ProxyMetastabilitySynchrony("Synchrony", sim.monitors[0].period))
        else:
            resulted_metric = (VarianceNodeVariance(sim.monitors[0].period))
        computed_metrics.append(resulted_metric)

    return computed_metrics


def launch_local_param(simulator, param1, param2, x_values, y_values, metrics, file_name):
    input_values = []
    for elem1 in x_values:
        for elem2 in y_values:
            if param1 == "conduction_speed" or param1 == "connectivity":
                el1_value = elem1
            else:
                el1_value = np.array([elem1])
            if param2 == "conduction_speed" or param2 == "connectivity":
                el2_value = elem2
            else:
                el2_value = np.array([elem2])
            input_values.append([el1_value, el2_value])

    sim = simulator.configure()  # deepcopy doesn't work on un-configured simulator o_O
    seq = SimSeq(
        template=sim,
        params=[param1, param2],
        values=input_values
    )
    pp = PostProcess(
        metrics=compute_metrics(sim, metrics),
        reduction=SaveDataToDisk(param1, param2, x_values, y_values, metrics, file_name),
    )
    exe = JobLibExec(seq=seq, post=pp, backend=None, checkpoint_dir=None)
    exe(n_jobs=4)
