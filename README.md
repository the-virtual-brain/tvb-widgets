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

These graphic user interface components enable:
 1. Easy setup of models and region specific or cohort simulations. This includes single simulations as well as parameter explorations.
 2. Selection of Data sources and their links to models. This will exploit the backend data access functionality to be developed new in TVB.
 3. Previews of queried data from Siibra and the KG.
 4. Deployment of jobs to HPC resources.
 5. Integration of a subset of TVB analysis and visualisation tools.
 6. The GUIs must be designed to be integrated into cells in the notebooks and Jupyter notebook extension for HPC resource usage and job tracking will be also developed as independent panels.

## Installation

    pip install tvb-widgets

### Development Installation

Create a dev environment with conda from *dev/prepare_env.sh* or mimic the command from *dev/Dockerfile*
```
Install the python. This will also build the TS package.
```bash
pip install -e ".[test, notebooks]"
```

When developing your extensions, you need to manually enable your extensions with the
notebook / lab frontend. For lab, this is done by the command:

```
jupyter labextension develop --overwrite .
yarn run build
```

### How to see your changes
#### Typescript:
If you use JupyterLab to develop then you can watch the source directory and run JupyterLab at the same time in different
terminals to watch for changes in the extension's source and automatically rebuild the widget.

```bash
# Watch the source directory in one terminal, automatically rebuilding when needed
yarn run watch
# Run JupyterLab in another terminal
jupyter lab
```

After a change wait for the build to finish and then refresh your browser and the changes should take effect.

#### Python:
If you make a change to the python code then you will need to restart the notebook kernel to have it take effect.


#  Acknowledgments
This project has received funding from the European Union’s Horizon 2020 Framework Programme for Research and Innovation under the Specific Grant Agreement No. 945539 (Human Brain Project SGA3).
