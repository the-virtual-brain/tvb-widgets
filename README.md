# tvb-widgets

**TheVirtualBrain - Widgets** is a package with somehow generic GUI components, 
but developed for **EBRAINS Showcases** in particular.

The showcases developed in the last phase of the HBP are meant to illustrate 
the full potential of technical and scientific features offered by EBRAINS. 
Access by the end users to this showcased functionality should be as easy as 
possible. In order to support the usability of the showcases, as well as future 
EBRAINS workflows, we develop here a set of modular graphic solutions which 
can be easily deployed in the EBRAINS Collaboratory within the JupyterLab. 

These graphic user interface components enable:
 1. Easy setup of models and region specific or cohort simulations. This includes single simulations as well as parameter explorations.
 2. Selection of Data sources and their links to models. This will exploit the backend data access functionality to be developed new in TVB.
 3. Previews of queried data from Siibra and the KG.
 4. Deployment of jobs to HPC resources.
 5. Integration of a subset of TVB analysis and visualisation tools.
 6. The GUIs must be designed to be integrated into cells in the notebooks and Jupyter notebook extension for HPC resource usage and job tracking will be also developed as independent panels.

Installation:

    pip install tvb-widgets
