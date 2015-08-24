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
 cl_database:
 Description:
    This is a collection of recipes launched after a GR run.  It checks 
    to see if everything is present and valid. If this has been run before, 
    it is possible that the results can be found in the design cache.  If 
    not, launch a job with the server.

 Created: 7/4/15 P. Athanas
  Edits by: 7/24/2015 R. Marlow
####################################################################
"""
import os.path
import sys
import hashlib
import sqlite3
import glob
import tarfile
import logging
import random
import zipfile
from cl_transport import transport_assembly_run, transport_component

# Handle to design/component DB
cldb = None
logger = None

#
# Environment  #####################################################
CL_DATABASE = os.environ['HOME']+'/.cl_design_component.cache'
CL_COMPILE_FILE = 'compile_run.conf'
CL_WORKDIR = './build'
CL_ASSEMBLY_FILE = 'assembly.dat'
CL_COMPONENT_CONF = 'component.conf'
CL_DISTRIB_DB = os.environ['PYBOMBS_ROOT']+'/target/share/gr-rda/examples/cl_client_cache_public.zip'
#GLOBAL KEY_DICT
PRJ_KEY_INFO = {
    "family" : "Xilinx_7Series",
    "platform" : "",
    "part" : "XC7K410T",
    "type" : "",
    "name" : "",
    "key" : "",
    "group" : ""
}
COMP_KEY_INFO = {
    "key" : "",
}

####################################################################
# build_environment
####################################################################
def build_environment():
   """ build_environment()
       Allow the ability to override internal environment with shell environment variables.
   """
   # CL_WORKDIR
   global CL_WORKDIR
   if os.environ.has_key('CL_WORKDIR'):
      CL_WORKDIR = os.environ['CL_WORKDIR']
      print CL_WORKDIR

####################################################################
# enable_logging
####################################################################
def enable_logging( name='mylogger', workdir=CL_WORKDIR ):
    """ enable_logging()
    Create a log file of relevant events.  Also echo logging information to the console.
    """
    global logger
    logger = logging.getLogger( name )
    hdlr = logging.FileHandler( os.path.join( workdir,'status.log'))
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(hdlr)
    
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    logger.addHandler(console_handler)


####################################################################
# Graceful_Exit
####################################################################
def graceful_exit( ):
    """graceful_exit()
    Called when a failure has occurred, and no recovery possible.
    """
    logger.critical('Processing Failed.')
    print "Boo hoo hoo!"
    exit(-1)
    
    
####################################################################
# get_info_from_keyfile
####################################################################
def get_info_from_keyfile(keytype, keyfilename = "", fieldname='key' ):
    """get_info_from_keyfile(keytype, path_fname)
    Looks for the key file, 'keyfile.conf', in the CL cache structure
    based at 'path_fname' in the directory hierarchy.
    Args:
       keytype   The type of key being saught.  Used to identify section 
                 in CONF file. (string)
       keyfilename      Location of the keyfile (string)
    Returns:
       doesn't return anything anymore, sets appropriate KEY_INFO, if found.
       None, if not found
    """
    global logger
    global PRJ_KEY_INFO
    global COMP_KEY_INFO
    if(keytype == "project"):
        KEY_INFO = PRJ_KEY_INFO
    elif(keytype == "component"):
        KEY_INFO = COMP_KEY_INFO
    else:
        logger.error('Invalid keytype '+ keytype)
    try:
        if(keytype == "project" and KEY_INFO[fieldname]):
            logger.info('Info '+ fieldname +' already acquired.')
        else:
            keyfile = os.path.join( keyfilename)
            if not os.path.isfile( keyfile ):
                logger.error( 'Cannot find ' + keytype + ' keyfile: '+ keyfile)
                exit(-1)
            # Read keyfile, look for [keytype] section
            with open( keyfile ) as f:
                kfn = f.readlines()
            start = 0
            for a in kfn:
                # Parse down until keytype field
                if start==0:
                    if '['+keytype+']' in a:
                        start = 1
                        continue
                elif start == 1:
                    if a[:1] == '[':
                        start = 2 
                        continue
                    else :
                        if fieldname in a:
                            key = a.split('=')[1].strip()[1:-1]
                            if len(key) < 1:
                                start = 3
                            else:
                                start = 99
                            break
                else :
                    logger.error('Damaged '+keytype+' keyfile.  Redownload keyfile.conf from Project Dashboard online' )
            if start != 99:
                logger.error( 'Damaged '+keytype+' keyfile.  Redownload keyfile.conf from Project Dashboard online' )
            #probably shouldn't log this if we want it to be protected
            #logger.info(key) 
            KEY_INFO[fieldname] = key
            if(keytype == "project"):
                PRJ_KEY_INFO = KEY_INFO
            elif(keytype == "component"):
                COMP_KEY_INFO = KEY_INFO
            else:
                logger.error('Invalid keytype '+ keytype)
            logger.info('Info '+fieldname+' acquired from '+keytype+ ' keyfile.')
    except Exception as err:
        print err[0]
        logger.error( 'Invalid keyfile fieldname ' + fieldname + '. ' + err[0] + '. Use a valid fieldname instead. ')


####################################################################
# open_cl_database
####################################################################
def open_cl_database():
    """ open_cl_database()
        Create a handle to the cl design/component database

        Returns true if succeeded.
    """
    global cldb
    if cldb != None:
        return True
    # Check for the existance of the DB
    while not os.path.isfile( CL_DATABASE ):
        logger.warning('Cannot open local design/component cache.  Creating.')
        really_initialize_db(True)
    cldb = sqlite3.connect( CL_DATABASE )
    # Check if tables are present
    rc = cldb.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    if len(rc) != 3:
        logger.error('Local design/component cache corrupted.  Please regenerate.')
        return False
    tables = rc[0][0]+rc[1][0]
    return ('design_cache' in tables) and ('component_cache' in tables)


####################################################################
# close_cl_database
####################################################################
def close_cl_database():
   """ close_cl_database()
       Undo what open_cl_database() does
   """
   global cldb
   cldb.close()
   cldb = None

####################################################################
# is_in_design_cache
####################################################################
def is_in_design_cache( key ):
   """ is_in_design_cache( design_cache_path, key)
   Boolean function to check if 'key' is an entry in the design cache.
   Args:
      design_cache_path: the root of the cache

      key: the key that is to be tested
   Return:
      True if the key is present
   """
   record = cldb.execute('select * from design_cache where design_key=\"'+key+'";').fetchall()
   return len(record) > 0


####################################################################
# remove_from_design_cache
####################################################################
def remove_from_design_cache( key ):
   """ remove_from_design_cache( key )
   function to remove a design from the design cache, based on the design key.
   Args:
      design_cache_path: the root of the cache

      key: the key that is to be tested
   Return:
     no return at this time.
   """
   sqlcmd = 'delete from design_cache where design_key=\"'+key+'";'
   print sqlcmd
   cldb.execute(sqlcmd)
   cldb.commit()

####################################################################
# remove_from_design_cache
####################################################################
def clear_design_cache():
   """ clear_design_cache( key )
   function to remove all designs from the design cache, based on the design key.
   Args:
   Return:
     no return at this time.
   """
   sqlcmd = 'delete from design_cache;'
   print sqlcmd
   cldb.execute(sqlcmd)
   cldb.commit()


####################################################################
# calculate_design_key
####################################################################
def calculate_design_key(builddir=CL_WORKDIR, datfile='edif.dat', keyfile='keyfile.conf'):
    """calculate_design_key(cache_path )
    Computes the key that is to be used as an index into the design cache.
    Args:
       cache_path
    Return:
       The project key, if it exists, and the component keys
    """
    global PRJ_KEY_INFO
    # Create a dictionary of components used in the design
    ckey = {}
    # Initialize hash value for DAT file
    dathash = ''
    open_cl_database()
    if not os.path.isfile( datfile ):
        logger.error( 'Cannot find ' + datfile + ' netlist file. ')
        exit(-1)
    # Start processing DAT file
   # TODO we shouldn't really have to open the dat file, instead a dictionary of the 'cell's used should be passed into this function
    with open( datfile ) as f:
        for datline in f:
            # Extract the cell instances
            if datline[:4] == 'Cell':
                cellname = datline.split(';')[1]
                # Cell has to be unique and not 'blacktop'
                if not ckey.has_key(cellname) and cellname != 'blacktop':
                    query = "select component_key, platform from component_cache where component_name='"+ \
                            cellname+"' order by timestamp desc limit 1;"
                    logger.info( "calculate_design_key(): Running query on cldb as "+query)
                    rc = cldb.execute(query).fetchall()
                    if len(rc) == 0:
                        logger.error( 'Error: component '+cellname+' not registered.  Stopping.')
                        logger.error("Register the missing components and resubmit.")
                        exit(-1)
                    ckey.update({ cellname : rc[0][0]} )
                    part = rc[0][1]
                    logger.debug( "RUN Component "+cellname+"--"+rc[0][0]+" platform "+part)
                    logger.info( "RUN Component "+cellname+"--"+rc[0][0]+" platform "+part)
            dathash = hashlib.sha1(datline+ dathash).hexdigest()

    # Hash for DAT file complete --> dathash
    # Look-up project key
    get_info_from_keyfile('project', keyfilename=keyfile, fieldname='key' )
    get_info_from_keyfile('project', keyfilename=keyfile, fieldname='platform' )
    # Create components file
    fcomp = open(os.path.join(builddir,CL_COMPILE_FILE),'w')
    fcomp.write('[compile]\n')
    fcomp.write('project_key = "'+PRJ_KEY_INFO["key"]+'"\n')
    fcomp.write('platform = "'+PRJ_KEY_INFO["platform"]+'"\n')
    for compname,compkey in ckey.iteritems(): 
       fcomp.write('component = ["'+compname+'": "'+compkey+'"]\n')
    #
    """ SSH KEY Generation
    # from subprocess import Popen, PIPE, STDOUT
    if not os.path.isfile( CL_SSHKEYFILE ):
        print "NO SSHKEY FOUND -- Generating"
        # Create rsa key pair
        fnull = open(os.devnull, 'w')
        p = Popen(['/usr/bin/ssh-keygen', '-t', 'rsa', '-q', '-f', \
                 CL_SSHKEYFILE ],stdin=PIPE, stdout=PIPE)
        p.communicate(input=b'y\n\n\n')
    with open( CL_SSHKEYFILE+'.pub', 'r') as fssh:
        fexchkey = fssh.read().strip()
    fcomp.write('sshpubkey=\''+fexchkey+'\'\n')
    """
    fcomp.close()
    # Use this information to form an index for design cache
    comp_sum = hashlib.sha1(PRJ_KEY_INFO["key"]+dathash).hexdigest()
    for acomp in ckey.itervalues(): 
        comp_sum = hashlib.sha1(comp_sum+acomp).hexdigest()

    return comp_sum, PRJ_KEY_INFO["key"], ckey, PRJ_KEY_INFO["platform"]


####################################################################
# initialize_db
####################################################################
def initialize_db():
    return really_initialize_db(False)

####################################################################
# really_initialize_db
####################################################################
def really_initialize_db(really):
    """ really_initialize_db()
    Gives you an opportunity to think it over.  The world will not end if you delete this
    cache -- it will rebuild in time.
    """
    global cldb
    if os.path.isfile(CL_DATABASE):
        if not really:
            logger.warning( 'CL component cache already exists. Will not overwrite it.  Really=False ')
            return False
        else:
            os.remove(CL_DATABASE)
    cldb = sqlite3.connect( CL_DATABASE )

    # Get DB snapshot from pybombs distribution
    print CL_DISTRIB_DB
    if not os.path.isfile(CL_DISTRIB_DB):
        logger.error( 'Cannot find distribution database: '+CL_DISTRIB_DB+'. Please check your installation.')
	exit(1)
    try:
	with zipfile.ZipFile(CL_DISTRIB_DB) as zf:
           zf.extractall(os.environ['HOME'])
	   
    except Exception as err:
        print err[0]
        logger.error( 'Difficulty installing the component cache:' + err[0] + '. ')
	exit(1)

    # Sanity check -- make sure it now exists
    if not os.path.isfile(CL_DATABASE):
        logger.error( 'Cannot find distribution database: '+CL_DISTRIB_DB+'. Please check your installation.')
	exit(1)

    logger.info("Design / component database created.")
    cldb.commit()
    return True


####################################################################
# push_component
####################################################################
def push_component( comp_root_dir, component_name, keyfile = "keyfile.conf" ):
    """ push_component()
    This is invoked to add a component, expressed in terms of a variety of shapes
    in the 'comp_root_dir' to the server database, where a key is generated.  The key is
    then added to the local database for subsequent runs.
    """
    # Get project key
    logger.info( "Pushing component "+component_name+" up to server.")
    global PRJ_KEY_INFO
    get_info_from_keyfile('project', keyfile, fieldname='key')
    get_info_from_keyfile('project', keyfile, fieldname='platform')
    # Make sure component structure is correct
    if not os.path.isdir(comp_root_dir):
        logger.error( "Error in push_component: cannot find component root in "+comp_root_dir)
        graceful_exit()
    salt = hashlib.sha1(str(random.random())).hexdigest()[:12]
    tfilename = os.path.join(CL_WORKDIR, salt+'_comp.tgz' )
    tar = tarfile.open(tfilename, "w:gz")
    tar.add(keyfile, arcname='keyfile.conf')
    ls = glob.glob(comp_root_dir+'/'+component_name+"_*")
    dbfiles=[]
    print ls
    if not ls:
      logger.error( "Error in push_component: No component with name "+component_name+" in component library "+comp_root_dir);
      graceful_exit()
    for a in ls:
        # Some initial easy checking
        if not os.path.isdir(a):
            # Only a component configuration file (optional) is allowed here
            if not os.path.basename(a) == CL_COMPONENT_CONF:
                logger.warning("Unexpected file in component tree: "+a)
                graceful_exit()
            tar.add(a, arcname=os.path.basename(a))
            continue
        logger.info( "Checking component directory "+os.path.basename(a))
        bitfilelist = glob.glob(a+'/*bit')
        if len(bitfilelist) != 1:
            logger.error("Wrong number of bit files in "+a)
            graceful_exit()
       
        metafilelist = glob.glob(a+'/*meta')
        if len(metafilelist) != 1:
            logger.error( "Wrong number of meta files in "+a)
            graceful_exit()
        # Add metafile
        shape = str(a.split('_')[-1])
        cname = os.path.basename(a[:a.rindex('_')])
        dbfiles.append([bitfilelist[0],metafilelist[0],shape, cname])
        baseofa = os.path.basename(a)
        baseofmeta = os.path.basename(metafilelist[0])
        tar.add(metafilelist[0], arcname=os.path.join(baseofa,baseofmeta))
  
    tar.close()
    
    # Push to server and pull component credentials
    if not transport_component(tfilename, salt, CL_WORKDIR):
    #if this succeeded, the component key will be returned in the work directory
        logger.error( "Component transport to the server failed.")
        graceful_exit()
    project_keyfile = salt+'_key.conf'
    project_keypath = os.path.join( CL_WORKDIR, project_keyfile)
    logger.info("project_keypath = "+project_keypath)
    if not os.path.isfile( project_keypath ):
        logger.error( "Could not place component return package in CL_WORKDIR. CL_WORKDIR = " + CL_WORKDIR)
        graceful_exit()
    get_info_from_keyfile('component', keyfilename = project_keypath, fieldname = "key")
    logger.info(PRJ_KEY_INFO)
    # Add files to local database
    logger.info("Component database opened.")
    open_cl_database()
    logger.info("Adding to database.")
    for db in dbfiles:
        add_component( COMP_KEY_INFO["key"], \
                component_name = db[3], \
                bit_filename=db[0], \
                meta_filename=db[1], \
                shape = db[2], \
                platform = PRJ_KEY_INFO['platform'], \
                group_member = 'PRIVATE')
        
    logger.info("Component added and registered.")


####################################################################
# add_component
####################################################################
def add_component( component_key, component_name, bit_filename, meta_filename, \
                   family = PRJ_KEY_INFO["family"], \
                   part = PRJ_KEY_INFO["part"], \
                   platform = PRJ_KEY_INFO["platform"],
                   group_member = 'PRIVATE', \
                   shape = 1, \
                 ):
    """ add_component() 
    Inserts a component into the CLDB.
    Args:
       component_key: server-generated component key
       component_name: as in GRC
       bit_filename: generated component bitfile
       meta_filename: generated metafile name
       family: FPGA generation name (optional, default=PRJ_KEY_INFO["family"])
       part:   FPGA part number (optional, default=PRJ_KEY_INFO["part"])
       platform: FPGA platform (optional, default=PRJ_KEY_INFO["platform"])
       group_member: (optional, default=PRIVATE)
       shape: which generated component (optional, default=1)
    Return:
       True if succeeded
    """
    # Check if key is already in the database
    query = 'select component_name from component_cache where component_key=\"' \
                          +component_key+'" and shape='+str(shape)+';'
    logger.info(query)
    record = cldb.execute(query).fetchall()
    logger.info(record)
    if len(record) > 0:
        logger.error( "Component ("+component_name+") already registered.  Failed.")
        graceful_exit()
    # Check if files exist first
    if not os.path.isfile( bit_filename):
        logger.error( "Cannot find bitfile "+bit_filename)
        graceful_exit()
    if not os.path.isfile( meta_filename):
        logger.error( "Error: cannot find metafile "+meta_filename)
        graceful_exit()
    # Load files into buffers
    with open(bit_filename, 'rb') as f:
        bitblob  = f.read()
    f.close()
    with open(meta_filename, 'rb') as f:
        metablob  = f.read()
    f.close()
    # Add into database
    sqlcmd = 'INSERT INTO component_cache (component_key, family, platform, part, component_name, group_member, shape, bitfile, metafile) VALUES("'+ \
                 component_key+'", "'+ \
                 family +'", "'+ \
                 platform +'", "'+ \
                 str(part)+'", "'+ \
                 component_name +'", "'+ \
                 group_member +'", '+ \
                 str(shape) +', ?, ?);'
    cldb.execute(sqlcmd, [buffer(bitblob), buffer(metablob)])
    cldb.commit()



####################################################################
# dump_components
####################################################################

def dump_components():
    """ dump_components()
    A simple diagnostic tool for examining the components registered in the local cache.
    """
    sqlcmd = 'select timestamp, component_name, family, part, group_member, shape from component_cache;'
    rc = cldb.execute(sqlcmd).fetchall()
    # Header
    print '\n%%%% LOCALLY CACHED COMPONENTS'
    print '__________________________________________________________________________________________'
    print '  DATE    |  NAME                          |  FAMILY        | PART     | GROUP      |SHAPE'
    print '------------------------------------------------------------------------------------------'
    lp = []
    for dd in rc:
        ap = []
        for ee in dd:
            if ee == None:
                ee = '...'
            ap.append(ee)
        lp.append(ap)
    for dd in lp:
       print dd[0][:10] + (10-len(dd[0]))*' ' + "|" +\
          dd[1][:32] + (32-len(dd[1]))*' ' + "|" +\
          dd[2][:16] + (16-len(dd[2]))*' ' + "|" +\
          dd[3][:10] + (10-len(dd[3]))*' ' + "|" +\
          dd[4][:12] + (12-len(dd[4]))*' ' + "| " + \
          str(dd[5])
    print '__________________________________________________________________________________________'


####################################################################
# dump_design_cache
####################################################################

def dump_design_cache():
    """ dump_design_cache()
    A simple diagnostic tool for examining the design cache.
    """
    sqlcmd = 'select timestamp, design_key, platform, part from design_cache;'
    rc = cldb.execute(sqlcmd).fetchall()
    # Header
    print '\n%%%% LOCALLY CACHED PRECOMPILED DESIGNS'
    print '________________________________________________________________________________________'
    print '  DATE             |  KEY                                           |  BOARD     | PART      '
    print '----------------------------------------------------------------------------------------'
    lp = []
    for dd in rc:
        ap = []
        for ee in dd:
            if ee == None:
                ee = '...'
            ap.append(ee)
        lp.append(ap)
    for dd in lp:
       print dd[0][:19] + (19-len(dd[0]))*' ' + "|" +\
          dd[1][:48] + (48-len(dd[1]))*' ' + "|" +\
          dd[2][:12] + (12-len(dd[2]))*' ' + "|" +\
          str(dd[3])
    print '________________________________________________________________________________________'
           
####################################################################
# extract components
####################################################################
def extract_components( key, workdir=CL_WORKDIR ):
    """ extract_components()
    Extract the bit file associated with the component indexed by 'key'
    and save the results in 'component_name'.bit.
    Args:
       key: component key
    """
    open_cl_database()
    rc = cldb.execute("select component_name, shape, bitfile from component_cache where component_key='"+key+"';").fetchall()
    if len(rc) == 0:
        logger.error( "Extract component failed.  Could not find key "+key)
        return False
    # Check to see if there is a place to extract the files
    if not os.path.isdir( workdir):
        os.mkdir( workdir)
    for entry in rc:
        cname = entry[0]
        shape = entry[1]
        logger.info( "Extracting component "+cname+" shape "+str(shape)+" from local cache. " )
        comppath = os.path.join(workdir, cname+'_'+str(shape))
        if os.path.isdir( comppath):
            logger.warning( "Path to component exists: "+comppath)
        else:
            os.mkdir( comppath )
        with open(os.path.join(comppath,cname+".bit"), "wb") as bit_file:
            bit_file.write(entry[2])
        bit_file.close()

    return True


####################################################################
# extract design
####################################################################
def extract_design( key, builddir = CL_WORKDIR ):
    """ extract_design()
    Extract the cached design from the design cache.
    Args:
       key: design hash key
    """
    open_cl_database()
    logger.info("Extracting design from design cache.")
    rc = cldb.execute("select assembly_file from design_cache where design_key='"+key+"';").fetchall()
    if len(rc) != 1:
        logger.error( "Extract design failed.  Could not find key "+key)
        graceful_exit()
    with open(builddir+"/"+"assembly.dat", "wb") as asm_file:
        asm_file.write(rc[0][0])
    asm_file.close()
    logger.info("Precompiled design extracted. design located at ")
    
           
           
####################################################################
# assemble_design
####################################################################
def assemble_design(builddir = CL_WORKDIR, keyfile="keyfile.conf", part=PRJ_KEY_INFO["part"], datfile="edif.dat"):
    """ assemble_design()
    This is invoked in the assembly process to first check to see if the design, present
    in the 'builddir' has already been assembled.  If so, it will be retreived out of cache.
    If not, it will go to the server to be rebuilt.  When complete, the rda_loader needs to
    be called, followed by post_assembly.
    """
    salt = hashlib.sha1(str(random.random())).hexdigest()[:12]
    design_key,project_key,component_keys, platform = calculate_design_key(builddir, datfile, keyfile)
    print design_key
    for eachkey in component_keys.itervalues(): 
        extract_components(eachkey, builddir)
    if is_in_design_cache(design_key):
        logger.info( "Design has already been compiled and is in the design cache")
        extract_design(design_key, builddir)
        logger.info( "Obtain assembly.dat from cache and process it with rda_loader")
    else:
        logger.info( "Design is NOT in the cache.  Push bundle to server.")
        logger.info( "Creating a cache entry ("+design_key+") and inserting assembly data.")
        # Create tarball of processing package and name it after the key
        logger.info( "Transferring compile request to server")
        tfilename = os.path.join(builddir, salt+'_run.tgz' )
        tar = tarfile.open(tfilename, "w:gz")
        tar.add(datfile, arcname = os.path.basename(datfile))
        tar.add(os.path.join(builddir,CL_COMPILE_FILE), arcname = CL_COMPILE_FILE)
        tar.close()
        if transport_assembly_run( salt, tfilename, builddir ):
        #if 1:
            # Compile succeeded.  Insert assembly.dat into design cache
            assmfile = os.path.join(builddir, CL_ASSEMBLY_FILE)
            if not os.path.isfile(assmfile):
                logger.error( "Result file "+CL_ASSEMBLY_FILE+" does not exist.")
                graceful_exit()
            with open(assmfile, 'rb') as f:
                asmblob  = f.read()
            f.close()
            # Add into database
            sqlcmd = 'INSERT INTO design_cache (design_key, platform, part, assembly_file) VALUES("'+ \
                    design_key+'", "'+ \
                    platform +'", "'+ \
                    part + '", (?));'
            logger.info("execute sql command: "+sqlcmd)
            cldb.execute(sqlcmd, [buffer(asmblob)])
            cldb.commit()
        else:
           logger.error( "Server failed to assemble design.  Examine the log file in the build directory.")
           graceful_exit()
    close_cl_database()
    logger.info( "Ready to call rda_loader in directory: "+os.path.abspath(builddir))

####################################################################
# main (for testing)
####################################################################

import shutil
if __name__ == "__main__":
    build_environment()
    if not os.path.isdir(CL_WORKDIR):
        print "Creating work directory: "+CL_WORKDIR
        os.mkdir(CL_WORKDIR)
    enable_logging()
    while not open_cl_database():
        logger.warning( "Database does not exist.  Creating.")
        really_initialize_db(True)
    print "====================================================="
    print "Testing components database."
    dump_components()
    print "====================================================="
    print "Testing designs database."
    dump_design_cache()
    
