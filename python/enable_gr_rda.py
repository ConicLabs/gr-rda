#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2015 Consolidated Logic 
# 
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
# 

import numpy
from gnuradio import gr
import sys, subprocess
import os
import time
import re
import shutil
import logging
from rda import rda_dictionary 
from rda import rda_edif
from rda import cl 


WORKDIR = ""
RDA_LIB_ROOT = ""

def build_environment():
   """ build_environment()
       Allow the ability to override internal environment with shell environment variables.
   """
   # CL_WORKDIR
   global WORKDIR
   global RDA_LIB_ROOT
   if os.environ.has_key('CL_WORKDIR'):
     WORKDIR = os.environ['CL_WORKDIR']
     print WORKDIR
   else:
     raise NameError("No environment variable CL_WORKDIR.") 
   if os.environ.has_key('RDA_LIB_ROOT'):
     RDA_LIB_ROOT = os.environ['RDA_LIB_ROOT']
     print RDA_LIB_ROOT
   else:
     raise NameError("No environment variable RDA_LIB_ROOT.") 



class enable_gr_rda(gr.interp_block):
    """
    docstring for block test_runtime
    """
    def __init__(self, location="", top_block="top_block.py", enable_run_rda=1, keyfile="", enable_debug=0):
      if enable_run_rda == 1:
        print "Name of top python script being searched for GR-RDA RFNoC blocks:"
        print top_block
        print "Location..."
        print location
        print "using keyfile ", keyfile
        rda_dict = rda_dictionary.rda_dictionary()
        #generate/import .dat definitions of rfnoc blocks (maybe stored in a dictionary)
        _rfnoc_cells = rda_dict.get_cells_dict()
        #open top_block and find all rfnoc_blocks defined in top_block
        _top_filename = location+"/"+top_block
        print top_block[:-3]
        #if we ever enable multiple USRPs, then this is where the code would probably need to change, in addition to a for loop down below as well
        _rfnoc_blocks, _block_selects, _block_revisions = self.find_rfnoc_blocks(_top_filename)
        print _block_revisions
        #cell matching rfnoc modules
        _old_rfblocks = self.check_old_blocks()
        #need to generate loops and .dat data structure
        rda_edif_dat = rda_edif.rda_edif(self.match_blocks(_rfnoc_blocks, _block_selects, _rfnoc_cells))
        #generate nets and loops if the cells have changed from previous
        if(not rda_edif_dat.cells_match(_old_rfblocks)):
          rda_edif_dat.generate_nets_loops()
          #generate .dat/edif of sandbox wrapper + sandbox blocks (rfnoc blocks)
          print "generate DAT"
          #TODO file name static for now
          dat_file = "/tmp/edif1.dat"
          rda_edif_dat.generate_dat(dat_file) 
          #verifies keyfile, checks component cache, and design cache. returns key and design cache hash
          #TODO do all these things correctly
          build_environment()
          if os.path.isdir(WORKDIR):
            shutil.rmtree(WORKDIR)
            os.mkdir(WORKDIR)
            if not os.path.isfile( keyfile ):
              print "Cannot find keyfile: " + keyfile
              exit(-1)
            if not os.path.isfile( dat_file ):
              print "Cannot find edif DAT file: " + dat_file
              exit(-1)
            shutil.copy(dat_file, WORKDIR)
            shutil.copy(keyfile, WORKDIR)
            try:
              cl.cl_database.build_environment()
              cl.cl_database.enable_logging('cl_compile', workdir=WORKDIR)
              logger = logging.getLogger( 'cl_compile')
              logger.info("Assembling design in "+os.path.basename(dat_file))
              cl.cl_database.assemble_design( WORKDIR, datfile=dat_file, keyfile=keyfile )
            except Exception as err:
              print "Failure: "+str(err.args)
              exit(-1)
          else:
            print WORKDIR, " WORKDIR is not a valid path."
            exit(-1)
          #TODO file names are static for now.
          print "Running rda_loader and programming the device"
          self.program()
        else:
          print """FPGA is already programmed with the desired RFNOC blocks"""
        #DONE
      else:
          print """Set "Use RDA? = No" in Device3 Using RDA block."""
          print """RDA will not be called."""
      print """Proceeding with UHD."""

    def print_dict(self, dictionary):
      for item in dictionary:
        print item
        print dictionary(item)

    def program(self):
      print sys.path[0]
      #print RDA_LIB_ROOT
      os.chdir(WORKDIR)
      print os.getcwd()
      #print os.path.join(RDA_LIB_ROOT+"static/lib/top.bit")
      #print os.path.join(WORKDIR,".")
      shutil.copy(os.path.join(RDA_LIB_ROOT+"static/lib/top.bit"), os.path.join(WORKDIR,".")) 
      pro = subprocess.call(['rda_loader', 'top.bit', 'assembly.dat', RDA_LIB_ROOT+'/modules/lib'])
      assert pro == 0,  "Programming or Assembly Failed."
      print "Waiting a bit to let the FPGA boot up."
      time.sleep(5) 

    def check_old_blocks(self, log="/tmp/uhd_log"):
      log_file = open(log, "w")
      print "Checking USRP for blocks with uhd_usrp_probe... This may take a couple seconds."
      p1 = subprocess.Popen("uhd_usrp_probe", shell=True, universal_newlines=True, stdout=log_file)
      p1.wait() 
      log_file.close()
      print "Done"
      log_file = open(log, "r")
      log_lines = log_file.readlines()
      starts_with = "-- *"
      old_blocks = []
      print "-- RFNoC Blocks:"
      for lin in log_lines:
        if starts_with in lin:
          print lin
          old_blocks.append(lin)
      return old_blocks

    #returns an array of rf_noc_blocks
    def find_rfnoc_blocks(self, filename="", search_string="_rfnoc_.*=.*ettus"):
      if(os.path.isfile(filename)):
         _top_file = open(filename, "r")
      else:
        raise IOError('File does not exist')
      #debug
      print _top_file
      print "Search String used to find RFNoC Blocks:"
      print search_string
      _rfnoc_blocks = []
      _block_selects = []
      _block_revisions = []
      _top_lines = _top_file.readlines()
      line_index = 0
      while line_index <  len(_top_lines):
        line = _top_lines[line_index]
        #debug
        #print line
        matched = re.search( search_string, line)
        #we don't need to program any "Radio" blocks so don't use those
        #TODO matched_revision needs to be specified for various situations
        if( matched and not "radio" in matched.group() and not "fosphor_display" in matched.group()):
          #hard coding each non-generic type block ...for now
          #matched2_fixed, matched_number_fixed, matched_revision = find_rfnoc_info()
          print line
          if "fir" in matched.group():
            matched2_fixed = "FIR"
            line_index+=3
            line = _top_lines[line_index]
            if "-" in line:
              matched_number_fixed = "0"
            else:
              matched_number_fixed = re.search("\s\d",line).group().replace(" ","")
            matched_revision = ""
          elif "window" in matched.group():
            matched2_fixed = "Window"
            line_index+=3
            line = _top_lines[line_index]
            if "-" in line:
              matched_number_fixed = "0"
            else:
              matched_number_fixed = re.search("\s\d",line).group().replace(" ","")
            matched_revision = ""
          #have to also find generic type block
          else:
            #print "found a 1st match"
            #debug
            matched2 = re.search("\A\s*\"\w*\"", line)
            matched_number =  re.search(",\s\d*", line)
            while (not matched2):
              #debug
              #print line
              matched2 = re.search("\A\s*\"\w*\"", line)
              matched_number = re.search(",\s\d*", line)
              line_index+=1
              line = _top_lines[line_index]
            #print "found 2nd match"
            matched2_fixed = matched2.group().replace("\"","").replace(" ","")
            matched_number_fixed = matched_number.group()[2:]
            #getting revision number last (if it exists)
            line_index+=1 
            line = _top_lines[line_index]
            print line
            matched3 = re.search("set_block_alias(.*)", line)
            if(matched3):
              print matched3.group() 
              matched_revision = matched3.group().replace("set_block_alias(\"","").replace("\")","")
            else:
              line_index-=1
              matched_revision = ""
              print "bad"
          #debug
          print matched2_fixed
          print matched_number_fixed
          print matched_revision
          _rfnoc_blocks.append(matched2_fixed)
          _block_selects.append(matched_number_fixed) 
          _block_revisions.append(matched_revision) 
        line_index+=1
      assert len(_rfnoc_blocks) > 0, 'No RFNoC Blocks found. This may be an error in the search parameter or an error in the flowgraph.'
      return _rfnoc_blocks, _block_selects, _block_revisions

    #def find_rfnoc_info(self, 



    #matches the blocks found in the flowgraph with the blocks in the dictionary
    def match_blocks( self, flowgraph_blocks, block_ids, block_dictionary):
      form_flow_blocks = {}
      block_index = 0
      fifo_blocks = 0
      found_first_fifo = 0
      for block in flowgraph_blocks:
        print block + " found?"
        if block in block_dictionary:
          print block + " found"
          if block == "FIFO":
            fifo_blocks += 1
          print "block info..."
          block_id = block_ids[block_index]
          block_instance = block+"_"+block_id
          block_cell = block_dictionary[block].format(block,block_id)
          form_flow_blocks[block_instance] = block_cell
        else:
          raise NameError('Block not found. Make sure the blocks have been properly registered in GNU Radio.')
        block_index += 1
      if fifo_blocks > 0:
        print form_flow_blocks
        fifo_blocks -= 1
        block_id = str(fifo_blocks)
        del form_flow_blocks["FIFO_"+block_id]
      while len(form_flow_blocks) < 3: #num of CE slots. hardcoded for now...
        block_id = str(fifo_blocks)
        fifo_blocks += 1
        block = "FIFO"
        print block + " created"
        block_instance = block+"_"+block_id
        block_cell = block_dictionary[block]
        block_cell = block_cell.format(block,block_id)
        form_flow_blocks[block_instance] = block_cell
      if len(form_flow_blocks) > 3:
        raise NameError('Too Many CE blocks instantiated in this design. There are currently 3 CE ports in RDA enabled RFNoC with 1 Static RFNoC FIFO block. ')
      return form_flow_blocks

if __name__ == "__main__":
    enable_rda("/local/rda/gr-rda/examples/rfnoc", "rfnoc_fft.py", 1,
        "~/keyfile.conf")
 
