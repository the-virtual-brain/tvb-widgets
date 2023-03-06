import os
import sys

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor


def execute_notebook(in_path, out_path, notebook):
    with open(os.path.join(in_path, notebook)) as f:
        nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=1000)

    ep.preprocess(nb)

    with open(os.path.join(out_path, notebook), 'w+', encoding='utf-8') as f:
        nbformat.write(nb, f)
    print(notebook + " - successful execution")


if __name__ == '__main__':

    if len(sys.argv) == 3:
        in_path = sys.argv[1]
        out_path = sys.argv[2]
    else:
        print("please insert the input and output paths")
        exit(-1)

    if not os.getenv('CLB_AUTH'):
        os.environ['CLB_AUTH'] = 'abc'

    if not os.path.exists(out_path):
        os.mkdir(out_path)

    notebooks = [file for file in os.listdir(in_path) if file[-6:] == ".ipynb"]

    for notebook in notebooks:
        execute_notebook(in_path, out_path, notebook)

