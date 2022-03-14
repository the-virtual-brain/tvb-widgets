# Last tested with Python 3.10

# Anaconda needs to be installed upfront
conda update -n base -c defaults conda
conda create -y --name tvb-widgets python=3 nomkl numba scipy numpy
conda install -y --name tvb-widgets -c conda-forge jupyterlab tvb-library
conda install -y --name tvb-widgets -c conda-forge ipygany pyvista
conda install -y --name tvb-widgets ipywidgets pytest pytest-mock pytest-cov
conda install -y --name tvb-widgets -c conda-forge nbval

pip install --upgrade pip
pip install ebrains_drive
