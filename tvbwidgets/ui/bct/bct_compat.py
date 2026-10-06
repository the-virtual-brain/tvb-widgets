
import numpy as np
import bct.algorithms.modularity as _bct_modularity
def apply_bct_patches():

    if getattr(_bct_modularity, "_tvb_ls2ci_patched", False):
        return

    def _patched_ls2ci(ls, zeroindexed=False):
        if ls is None or len(ls) == 0:
            return ()

        nr_indices = sum(map(len, ls))
        ci = np.zeros((nr_indices,), dtype=int)
        z = int(not zeroindexed)

        for i, group in enumerate(ls):
            for node in group:
                ci[node] = i + z

        return ci

    _bct_modularity.ls2ci = _patched_ls2ci
    _bct_modularity._tvb_ls2ci_patched = True