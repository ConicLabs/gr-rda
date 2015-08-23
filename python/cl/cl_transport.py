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
"""
####################################################################
 cl_transport:
 Description:
    This is a collection of recipes that handle the transfer of data
    to/from the CL server.

 Created: 7/28/15 P. Athanas

####################################################################
"""
import paramiko
import tarfile
import os
from time import sleep
from scp import SCPClient
from sh import tail
CL_SERVER_NAME = 'consolidated-logic.com'
CL_SERVER_USER = 'captive'
CL_SERVER_PW = '3015torg'


####################################################################
# createSSHClient
####################################################################
def createSSHClient(server, port, user, password):
   client = paramiko.SSHClient()
   client.load_system_host_keys()
   client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   client.connect(server, port, user, password)
   return client


####################################################################
# transport_component
####################################################################
def transport_component( tfilename, seed_name, workdir='./build' ):

   # Push package: to-be processed packages are placed in 'comp' directory.
   # Pulled package: finished work is in the 'get' directory.
   retry = 1
   ssh = createSSHClient(CL_SERVER_NAME, 22, CL_SERVER_USER, CL_SERVER_PW)
   while (retry < 10):
      try:
         scp = SCPClient(ssh.get_transport())
         scp.put(tfilename, remote_path='component')
         # If it got this far, it succeeded
         break;
      except Exception as err:
         print '=============='
         print err[0]
         print '    Retry attempt #'+str(retry)
         print '=============='
         sleep(2)
         scp.close()
   if retry > 10:
      # Should not get to this point
      print "Error: cannot transport component to server.  Network problem?"
      exit(-1)
   waittime = 0
   print '=============='
   while (waittime < 600):
      try:
         scp = SCPClient(ssh.get_transport())
         # Check the log file
         scp.get('get/'+seed_name+'_comp.log', local_path = workdir)
         line  = tail("-1", os.path.join(workdir,seed_name+'_comp.log' )).strip()
         print line
         if 'Processing Complete' in line:
            if "Failed" in line:
               print "\nAn error occurred in registering the component.  See "+\
                  os.path.join(workdir,seed_name)+'_comp.log for details.'
               return False
            break
      except Exception as err:

         print err[0]
         if 'No such file or directory' in err[0]:
            print "---- No status yet ----"
      sleep(1)
      waittime = waittime + 1
      scp.close()
   print '=============='
   # Compile complete.  Download results.
   # 
   # Server stores component, generates key
   #
   waittime = 0
   while (waittime < 6):
      try:
         scp = SCPClient(ssh.get_transport())
         scp.get('get/'+seed_name+'_key.conf', local_path = workdir)
         break
      except Exception as err:
         print '=============='
         print err[0]
         print '=============='
         waittime = waittime + 1
         sleep(1)
         scp.close()
   if waittime > 6:
      # Should not get to this point
      print "Error: cannot transport component key from server.  Network problem?"
      exit(-1)
   return True
####################################################################
# transport_assembly_run
####################################################################
def transport_assembly_run( seed_name, tfilename, workdir='./build' ):

   # Push package: to-be processed packages are placed in 'put' directory.
   # Pulled package: finished work is in the 'get' directory.
   retry = 1
   # Credentials wide out in the open:
   ssh = createSSHClient(CL_SERVER_NAME, 22, CL_SERVER_USER, CL_SERVER_PW)
   while (retry < 10):
      try:
         scp = SCPClient(ssh.get_transport())
         scp.put(tfilename, 'run')
         # If it got this far, it succeeded
         break;
      except Exception as err:
         print '=============='
         print err[0]
         print '    Retry attemp #'+retry
         print '=============='
         sleep(5)

   # 
   # Server Processing Phase
   #
   waittime = 0
   while (waittime < 600):
      try:
         scp = SCPClient(ssh.get_transport())
         # Check the log file
         scp.get('get/'+seed_name+'_run.log', local_path=workdir)
         line  = tail("-1", os.path.join(workdir,seed_name+'_run.log') ).strip()
         print line
         if 'Assembly Complete' in line:
            break
         if 'ERROR' in line:
            exit(1)
      except Exception as err:
         print '=============='
         print err[0]
         print '=============='
         if 'No such file or directory' in err[0]:
            print "---- No status yet ----"
      sleep(2)
      waittime = waittime + 1
      scp.close()
    # Compile complete.  Download results.
   try:
      scp.get('get/'+seed_name+'_assembly.dat', local_path=workdir)
      os.rename( os.path.join(workdir, seed_name+'_assembly.dat'), os.path.join(workdir,'assembly.dat'))
   except Exception as err:
      print '=============='
      print err[0]
      print '=============='
      exit(1)

   return True
