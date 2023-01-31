# Last tested with Python 3.8

# Anaconda needs to be installed upfront
conda update -n base -c defaults conda
conda create -y --name tvb-widgets python=3.8 nomkl numba scipy numpy
conda install -y --name tvb-widgets -c conda-forge jupyterlab tvb-library tvb-data ipywidgets==7.7.1
conda install -y --name tvb-widgets -c conda-forge pythreejs pyvista colorcet
conda install -y --name tvb-widgets ipywidgets

pip install --upgrade pip
pip install ebrains_drive mne

# Optionally install tvb-data from ZENODO to use demo data within it
