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



class rda_dictionary():
  def __init__ (self):
    self.cells_dict = {
    "FIFO" : "Cell;noc_block_axi_fifo_loopback_reg;{};{};Port;input;bus_clk;Port;input;bus_rst;Port;input;ce_clk;Port;input;ce_rst;Port;input;i_tlast;Port;input;i_tvalid;Port;input;o_tready;Port;output;i_tready;Port;output;o_tlast;Port;output;o_tvalid;Array;input;i_tdata;64;Array;output;o_tdata;64;Array;output;debug;64;"
    ,
    "FFT" : "Cell;noc_block_fft;{};{};Port;input;bus_clk;Port;input;bus_rst;Port;input;ce_clk;Port;input;ce_rst;Port;input;i_tlast;Port;input;i_tvalid;Port;input;o_tready;Port;output;i_tready;Port;output;o_tlast;Port;output;o_tvalid;Array;input;i_tdata;64;Array;output;o_tdata;64;Array;output;debug;64;"
    ,
    "FIR" : "Cell;noc_block_fir_filter;{};{};Port;input;bus_clk;Port;input;bus_rst;Port;input;ce_clk;Port;input;ce_rst;Port;input;i_tlast;Port;input;i_tvalid;Port;input;o_tready;Port;output;i_tready;Port;output;o_tlast;Port;output;o_tvalid;Array;input;i_tdata;64;Array;output;o_tdata;64;Array;output;debug;64;"
    ,
    "AddSub" : "Cell;noc_block_addsub;{};{};Port;input;bus_clk;Port;input;bus_rst;Port;input;ce_clk;Port;input;ce_rst;Port;input;i_tlast;Port;input;i_tvalid;Port;input;o_tready;Port;output;i_tready;Port;output;o_tlast;Port;output;o_tvalid;Array;input;i_tdata;64;Array;output;o_tdata;64;Array;output;debug;64;"
    ,
    "Window" : "Cell;noc_block_window;{};{};Port;input;bus_clk;Port;input;bus_rst;Port;input;ce_clk;Port;input;ce_rst;Port;input;i_tlast;Port;input;i_tvalid;Port;input;o_tready;Port;output;i_tready;Port;output;o_tlast;Port;output;o_tvalid;Array;input;i_tdata;64;Array;output;o_tdata;64;Array;output;debug;64;"
    ,
    "KeepOneInN" : "Cell;noc_block_keep_one_in_n;{};{};Port;input;bus_clk;Port;input;bus_rst;Port;input;ce_clk;Port;input;ce_rst;Port;input;i_tlast;Port;input;i_tvalid;Port;input;o_tready;Port;output;i_tready;Port;output;o_tlast;Port;output;o_tvalid;Array;input;i_tdata;64;Array;output;o_tdata;64;Array;output;debug;64;"
    ,
    "VectorIIR" : "Cell;noc_block_vector_iir;{};{};Port;input;bus_clk;Port;input;bus_rst;Port;input;ce_clk;Port;input;ce_rst;Port;input;i_tlast;Port;input;i_tvalid;Port;input;o_tready;Port;output;i_tready;Port;output;o_tlast;Port;output;o_tvalid;Array;input;i_tdata;64;Array;output;o_tdata;64;Array;output;debug;64;"
    ,
    "LogPwr" : "Cell;noc_block_logpwr;{};{};Port;input;bus_clk;Port;input;bus_rst;Port;input;ce_clk;Port;input;ce_rst;Port;input;i_tlast;Port;input;i_tvalid;Port;input;o_tready;Port;output;i_tready;Port;output;o_tlast;Port;output;o_tvalid;Array;input;i_tdata;64;Array;output;o_tdata;64;Array;output;debug;64;"
    ,
    "fosphor" : "Cell;noc_block_vector_iir;{};{};Port;input;bus_clk;Port;input;bus_rst;Port;input;ce_clk;Port;input;ce_rst;Port;input;i_tlast;Port;input;i_tvalid;Port;input;o_tready;Port;output;i_tready;Port;output;o_tlast;Port;output;o_tvalid;Array;input;i_tdata;64;Array;output;o_tdata;64;Array;output;debug;64;"

    }
  def get_cells_dict(self):
    return self.cells_dict
