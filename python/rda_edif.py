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
import os
import re
from collections import namedtuple
import itertools
Port_Connection = namedtuple('Port_Connection', 'io name')
Array_Connection = namedtuple('Array_Connection', 'io name length')
Net_Connection = namedtuple('Net_Connection', "module instance name index")

class rda_edif():
    """
    docstring for block test_runtime
    """
    #initialize this rda EDIF data structure
    def __init__(self, cell_dictionary):
      self.loops = []
      self.nets = {}
      #cell list used in this design
      cell_dict_temp = cell_dictionary
      #generate cell objects for each cell in the dictionary
      self.cell_dict = self.generate_cells(cell_dict_temp)
      print "blacktop..."
      #get cell info for the static design
      self.blacktop_cell = self.get_static_cell()
      #set up blacktop stuff
      #self.generate_nets_loops()

    def generate_nets_loops(self):
      #set up blacktop stuff
      bt_ce_data = ["ce{}i_tdata", "ce{}o_tdata"]
      ce_data = ["i_tdata", "o_tdata"]
      bt_ce_lvr = ["ce{}o_tlast", "ce{}i_tlast", "ce{}o_tvalid", "ce{}i_tvalid", "ce{}o_tready", "ce{}i_tready"]
      ce_lvr = ["o_tlast", "i_tlast", "o_tvalid", "i_tvalid", "o_tready", "i_tready"]
      bt_clk_rst = ["bus_clk", "bus_rst", "radio_clk", "radio_rst"]
      ce_clk_rst = ["bus_clk", "bus_rst", "ce_clk", "ce_rst"]
      #generate nets (clk, rst??)
      for j in range(4):
        self.generate_net(bt_clk_rst[j])
        bt_pc = self.blacktop_cell.get_port_connection(bt_clk_rst[j])
        self.add_net_connection(bt_pc.name, self.blacktop_cell, bt_pc)
      #generate loops and targetted nets (1-bit loops) based on cells (simple as this: for each cell connect it to the associated ports on
      # the RFNOC AXI bus. these have no
      #  specified order other than the cell dictionary itself)
      #hard coded for now. here is where it will need to change
      # connect nets
      i = 0
      for index in self.cell_dict:
        print index
        bt_ac_input = self.blacktop_cell.get_array_connection(bt_ce_data[0].format(str(i)))
        bt_ac_output = self.blacktop_cell.get_array_connection(bt_ce_data[1].format(str(i)))
        ce_ac_input = self.cell_dict[index].get_array_connection(ce_data[0])
        ce_ac_output = self.cell_dict[index].get_array_connection(ce_data[1])
        #blacktop output to ce input
        self.add_loop(self.blacktop_cell, self.cell_dict[index], bt_ac_input, ce_ac_input)
        #ce output to blacktop input
        self.add_loop(self.cell_dict[index], self.blacktop_cell, ce_ac_output, bt_ac_output)
        for j in range(6):
          bt_pc = self.blacktop_cell.get_port_connection(bt_ce_lvr[j].format(str(i)))
          ce_pc = self.cell_dict[index].get_port_connection(ce_lvr[j])
          self.generate_net(bt_pc.name)
          self.add_net_connection(bt_pc.name, self.blacktop_cell, bt_pc)
          self.add_net_connection(bt_pc.name, self.cell_dict[index], ce_pc)
        #iterate to next index and i
        for j in range(4):
          ce_pc = self.cell_dict[index].get_port_connection(ce_clk_rst[j])
          self.add_net_connection(bt_clk_rst[j%2], self.cell_dict[index], ce_pc)
        i += 1
      print "done"


    #this is stupid
    def cells_match(self, prev_cells):
      for pc in prev_cells:
        print pc
      for c in self.cell_dict:
        print c
        if not c in "##".join(prev_cells):
          print "not found, need to generate bitstream and program FPGA."
          return 0
        else:
          print "found"
      print "all cells found"
      return 1

    def write_cell_dict_file(self, cell_dict, filename):
      file_writer = open(filename, "w")
      for d in cell_dict:
        file_writer.write(d+"\n")
        file_writer.write(cell_dict[d].get_rda_cell()+"\n")

    #fetches the cell string of
    def get_static_cell(self):
      #Ugly but suffices for now.
      static_cell_str = "Cell;blacktop;blacktop;0;Port;input;ce0i_tvalid;Port;input;ce0i_tlast;Port;input;ce1i_tvalid;Port;input;ce1i_tlast;Port;input;ce2i_tvalid;Port;input;ce2i_tlast;Port;input;ce0o_tready;Port;input;ce1o_tready;Port;input;ce2o_tready;Port;input;radio_clk;Port;input;bus_clk;Port;input;radio_rst;Port;input;bus_rst;Port;output;ce0i_tready;Port;output;ce1i_tready;Port;output;ce2i_tready;Port;output;ce0o_tvalid;Port;output;ce0o_tlast;Port;output;ce1o_tvalid;Port;output;ce1o_tlast;Port;output;ce2o_tvalid;Port;output;ce2o_tlast;Array;input;ce0i_tdata;64;Array;input;ce1i_tdata;64;Array;input;ce2i_tdata;64;Array;output;ce0o_tdata;64;Array;output;ce1o_tdata;64;Array;output;ce2o_tdata;64;"
      return rda_cell(static_cell_str)

    def generate_cells(self, cells):
      cell_dict = {}
      for name in cells:
        #print name
        #print cells[name]
        cell_dict[name] = rda_cell(cells[name])
      return cell_dict

    def add_loop(self, start_cell, end_cell, ac1, ac2):
      self.loops.append(rda_loop(start_cell.get_name(), end_cell.get_name(), start_cell.get_instance()+start_cell.get_id(), end_cell.get_instance()+end_cell.get_id(), ac1, ac2))

    def generate_net(self, name):
      self.nets[name] = rda_net(name)

    def add_net_connection(self, name, cell, pc):
      self.nets[name].add_net_connection(cell.get_name(), cell.get_instance()+cell.get_id(), pc.name, "-1")

    def generate_dat(self, filename):
      edif_dat = open(filename, "w")
      for cell in self.cell_dict:
        edif_dat.write(self.cell_dict[cell].get_rda_cell()+"\n")
        print cell
        print self.cell_dict[cell].get_rda_cell()
      edif_dat.write(self.blacktop_cell.get_rda_cell()+"\n")
      print self.blacktop_cell.get_rda_cell()
      for net in self.nets:
        print net
        edif_dat.write(self.nets[net].get_rda_net()+"\n")
        print self.nets[net].get_rda_net()
      for loop in self.loops:
        print loop
        edif_dat.write(loop.get_rda_loop()+"\n")
        print loop.get_rda_loop()

