# Terminator HostWatch Plugin
This plugin monitors the last line (PS1) of each terminator terminal, and applies a host-specific profile if the hostname is changed. 

The plugin simply parses the PS1-evaluated last line and matches it against the regex `[^@]+@(\w+)` (e.g. to match `user@host`).

If last line too short (PS1 may be two-lines text, with prompt on last line), the plugin searches for regex in the line above the prompt.
Eg. :
```
[user@host /a/very/long/path] /dev/pts/42
$ 
```

Profiles are either :
  - plain hostname
  - a regexp

The plugin searches for hostname exact profile matching or hostname matching profile regexp.

Eg. :
```
[profiles]
  # matches hostname like ns123456
  [[ns[0-9]+]]
    ...
  # matches hostname like ip-172-16-1-2
  [[ip+]]
    ...
  # matches hostname like prd-server-1
  [[prd-*]]
    ...
```

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
Put the `host_watch.py` in `/usr/share/terminator/terminatorlib/plugins/` or `~/.config/terminator/plugins/`. Then create a profile in Terminator to match your hostname. If you have a server that displays `user@myserver ~ $`, for instance, create a profile called `myserver`.

## Configuration
For now, the only setting you can change is the regex patterns the plugin will react on. The default pattern is `[^@]+@(\w+)` (e.g. `user@host`). To change that, add this to your .config/terminator/config file and adjust the regexes accordingly:

```
[plugins]
  [[HostWatch]]
    patterns = "[^@]+@(\w+):([^#]+)#", "[^@]+@(\w+) .+ \$"
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
   HostWatch::check_host: switching to profile EMEA0014, because line 'pheckel@EMEA0014 ~ $ ' matches pattern '[^@]+@(\w+)'
   HostWatch::check_host: switching to profile kartoffel, because line 'root@kartoffel:~# ' matches pattern '[^@]+@(\w+)'
   ...
```

## Authors
The plugin was developed by GratefulTony (https://github.com/GratefulTony/TerminatorHostWatch), 
and extended by Philipp C. Heckel (https://github.com/binwiederhier/TerminatorHostWatch).

## License
The plugin is licensed as GPLv2 only.
