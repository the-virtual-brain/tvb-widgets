FROM continuumio/miniconda3

ARG TVB_USER=tvb_user
ARG USER_HOME=/home/$TVB_USER
ARG JUPYTER_CONFIG=$USER_HOME/.jupyter

RUN useradd -ms /bin/bash $TVB_USER
WORKDIR $USER_HOME

USER root
RUN conda update -n base -c defaults conda
RUN conda create -y --name tvb-widgets python=3 nomkl numba scipy numpy
RUN conda install -y --name tvb-widgets -c conda-forge jupyterlab tvb-library
RUN conda install -y --name tvb-widgets -c conda-forge ipygany pyvista
RUN conda install -y --name tvb-widgets ipywidgets
RUN /opt/conda/envs/tvb-widgets/bin/pip install --upgrade pip
RUN /opt/conda/envs/tvb-widgets/bin/pip install ebrains_drive

USER $TVB_USER

CMD ["bash","-c","source activate tvb-widgets && python"]