class rda_cell():
    """
    docstring for block test_runtime
    """
    #initialize this rda EDIF data structure
    def __init__(self, cell_string):
      cell_string_array = cell_string.split(";")
      self.name = cell_string_array[1]
      self.instance = cell_string_array[2]
      self.id_string = cell_string_array[3]
      cell_string_array.pop(len(cell_string_array)-1)
      self.array_in = {}
      self.array_out = {}
      self.ports = {}
      index = 4
      while index < len(cell_string_array):
        if cell_string_array[index] == "Array":
          index += 1
          io = cell_string_array[index]
          index += 1
          name = cell_string_array[index]
          index += 1
          length = re.sub('[^0-9]','', cell_string_array[index]) #strips all non numeric characters, sanity check
          self.create_array_connection(io, name, length)
        elif cell_string_array[index] == "Port":
          index += 1
          io = cell_string_array[index]
          index += 1
          name = cell_string_array[index]
          self.create_port_connection(io, name)
        else:
          raise NameError('Invalid port or array format in rda_cell.')
        index += 1

    def create_array_connection(self, io, name, length):
      ac = Array_Connection(io, name, length)
      print ac
      if(ac.io == "input"):
        self.array_in[name] = ac
      elif(ac.io == "output"):
        self.array_out[name] = ac
      else:
        raise NameError('Invalid io type for rda_cell port/array.')

    def create_port_connection(self, io, name):
      pc = Port_Connection(io, name)
      #print pc
      self.ports[name] = pc

    def get_name(self):
      return self.name
    def get_instance(self):
      return self.instance
    def get_id(self):
      return self.id_string
    def get_array_connection(self, name):
      if name in self.array_in:
        return self.array_in[name]
      elif name in self.array_out:
        return self.array_out[name]
      else:
        print name
        raise NameError('Array Connection not found with name.')
    def get_port_connection(self, name):
      if name in self.ports:
        return self.ports[name]
      else:
        print name
        raise NameError('Port Connection not found with name.')


    def get_rda_cell(self):
      rda_cell_string = "Cell;"+self.name+";"+self.instance+self.id_string+";"
      for ar in self.array_in:
        a = self.array_in[ar]
        rda_cell_string = rda_cell_string + "Array;"+a.io+";"+a.name+";"+a.length+";"
      for ar in self.array_out:
        a = self.array_out[ar]
        rda_cell_string = rda_cell_string + "Array;"+a.io+";"+a.name+";"+a.length+";"
      for po in self.ports:
        p = self.ports[po]
        rda_cell_string = rda_cell_string + "Port;"+p.io+";"+p.name+";"
      return rda_cell_string


