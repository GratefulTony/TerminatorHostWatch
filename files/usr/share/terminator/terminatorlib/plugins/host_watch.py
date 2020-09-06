#!/usr/bin/python
#
# HostWatch Terminator Plugin
# Copyright (C) 2015 GratefulTony & Philipp C. Heckel
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
  This plugin monitors the last line (PS1) of each terminator terminal, and
  applies a host-specific profile if the hostname is changed.

PROMPT MATCHING
  The plugin simply parses the PS1-evaluated last line and matches it against
  a regex "[^@]+@(\w+)" ((e.g. user@host) to find hostname.

PROFILE MATCHING
  Once an hostname is found, the plugin tries to match it against the profiles.
  Profiles might be :
  - plain hostnames
  - or regex
  The configuration allow to create matching rules for hostname pattern against
  profile.

PROMPT WRAPPING

  PS1 might be displayed in more than one line, for instance if :
  - very long path, wrapping over several lines
  - terminal window too small
  - PS1 set up for 2 lines

  E.g. :
  - geeky and informational PS1 :
  [user@host very/long/path] /dev/pts/42
  $

  - unusually long PS1 due to full path display :
  [user@host a/very/very/long/and/annoying/psychopathic/library/of/whatever/appl
  lication/path/that/wraps]$

  We search the first line of PS1 by searching back for last LF character in
  terminal history from current cursor position. The line following that LF is
  the PS1 first line, expected to contain 'user@host' pattern.

  To avoid unecessary treatment, a minimal prompt length might be set, mandatory
  if two-lines PS1 is used.
  A minimal line length is also set up, to avoid unecessary pattern search for
  short lines, or lines being typed and not complete.

  Profile name is a plain name (the hostname), or a regexp.
  The plugin checks for exact match between hostname and profile, or profile
  pattern and hostname.

INSTALLATION

  Put this .py in /usr/share/terminator/terminatorlib/plugins/hostWatch.py
  or ~/.config/terminator/plugins/hostWatch.py.

  Then create a profile in Terminator to match your hostname. If you have a
  server that displays 'user@myserver ~ $', for instance, create a profile
  called 'myserver'.

  Profiles names/regexp are evaluated in a non-predictable order, so be careful
  with your regexp and be as specific and restrictive as possible.

CONFIGURATION

  Plugin section in .config/terminator/config :
  [plugins]
    [[HostWatch]]

  Configuration keys :
  - prompt patterns : for prompt matching
    key : patterns
    value : a regex list. Default if not set : "[^@]+@(\w+)" (e.g. user@host)
    E.g :
    patterns = "[^@]+@(\w+):([^#]+)#", "[^@]+@(\w+) .+ \$"

  - profile patterns : searches profile against hostname pattern
    key : profile_patterns
    value : dict-like list, pattern:profile. Default if not set : None
    E.g :
    profile_patterns = "jenkins":"inf","^itg-*":"itg","^ip-10-1-*":"itg",
    "^ns[0-9]+":"ovh","^sd-[0-9]+":"ovh","aramis":"local"

    profiles are search in order, by profile patterns, then by profile name
    (that can also be a pattern, so be carefull with mixed-up config)

  - minimal prompt length : triggers backward search (see wrapping above)
    Adapt this to your usual prompt length. If PS1 is a two lines prompt (see
    above), might be 2 chars (prompt char+space).
    key : prompt_minlen
    value : an int. Default if not set : 3

  - minimal line length : minimal length of line for pattern search when PS1
    candidate line has been found.
    Adapt this to your usual PS1 length.
    key : line_minlen
    value : an int. Default if not set : 10

  - failback profile : profile if no matching pattern/profile found
    key : failback_profile
    value : a string. Default if not set : 'default'

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

     HostWatch::check_host: switching to profile EMEA0014, because line 'pheckel@EMEA0014 ~ $ ' matches pattern '[^@]+@(\w+)'
     HostWatch::check_host: switching to profile kartoffel, because line 'root@kartoffel:~# ' matches pattern '[^@]+@(\w+)'
     ...

AUTHORS
  The plugin was developed by GratefulTony (https://github.com/GratefulTony/TerminatorHostWatch),
  and extended by Philipp C. Heckel (https://github.com/binwiederhier/TerminatorHostWatch).
"""

import re
import terminatorlib.plugin as plugin

from terminatorlib.util import err, dbg
from terminatorlib.terminator import Terminator
from terminatorlib.config import Config
from collections import OrderedDict

# Every plugin you want Terminator to load *must* be listed in 'AVAILABLE'
# This is inside this try so we only make the plugin available if pynotify
#  is present on this computer.
AVAILABLE = ['HostWatch']


class HostWatch(plugin.Plugin):
    dbg("loading HostWatch")
    watches = {}
    config = {}
    profile_mappings = OrderedDict()
    capabilities = ['host_watch']
    patterns = []
    prompt_minlen = 0
    line_minlen = 10
    failback_profile = 'default'
    AVAILABLE = ['HostWatch']

    def __init__(self):
        self.config = Config().plugin_get_config(self.__class__.__name__)
        self.watches = {}
        self.prompt_minlen = int(self.get_prompt_minlen())
        self.line_minlen = int(self.get_line_minlen())
        self.failback_profile = self.get_failback()
        self.last_profile = self.failback_profile
        self.load_patterns()
        self.load_profile_mappings()
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
            sel_profile = self.failback_profile
            for prompt_pattern in self.patterns:
                match = prompt_pattern.match(last_line)
                if match:
                    hostname = match.group(1)
                    dbg("match search pattern : %s (%s) ->%s" % (prompt_pattern.pattern, last_line, hostname))
                    dbg(self.profile_mappings)
                # since dict is ordered, iterate regexp/mapping, then profiles
                    for profile_pattern, profile in self.profile_mappings.items():

                        # we create a pattern based on profile name
                        # profile_pattern=re.compile(profile)
                        if hostname == profile or profile_pattern.match(hostname):
                            dbg(
                                "matching profile '" + profile + "' found : line '" + last_line + "' matches prompt pattern '" + prompt_pattern.pattern + "' and profile pattern '" + profile_pattern.pattern + "'")
                            sel_profile = profile
                            # break on first profile match
                            break

                    # avoid re-applying profile if no change
                    if sel_profile != self.last_profile or True: # disabled this check, profile wasnt updating for multiple splits. todo: revisit.
                        dbg("setting profile " + sel_profile)
                        terminal.set_profile(None, sel_profile, False)
                        self.last_profile = sel_profile
                    # break on first pattern match
                    break

        return True

    def get_last_line(self, terminal):
        """Retrieve last line of terminal (contains 'user@hostname')"""
        ret = None
        vte = terminal.get_vte()

        cursor = vte.get_cursor_position()
        column_count = vte.get_column_count()
        row_position = cursor[1]

        start_row = row_position
        start_col = 0
        end_row = row_position
        end_col = column_count
        is_interesting_char = lambda a, b, c, d: True

        """ manage text wrapping :
        usecases :
        - PS1 too long
        - componant of PS1 forcing display on several lines (e.g working directory)
        - window resizing
        - ...
        So, very ugly algorithm
        if current line too short, we assume prompt is wrapped
        we the search for 1st line of prompt, that is : first line following the
        last line containing LF
        we iterate back until LF found (means : end of output of last command), 
        then forward one line
        """
        lines = vte.get_text_range(start_row, start_col, end_row, end_col, is_interesting_char)[0]

        if lines and lines[0]:
            # line too short, iterate back
            if len(lines) <= self.prompt_minlen:
                dbg("line below prompt min size of " + str(
                    self.prompt_minlen) + " chars : must iterate back")
                start_row = start_row - 1
                end_row = start_row
                lines = vte.get_text_range(start_row, start_col, end_row, end_col, is_interesting_char)[0]
                prev_lines = lines
                # we iterate back to first line of terminal, including history...
                while lines != None and start_row >= 0:
                    # LF found, PS1 first line is next line... eeeer previous pushed line
                    if lines[len(lines) - 1] == '\n':
                        lines = prev_lines
                        break

                    lines = vte.get_text_range(start_row, start_col, end_row, end_col, is_interesting_char)[0]
                    start_row = start_row - 1
                    end_row = start_row
                    prev_lines = lines

        lines = lines.splitlines()
        if lines and lines[0]:
            if len(lines[0]) >= self.line_minlen:
                ret = lines[0]
            else:
                # should never happen since we browse back in history
                dbg("line '" + lines[0] + "' too short, won't use : " + str(len(lines[0])))

        return ret

    def load_patterns(self):

        if self.config and 'patterns' in self.config:
            if isinstance(self.config['patterns'], list):
                for pat in self.config['patterns']:
                    self.patterns.append(re.compile(pat))
            else:
                self.patterns.append(re.compile(self.config['patterns']))
        else:
            self.patterns.append(re.compile(r"[^@]+@(\w+)"))

    def get_prompt_minlen(self):
        """ minimal prompt length, below this value, we search for PS1 on previous line """

        if self.config and 'prompt_minlen' in self.config:
            return self.config['prompt_minlen']
        else:
            return 3

    def get_line_minlen(self):
        """ minimal PS1 length, below this value, last_line returns None """

        if self.config and 'line_minlen' in self.config:
            return self.config['line_minlen']
        else:
            return 10

    def get_failback(self):
        """ failback profile, applies if profile not found. """

        if self.config and 'failback_profile' in self.config:
            return self.config['failback_profile']
        else:
            return 'default'

    def load_profile_mappings(self):
        """ get profile mapping as declared with profile_patterns config key
        and append profile names as patterns
        profiles are saved as compiled patterns in an ordered dictionary
        so patterns mappings are parsed prior to profiles
        """

        if self.config and 'profile_patterns' in self.config:
            # we have to parse and create dict since configuration doesnt allow this
            for pre in self.config['profile_patterns']:
                kv = pre.split(":")
                if len(kv) == 2:
                    # config recovered as ugly string with leading and trailing quotes removed, must remove ' and "
                    dbg("profile mapping : %s -> %s" % (
                    kv[0].replace("'", "").replace('"', ''), kv[1].replace("'", "").replace('"', '')))
                    self.profile_mappings[re.compile(kv[0].replace("'", "").replace('"', ''))] = kv[1].replace("'",
                                                                                                               "").replace(
                        '"', '')
        # we load profile name as plain regex
        for v in Terminator().config.list_profiles():
            dbg("Adding profile for " + v)
            self.profile_mappings[re.compile(v)] = v
