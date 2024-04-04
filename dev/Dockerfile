FROM continuumio/miniconda3

ARG TVB_USER=tvb_user
ARG USER_HOME=/home/$TVB_USER
ARG JUPYTER_CONFIG=$USER_HOME/.jupyter

RUN useradd -ms /bin/bash "$TVB_USER"
WORKDIR $USER_HOME

USER root
RUN conda update -n base -c defaults conda
COPY dev/prepare_env.sh .
COPY requirements.txt ..
RUN bash ./prepare_env.sh

USER $TVB_USER

CMD ["bash","-c","source activate tvb-widgets && python"]
