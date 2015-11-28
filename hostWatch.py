#!/usr/bin/python
#
# HostWatch Terminator Plugin
# Copyright (C) 2015 eGratefulTony & Philipp C. Heckel
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
NAME
  hostWatch.py - Terminator plugin to apply a host-dependant terminal profile

DESCRIPTION
  This plugin monitors the last line of each terminator terminal, and applies a 
  host-specific profile if the hostname is changed.

INSTALLATION
  Put this .py in /usr/share/terminator/terminatorlib/plugins/hostWatch.py 
  or ~/.config/terminator/plugins/hostWatch.py.

  Then create a profile in Terminator to match your hostname. If you have a
  server that displays 'user@myserver ~ $', for instance, create a profile
  called 'myserver'.  

DEVELOPMENT
  Development resources for the Python Terminator class and the 'libvte' Python 
  bindings can be found here:

  For terminal.* methods, see: 
    - http://bazaar.launchpad.net/~gnome-terminator/terminator/trunk/view/head:/terminatorlib/terminal.py
    - and: apt-get install libvte-dev; less /usr/include/vte-0.0/vte/vte.h

  For terminal.get_vte().* methods, see:
    - https://github.com/linuxdeepin/python-vte/blob/master/python/vte.defs
    - and: apt-get install libvte-dev; less /usr/share/pygtk/2.0/defs/vte.defs

DEBUGGING
  To debug the plugin, start Terminator from another terminal emulator 
  like this:

     $ terminator --debug-classes=HostWatch

  That should give you output like this:

     HostWatch::check_host: switching to profile mypc
     HostWatch::check_host: switching to profile myserver
     ...

AUTHORS
  The plugin was developed by GratefulTony (https://github.com/GratefulTony/TerminatorHostWatch), 
  and extended by Philipp C. Heckel (https://github.com/binwiederhier/TerminatorHostWatch).
"""

import re
import terminatorlib.plugin as plugin

from terminatorlib.util import err, dbg
from terminatorlib.terminator import Terminator

try:
    import pynotify
    # Every plugin you want Terminator to load *must* be listed in 'AVAILABLE'
    # This is inside this try so we only make the plugin available if pynotify
    #  is present on this computer.
    AVAILABLE = ['HostWatch']
except ImportError:
    err(_('HostWatch plugin unavailable'))

class HostWatch(plugin.Plugin):
    watches = {}
    profiles = {}
    hostmatch = re.compile(r"[^@]+@(\w+)")
    
    def __init__(self):
        self.watches = {}
        self.profiles = Terminator().config.list_profiles()
        self.update_watches()
        
    def update_watches(self):
        for terminal in Terminator().terminals:
            if terminal not in self.watches:
                self.watches[terminal] = terminal.get_vte().connect('contents-changed', self.check_host, terminal)

    def check_host(self, _vte, terminal):
        """Our host might have changed..."""

        self.update_watches()

        last_line = self.get_last_line(terminal)

        if last_line:
            match = self.hostmatch.match(last_line)
            if match:
                hostname = match.group(1)
                if hostname in self.profiles:
                    if hostname != terminal.get_profile():
                        dbg("switching to profile " + hostname)
                        terminal.set_profile(None, hostname, False)
                else:
                    dbg("no profile " + hostname + "; you must create a profile manually first.")
                    
        return True

    def get_last_line(self, terminal):
        """Retrieve last line of terminal (contains 'user@hostname')"""

        vte = terminal.get_vte()

        cursor = vte.get_cursor_position()
        column_count = vte.get_column_count()
        row_position = cursor[1]

        start_row = row_position
        start_col = 0
        end_row = row_position
        end_col = column_count
        is_interesting_char = lambda a, b, c, d: True

        lines = vte.get_text_range(start_row, start_col, end_row, end_col, is_interesting_char).splitlines()

        if lines and lines[0]:
            return lines[0]
        else:
            return None

