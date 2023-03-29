rem Last tested with Python 3.8

rem Anaconda needs to be installed upfront
conda update -n base -c defaults conda
conda create -y --name tvb-widgets python=3.8 nomkl numba scipy numpy jupyterlab
conda install -y --name tvb-widgets -c conda-forge pyvista

pip install --upgrade pip
pip install -r ../requirements.txt

rem Optionally install tvb-data from ZENODO to use demo data within it
