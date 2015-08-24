gr-rda GNU Radio Out-of-Tree Module. This module interfaces with the RDA cloud app for FPGA rapid assembly. Current Target: Kintex-7 on the USRP X310, using the RFNoC block library for modular assembly.

gr-rda.lwr is the pybombs recipe. Add it to pybombs/recipes and run ./pybombs install gr-rda

What's in this OOT module?
/apps/ - support scripts for runtime
/examples/ - example grc designs
/examples/rfnoc - example rfnoc grc designs
/grc/ - grc block specification for device3 block
/python/ - all python code
/python/rda/ - python code that interacts with the rda server and local cache databses



