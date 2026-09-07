# ASTER standard methods

The root package defines the standard LS4T-DATA, projection, explicit mosaic,
study-area and configurable split-window LST interfaces for ASTER channels 13
and 14. No native ASTER HDF reader has been accepted yet. `aster_extract`
therefore starts from reviewed prepared arrays; a real native reader must first
be validated in `cases/aster/` before promotion here.
