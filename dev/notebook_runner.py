# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import os
import sys
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


def execute_notebook(in_path, notebook):
    with open(os.path.join(in_path, notebook), encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=None)

    ep.preprocess(nb)

    # with open(os.path.join(out_path, notebook), 'w+', encoding='utf-8') as f: # for debug only
    #     nbformat.write(nb, f)
    print(notebook + " - successful execution")


if __name__ == '__main__':

    if len(sys.argv) == 2:
        in_path = sys.argv[1]
    else:
        print("please insert the input path")
        exit(-1)

    if not os.getenv('CLB_AUTH'):
        os.environ['CLB_AUTH'] = 'abc'

    notebooks = [file for file in os.listdir(in_path) if file[-6:] == ".ipynb"]

    # start as many threads as logical cpus
    with ThreadPool(cpu_count()) as pool:
        pool.map(lambda notebook: execute_notebook(in_path, notebook), notebooks)
