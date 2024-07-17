# Bezel Project Renamer

## What is this?

When you get the Bezel Project unless your ROM sets are NoIntro sets you must rename your ROMs. What this software does is instead rename the config files that Bezel Project ships with. This project is specifically for "theme" sets.

## How does it work?

What this script does is CRC check every single rom you have and rename the config files associated with the roms. This should have 100% compatability with literally anything as a result, removing the ROM name requirement. If you find a ROM that isn't compatible, find a compatible DAT file that's also compatible with the Bezel Project's naming conventions (probably NoIntro, but you might need older DATs sometimes as Bezel Project is several years behind on some names).

## Requirements

`pip3 install PyGithub py7zr` (might need `--break-system-packages` on debian based systems ... it doesn't break system packages, they just want to scare you, it installs locally, just don't run as root)

These requirements could likely be made optional in the future.

## Usage

The following command would fix all the Bezel Project configs for N64 (it doesn't modify anything in the rom directory):

`python3 renamer.py ~/RetroPie/roms/n64`

## Caveats

This script was written to solve a problem, but hasn't had work beyond that so there are some quirks:

1. You must be inside the same directory as `renamer.py`.
2. You must not have a trailing slash at the end of the command.

### Q: What if I no longer want the changes provided by this script?
**A: Simply re-install Bezel Project. You could go as far as to delete all the added config files as well.**

### Q: Why doesn't the bezel show up on my game still?
**A: Either the CRC isn't in your DAT, or the name provided by the DAT is different than what Bezel Project uses, or they simply don't have a bezel for that game.**

### Q: What systems are supported?
**A: Check out `renamer.py`, if it's in the supported system list it's supported, but if it's missing the dat it still needs that. Arcade is not supported, and likely won't be.**

## License

Honestly I'd really like it if the Bezel Project could include code like this in the future, so if someone gets in contact with me I'll change the license to whatever they need or help with whatever.