#!:/bin/bash
##############
#ENV VARIABLES
##############
#these are all used during run time assembly
#This can be anywhere you have r/w/x access. Should automatically create this dir if it doesn't exist.
export CL_WORKDIR=~/Projects/build/
#point this to the client_component_template git repo directory.
export RDA_LIB_ROOT=~/Projects/client_component_template/ 
#point this to the parent folder of pybombs conic
export PYBOMBS_ROOT=~/Projects/
echo "updated GR-RDA and CL RDA ENV Variables"
