#!/bin/bash
#echo "### Inside program ###"
STATIC_PATH=~/Projects/client_components/
STATIC_GR_RDA_PATH=~/Projects/pybombs/src/gr-rda/
#necessary wait to ensure that the usrp will properly respond
if [  $1 == "-h" ];  then
  echo "This script makes adding an RFNoC block to RDA. "
  echo " Just run as: add__module [blockname] [modulename] "
  echo " [blockname] should match the blockname tag in the UHD XML representation of the module."
  echo " [modulename] should match the top level module name used when adding the module to the HDL RDA module library. "
  exit 0;
fi
MODULE_NAME=$2
BLOCK_NAME=$1
DAT_STRING="Cell;${MODULE_NAME};{};{};Port;input;bus_clk;Port;input;bus_rst;Port;input;ce_clk;Port;input;ce_rst;Port;input;i_tlast;Port;input;i_tvalid;Port;input;o_tready;Port;output;i_tready;Port;output;o_tlast;Port;output;o_tvalid;Array;input;i_tdata;64;Array;output;o_tdata;64;Array;output;debug;64;"

sed -i "/self.cells_dict = {/a\ \ \ \ \"${BLOCK_NAME}_{}\" : \"${DAT_STRING}\"" ${STATIC_GR_ETTUS_PATH}/python/rda_dictionary.py



