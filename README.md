# Terminator HostWatch Plugin
This plugin monitors the last line (PS1) of each terminator terminal, and applies a host-specific profile if the hostname is changed. 

## How it works

### Prompt matching
The plugin simply parses the PS1-evaluated last line and matches it against a regex "[^@]+@(\w+)" ((e.g. user@host) to find hostname.

### Profile matching
Once an hostname is found, the plugin tries to match it against the profiles.

Profiles might be :
 - plain hostnames
 - or regex

The configuration allow to create matching rules for hostname pattern against profile.

### Prompt wrapping
PS1 might be displayed in more than one line, for instance if :
 - very long path, wrapping over several lines
 - terminal window too small
 - PS1 set up for 2 lines

E.g. :
- geeky and informational PS1 :
```
[user@host very/long/path] /dev/pts/42
$ 
```  
- unusually long PS1 due to full path display, wrapped to terminal width :
```
[user@host a/very/very/long/and/annoying/psychopathic/library/of/whatever/appl
lication/path/that/wraps]$ 
```

We search the first line of PS1 by searching back for last LF character in terminal history from current cursor position. The line following that LF is the PS1 first line, expected to contain 'user@host' pattern.

To avoid unecessary treatment, a minimal prompt length might be set, mandatory if two-lines PS1 is used.
A minimal line length is also set up, to avoid unecessary pattern search for short lines, or lines being typed and not complete.

Profile name is a plain name (the hostname), or a regexp.
The plugin checks for exact match between hostname and profile, or profile pattern and hostname.

![Profiles](assets/terminator-hostwatch.png)

## Installation

**Debian-based systems:**   
1. Either download a `.deb`-file from the [release page](https://github.com/binwiederhier/TerminatorHostWatch/releases)   
2. Or: Add my [Debian/APT archive](http://archive.philippheckel.com/apt/):

```bash
wget -qO - http://archive.philippheckel.com/apt/Release.key | sudo apt-key add -
sudo sh -c "echo deb http://archive.philippheckel.com/apt/release/ release main > /etc/apt/sources.list.d/archive.philippheckel.com.list"
sudo apt-get update
sudo apt-get install terminator-hostwatch
```

**Other Linux systems:**   
Put the `host_watch.py` in `/usr/share/terminator/terminatorlib/plugins/` or `~/.config/terminator/plugins/`.

Minimal configuration : create a profile in Terminator to match your hostname. If you have a server that displays `user@myserver ~ $`, for instance, create a profile called `myserver`.

## Configuration
Plugins section in `.config/terminator/config` :
```
[plugins]
  [[HostWatch]]
    ...
```

### Configuration keys
The following keys are available :

- prompt patterns : for prompt matching

*key* : patterns

*value* : a regex list. Default if not set : "[^@]+@(\w+)" (e.g. user@host)

Don't forget to create a group in the regex for the `host` field (with `()`), otherwise no hostname can be extracted from regex.

E.g :
```
patterns = "[^@]+@(\w+):([^#]+)#", "[^@]+@(\w+) .+ \$"
```

- profile patterns : searches profile against hostname pattern

*key* : profile_patterns

*value* : dict-like list, `pattern:profile`. Default if not set : None

E.g :
```
profile_patterns = "jenkins":"inf","^itg-*":"itg","^ip-10-1-*":"itg","^ns[0-9]+":"ovh","^sd-[0-9]+":"ovh","aramis":"local"
```
Profiles are searched in order : first by profile patterns, then by profile name, used as patterns also (so be carefull with mixed-up config)
  
- minimal prompt length : triggers backward search (see wrapping above)

Adapt this to your usual prompt length. If PS1 is a two lines prompt (see above), might be 2 chars (prompt char+space).

*key* : prompt_minlen

*value* : integer. Default if not set : 3

E.g :
```
prompt_minlen = 8
```
- minimal line length : minimal length of line for pattern search when PS1 candidate line has been found.

Adapt this to your usual PS1 length.

*key* : line_minlen

*value* : integer. Default if not set : 10

  E.g :
```
line_minlen = 15
```
  
- failback profile : profile if no matching pattern/profile found

*key* : failback_profile

*value* : string. Default if not set : 'default'

E.g :
```
failback_profile = servers
```

## Development
Development resources for the Python Terminator class and the 'libvte' Python bindings can be found here:

For terminal.* methods, see: 
  - http://bazaar.launchpad.net/~gnome-terminator/terminator/trunk/view/head:/terminatorlib/terminal.py
  - and: `apt-get install libvte-dev; less /usr/include/vte-0.0/vte/vte.h`

For terminal.get_vte().* methods, see:
  - https://github.com/linuxdeepin/python-vte/blob/master/python/vte.defs
  - and: `apt-get install libvte-dev; less /usr/share/pygtk/2.0/defs/vte.defs`

## Debugging
To debug the plugin, start Terminator from another terminal emulator 
like this:

```
$ terminator --debug-classes=HostWatch
```

That should give you output like this:

```
   HostWatch::load_profile_mappings: profile mapping : jenkins -> itg
   HostWatch::load_profile_mappings: profile mapping : ^itg-* -> itg
   HostWatch::load_profile_mappings: profile mapping : ^ip-10-1-* -> itg
   HostWatch::load_profile_mappings: profile mapping : aramis -> local
   ...
   HostWatch::get_last_line: line below prompt min size of 6 chars : must iterate back '
'
   HostWatch::get_last_line: line below prompt min size of 6 chars : must iterate back '$ 
'
   HostWatch::check_host: match search pattern : ^\[[a-zA-Z0-9-]+@([a-zA-Z0-9-]+) * ([devel@aramis ~/.config/terminator/plugins] 14:47:50 0 /dev/pts/11) ->aramis
   HostWatch::check_host: matching profile 'local' found : line '[devel@aramis ~/.config/terminator/plugins] 14:47:50 0 /dev/pts/11' matches prompt pattern '^\[[a-zA-Z0-9-]+@([a-zA-Z0-9-]+) *' and profile pattern 'aramis'
   HostWatch::check_host: setting profile local
   ...
```

## Authors
The plugin was developed by GratefulTony (https://github.com/GratefulTony/TerminatorHostWatch), 
and extended by Philipp C. Heckel (https://github.com/binwiederhier/TerminatorHostWatch).

## License
The plugin is licensed as GPLv2 only.
