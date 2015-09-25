#!/bin/bash
# Expects bash 4.0 for log redirection to work
# Copyright Consolidated Logic 2015 All Rights Reserved 
# Author: Ali Sohanghpurwala (asohangh@conic-labs.com)
# This script automatically installs gnuradio, uhd, and Consolidated Logic RDA and Component Creation

# Edit the following parameters if you want to change build/install parameters
USER=`whoami`
PYBOMBS_TARGET=/home/$USER/target
PYBOMBS_SRC=/home/$USER/pybombs_conic
LOG_LOCATION=/tmp/cl_install.log
MAKEWIDTH=`nproc`

echo "Starting RDA Installation process, this will prompt you for administrator credentials (perhaps multiple times) and take some time to build"
echo
echo "I am building pybombs in $PYBOMBS_SRC and installing to $PYBOMBS_TARGET.  Progress information is logged to $LOG_LOCATION"
echo "If you want to change any of these parameters, hit Ctrl+C before entering you admin password, edit and re-run install_conic.sh"
echo
echo "Installing base-dependencies from apt-get, this may take some time"
yes | sudo apt-get install build-essential git vim python-dev python-pip libusb-dev libftdi-dev &>> $LOG_LOCATION
if [ $? -ne 0 ]; then
  echo "Failed to install dependencies via apt-get, check network connectivity and try again"
  exit
fi
sudo pip install paramiko scp sh &>> $LOG_LOCATION

echo "Cloning and building gnuradio with Consolidated Logic custom recipes"
git clone --recursive https://github.com/pybombs/pybombs.git $PYBOMBS_SRC &>> $LOG_LOCATION
cd $PYBOMBS_SRC/recipes 
rm uhd.lwr gr-ettus.lwr gr-rda.lwr xc3sprog.lwr rda-cc-apps.lwr 2> /dev/null
wget https://github.com/ConicLabs/gr-rda/raw/master/uhd.lwr https://github.com/ConicLabs/gr-rda/raw/master/gr-ettus.lwr https://github.com/ConicLabs/gr-rda/raw/master/gr-rda.lwr https://github.com/ConicLabs/cl-xc3sprog/raw/master/packages/xc3sprog.lwr https://raw.githubusercontent.com/ConicLabs/rda-cc-apps/master/rda-cc-apps.lwr &>> $LOG_LOCATION

# Creating config.dat with default values
cd $PYBOMBS_SRC
echo "[config]" >> config.dat
echo "gituser = $USER" >> config.dat
echo "gitcache = " >> config.dat
echo "gitoptions = " >> config.dat
echo "prefix = $PYBOMBS_TARGET" >> config.dat
echo "satisfy_order = deb,src" >> config.dat
echo "forcepkgs = " >> config.dat
echo "forcebuild = gnuradio,uhd,gr-air-modes,gr-osmosdr,gr-iqbal,gr-fcdproplus,uhd,rtl-sdr,osmo-sdr,hackrf,gqrx,bladeRF,airspy" >> config.dat
echo "timeout = 30" >> config.dat
echo "cmakebuildtype = RelWithDebInfo" >> config.dat
echo "builddocs = OFF" >> config.dat
echo "cc = gcc" >> config.dat
echo "cxx = g++" >> config.dat
echo "makewidth = $MAKEWIDTH" >> config.dat

# Install GNURadio and RDA applications
echo "Installing GNURadio and UHD, this may take anywhere from 20 minutes to several hours."
cd $PYBOMBS_SRC
./pybombs install gnuradio &>> $LOG_LOCATION
# Remove and re-install uhd if gnuradio build failed
# This is a workaround for issues found building this version of UHD
if [ $? -ne 0 ]; then
  yes | ./pybombs remove uhd &>> $LOG_LOCATION
  ./pybombs install uhd &>> $LOG_LOCATION
  ./pybombs install gnuradio &>> $LOG_LOCATION
fi
echo "Installing RDA Tools"
./pybombs install rda-cc-apps &>> $LOG_LOCATION

if [ ! -f /etc/udev/rules.d/52-digilent-usb.rules ]; then
  echo "Install Digilent udev rules"
  sudo cp $PYBOMBS_SRC/src/xc3sprog/cables/52-digilent-usb.rules /etc/udev/rules.d
fi
