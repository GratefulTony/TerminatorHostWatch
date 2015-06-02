#!/usr/bin/python
# Terminator plugin by GratefulTony
# GPL v2 only
"""hostWatch.py - Terminator Plugin to watch a terminal for hostname, and apply a host-dependant profile"""

import time
import gtk
import gobject
import terminatorlib.plugin as plugin

from terminatorlib.translation import _
from terminatorlib.util import err, dbg
from terminatorlib.version import APP_NAME
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
    """Add custom commands to the terminal menu"""
    watches = {}
    hostsWeCareAbout = {}
    currentBestGuessHost = 'localhost'    
    
    def __init__(self):
        self.watches = {}
        self.updateTerms()
        self.hostsWeCareAbout = Terminator().config.list_profiles()
        
    def updateTerms(self):
        #t = threading.Timer(self.termRefreshInterval, self.updateTerms)
        #t.daemon = True
        #t.start()
        #print "update terms..."
        for terminal in Terminator().terminals:
            if terminal not in self.watches:
                self.watch(None, terminal)

    def watch(self, _widget, terminal):
        """Watch a terminal"""
        vte = terminal.get_vte()
        self.watches[terminal] = vte.connect('contents-changed', self.checkhost, terminal)

    def checkhost(self, _vte, terminal):
        """Our host might have changed..."""
#        now = time.time()
#        if now > self.lastCheckedTerms + self.termRefreshInterval:
#            self.lastCheckedTerms = now
#            for terminal in Terminator().terminals:
#                self.watch(None, terminal)
        self.updateTerms()
        show_notify = False
        allText = terminal.get_vte().get_text(lambda *a: True).splitlines()
        text = next(s for s in reversed(allText) if s).split()[0].split('@')[1].split(':')[0]

        if text != self.currentBestGuessHost:
            #Ideally, we should doublecheck the hostname instead of trusting our parse job.
            # print "cmd" + terminal.get_vte().fork_command(None, ['/bin/bash','hostname'])
            self.currentBestGuessHost = text
            dbg( "switched to " + text)

        profile = 'default'
        if self.currentBestGuessHost in terminal.config.list_profiles():
            profile = self.currentBestGuessHost

        terminal.set_profile(None, self.currentBestGuessHost, False)
                    
        return True
