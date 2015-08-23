# Copyright 2012 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.

install(
  FILES
  rfnoc_fft.grc
  rfnoc_fir_tx.grc   
  rfnoc_keep.grc    
  rfnoc_radio_host.grc  
  rfnoc_vector_iir.grc  
  rfnoc_window.grc
  rfnoc_addsub.grc  
  rfnoc_fifo_test.grc  
  rfnoc_fir.grc      
  rfnoc_logpwr.grc  
  rfnoc_tx.grc
  DESTINATION ${GR_PKG_DATA_DIR}/examples/rfnoc/
)

