#!/bin/bash

DEFAULT=/ #we get the relative path, usr/share/terminator/terminatorlib/plugins/host_watch.py from the git repo dir structure.
FALLBACK=~/.config/terminator/plugins/host_watch.py
FILES=$(ls files)
PLUGIN_FILE=$(find . -name \*host_watch.py -print)


echo installing TerminatorHostwatch...

if [ $# -eq 0 ]
then
  echo installing to default location: $DEFAULT
  {
          echo attempting install...  
	  install -D files/* $DEFAULT
  } || {
	  echo falling back to userland install since no sudo.
          install -D $PLUGIN_FILE $FALLBACK
  }
else
  echo installing to $1     	
  install -D $PLUGIN_FILE $1 
fi 

