#!/bin/bash
FALLBACK=~/.config/terminator/plugins/host_watch.py
PLUGIN_FILE=$(find . -name \*host_watch.py -print)
DEFAULT=/${PLUGIN_FILE#./*/}

echo installing TerminatorHostwatch...

if [ $# -eq 0 ]
then
  echo installing to default location: $DEFAULT
  {
          echo attempting install...  
	  install -D $PLUGIN_FILE $DEFAULT
  } || {
	  echo falling back to userland install since no sudo.
          echo installing to $FALLBACK
          install -D $PLUGIN_FILE $FALLBACK
  }
else
  echo installing to $1     	
  install -D $PLUGIN_FILE $1 
fi 

