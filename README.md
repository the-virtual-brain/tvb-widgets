<p>
    <img src="dev/TVB_logo.svg" alt="TVB logo" title="TVB" align="right" height="100" />
</p>

# tvb-widgets
![Github Actions Status](https://sonarcloud.io/api/project_badges/measure?project=the-virtual-brain_tvb-widgets&metric=alert_status) 
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=the-virtual-brain_tvb-widgets&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=the-virtual-brain_tvb-widgets)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=the-virtual-brain_tvb-widgets&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=the-virtual-brain_tvb-widgets) 
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=the-virtual-brain_tvb-widgets&metric=ncloc)](https://sonarcloud.io/summary/new_code?id=the-virtual-brain_tvb-widgets)


**TheVirtualBrain - Widgets** is a package with somehow generic GUI components, 
but developed for **EBRAINS Showcases** in particular.

The showcases developed in the last phase of the HBP are meant to illustrate 
the full potential of technical and scientific features offered by EBRAINS. 
Access by the end users to this showcased functionality should be as easy as 
possible. In order to support the usability of the showcases, as well as future 
EBRAINS workflows, we develop here a set of modular graphic solutions which 
can be easily deployed in the EBRAINS Collaboratory within the JupyterLab. 

This module is also documented in EBRAINS here: https://wiki.ebrains.eu/bin/view/Collabs/tvb-widgets

These graphic user interface components enable:
 1. Easy setup of models and region specific or cohort simulations. This includes single simulations as well as parameter explorations.
 2. Selection of Data sources and their links to models. This will exploit the backend data access functionality to be developed new in TVB.
 3. Integration of a subset of TVB analysis and visualisation tools.
 4. The GUIs must be designed to be integrated into cells in the notebooks and Jupyter notebook extension for HPC resource usage and job tracking will be also developed as independent panels.

## Installation

This module is already available in EBRAINS lab,
but you can also make use of it locally, in which case, execute:

    jupyter labextension install @jupyter-widgets/jupyterlab-manager
    jupyter labextension install jupyter-matplotlib
    pip install tvb-widgets

In order to install tvb-widgets from the local repo clone, directly in a notebook, run (in the first cell): 

    %pip install --quiet --upgrade pip
    %pip install --quiet -e ..
    %pip install tvb-data

For some of our widgets, where connection to EBRAINS storage is necessary, 
you should setup as environment variable before launching the local Jupyter Lab instance:

    export CLB_AUTH = "{Your TokenString copied from EBRAINS Collab}"

To retrieve the token string, execute in https://lab.ch.ebrains.eu/:

    clb_oauth.get_token()

#  Acknowledgments
This project has received funding from the European Union’s Horizon 2020 Framework Programme for Research and Innovation under the Specific Grant Agreement No. 945539 (Human Brain Project SGA3).

This project has received funding from the European Union’s Horizon Europe Programme under the Specific Grant Agreement No. 101147319 (EBRAINS 2.0 Project).

This projects also has contribution from @peeplika as part of Google Summer of Code, through INCF organization (https://summerofcode.withgoogle.com/programs/2024/organizations/incf).

