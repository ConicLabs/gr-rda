INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_RDA rda)

FIND_PATH(
    RDA_INCLUDE_DIRS
    NAMES rda/api.h
    HINTS $ENV{RDA_DIR}/include
        ${PC_RDA_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    RDA_LIBRARIES
    NAMES gnuradio-rda
    HINTS $ENV{RDA_DIR}/lib
        ${PC_RDA_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
)

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(RDA DEFAULT_MSG RDA_LIBRARIES RDA_INCLUDE_DIRS)
MARK_AS_ADVANCED(RDA_LIBRARIES RDA_INCLUDE_DIRS)