# format is like this 
#Loop;afpga_passthrough_PASS3_wire_0;33;passthrough;PASS3;out;passthrough;PASS2;in;
#Loop;BT_in_01;33;blacktop;BT0;in1;passthrough;PASS3;in;
class rda_loop():
    """
    docstring for block test_runtime
    """
    #initialize this rda EDIF data structure
    #start and end should be instances
    def __init__(self, start_module, end_module, start_instance_id, end_instance_id, ac1, ac2):
      print ac1
      print ac2
      print "poop"
      if ac1.length != ac2.length:
        raise ValueError('Input and output connections must be the same length when initializing a rda_loop')
      self.name = start_module+"_"+ac1.name+"_"+end_module+"_"+ac2.name+"_wire_0"
      self.length = ac1.length
      self.start_module = start_module
      self.end_module = end_module
      self.start_instance_id = start_instance_id
      self.end_instance_id = end_instance_id
      self.start_port_name = ac1.name
      self.end_port_name = ac2.name
      #print self.get_rda_loop()

    def get_rda_loop(self):
      rda_loop_string = "Loop;"+self.name+";"+self.length+";"+self.start_module+";"+self.start_instance_id+";"+self.start_port_name+";"+self.end_module+";"+self.end_instance_id+";"+self.end_port_name+";"
      return rda_loop_string

#Net;null_valid;blacktop;BT0;null_valid;-1;blacktop;BT0;out1;32;blacktop;BT0;out2;32;blacktop;BT0;out3;32;blacktop;BT0;out4;32;blacktop;BT0;out5;32;
#Net;clk;passthrough;PASS3;clk;-1;passthrough;PASS2;clk;-1;blacktop;BT0;clk;-1;
class rda_net():
    """
    docstring for block test_runtime
    """
    #initialize this rda EDIF data structure
    def __init__(self, name):
      #array of net_connections
      self.net_array = []
      self.name = name

    def add_net_connection(self, module, instance, port_name, index):
      nc = Net_Connection(module, instance, port_name, index)
      self.net_array.append(nc)

    def get_rda_net(self):
      rda_net_string = "Net;"+self.name+";"
      for net in self.net_array:
        rda_net_string = rda_net_string+net.module+";"+net.instance+";"+net.name+";"+net.index+";"
      return rda_net_string


if __name__ == "__main__":
    dictionary = {}
    rda_edif(dictionary)
