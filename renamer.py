import os, sys
import zipfile
import py7zr
import xml.etree.ElementTree as ET

from github import Github

QUIET = False
DRY_RUN = True
DEBUG = True

supported_systems = {
    "Amiga": "amiga",
    "AmstradCPC": "amstradcpc",
    "Atari2600": "atari2600",
    "Atari5200": "atari5200",
    "Atari7800": "atari7800",
    "Atari800": "atari800",
    "AtariJaguar": "atarijaguar",
    "AtariLynx": "atarilynx",
    "AtariST": "atarist",
#    "Atomiswave": "UNKNOWN",
    "C64": "c64",
#    "CD32": "UNKNOWN",
#    "CDTV": "UNKNOWN",
    "ColecoVision": "coleco",
    "Dreamcast": "dreamcast",
    "FDS": "fds",
    "Famicom": "nes",
    "GB": "gb",
    "GBA": "gba",
    "GBC": "gbc",
    "GCEVectrex": "vectrex",
    "GameGear": "gamegear",
    "Intellivision": "intellivision",
    "MAME": "mame-libretro",
    "MSX": "msx",
    "MSX2": "msx",
    "MasterSystem": "mastersystem",
    "MegaDrive": "megadrive",
    "N64": "n64",
    "NDS": "nds",
    "NES": "nes",
    "NGP": "ngp",
    "NGPC": "ngpc",
#    "Naomi": "UNKNOWN",
#    "PCE-CD": "UNKNOWN",
    "PCEngine": "pcengine",
    "PSX": "psx",
#    "SFC": "UNKNOWN",
    "SG-1000": "sg-1000",
    "SNES": "snes",
    "Saturn": "saturn",
    "Sega32X": "sega32x",
    "SegaCD": "segacd",
#    "SuperGrafx": "UNKNOWN",
#    "TG-CD": "UNKNOWN",
#    "TG16": "UNKNOWN",
    "Videopac": "videopac",
    "Virtualboy": "virtualboy",
#    "X68000": "UNKNOWN",
#    "ZX81": "UNKNOWN"
}

main_system = ""

def get_system_from_rom_dir(rom_dir):
    # grab just the last part of the path, in case it's a full path
    rom_dir = os.path.basename(rom_dir)
    for system, s_rom_dir in supported_systems.items():
        if s_rom_dir == rom_dir:
            return system
    return None

# Check args if we have a directory, if so, grab the rom directory name from it, and see if we get a system name
if len(sys.argv) > 1:
    rom_dir = sys.argv[1]
    system = get_system_from_rom_dir(rom_dir)
    if system:
        main_system = system
        if not QUIET:
            print(f"System: {system}")
    else:
        print(f"System not found for directory: {rom_dir}")
        sys.exit()
else:
    print("Usage: Run after bezel project setup, provide the rom directory as an argument.")
    sys.exit()

config_dir = '/opt/retropie/configs/all/retroarch/config/'

g = Github()

repo = g.get_repo("thebezelproject/bezelproject-%s" % main_system)
contents = repo.get_contents("retroarch/config")

supported_emulators = [content.name for content in contents if content.type == "dir"]

# Function to calculate CRC32 of a file
def calculate_crc32(file_data):
    crc = zipfile.crc32(file_data) & 0xFFFFFFFF
    return format(crc, '08x')

# Function to calculate CRC32 of a plain file
def calculate_crc32_from_file(file_path):
    with open(file_path, 'rb') as f:
        file_data = f.read()
        return calculate_crc32(file_data)

# Function to parse the DAT file and extract CRC to game name mappings
def parse_dat_file(dat_file):
    crc_to_name = {}
    tree = ET.parse(dat_file)
    root = tree.getroot()
    for game in root.findall('game'):
        game_name = game.get('name')
        for rom in game.findall('rom'):
            crc = rom.get('crc')
            crc_to_name[crc] = game_name
    return crc_to_name

# Function to extract CRC from a ZIP file
def extract_crc_from_zip(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.file_size > 0 and not file_info.filename.endswith('.txt'):  # Ignore directories, empty files, and text files
                with zip_ref.open(file_info.filename) as file:
                    file_data = file.read()
                    crc = calculate_crc32(file_data)
                    return crc  # Assuming there's only one ROM per ZIP

# Function to extract CRC from a 7z file
def extract_crc_from_7z(sevenz_file):
    with py7zr.SevenZipFile(sevenz_file, mode='r') as archive:
        for name, bio in archive.readall().items():
            bio.seek(0, os.SEEK_END)  # Move the cursor to the end of the file
            size = bio.tell()  # Get the size of the file
            bio.seek(0, os.SEEK_SET)  # Reset the cursor to the beginning of the file
            if size > 0 and not name.endswith('.txt'):  # Ignore directories, empty files, and text files
                file_data = bio.read()
                crc = calculate_crc32(file_data)
                return crc  # Assuming there's only one ROM per 7z

# Path to the script, minus the script
script_path = os.path.dirname(os.path.realpath(__file__))

# Load all DAT files and build CRC to game name mapping. Located in "{path_to_this_script}/dat/romdirname". Load all dat files in the dir. Should be full path.
dat_files = os.listdir(f'dats/{supported_systems[main_system]}/')
for i in range(len(dat_files)):
    dat_files[i] = os.path.join(script_path, f'dats/{supported_systems[main_system]}/{dat_files[i]}')

if len(dat_files) == 0:
    print("No DAT files found for the system.")
    sys.exit()

crc_to_name_mapping = {}
for dat_file in dat_files:
    crc_to_name_mapping.update(parse_dat_file(dat_file))

try:
    config_files = os.listdir(os.path.join(config_dir, supported_emulators[0]))
except Exception as e:
    print(f"Error reading config files (did you run the Bezel Project script?): {e}")
    sys.exit()

missing_crcs = []

# Process each ROM file in the ROMs directory
for rom_filename in os.listdir(sys.argv[1]):
    rom_file_path = os.path.join(sys.argv[1], rom_filename)

    # Skip directories
    if os.path.isdir(rom_file_path):
        continue

    if rom_filename.endswith('.zip'):
        crc = extract_crc_from_zip(rom_file_path)
    elif rom_filename.endswith('.7z'):
        crc = extract_crc_from_7z(rom_file_path)
    elif rom_filename.endswith('.txt') or rom_filename.endswith('.cfg') or rom_filename.endswith('.sav') or rom_filename.endswith('.srm') or rom_filename.endswith('.opt') or rom_filename.endswith('.state') or rom_filename.endswith('.xml') or rom_filename.endswith('.m3u') or rom_filename.endswith('rtc'):
        continue
    else:
        crc = calculate_crc32_from_file(rom_file_path)

    game_name = crc_to_name_mapping.get(crc)
    if game_name:
        # Create the new config filename
        new_config_filename = f'{os.path.splitext(rom_filename)[0]}.cfg'
        old_config_filename = f'{game_name}.cfg'

        # Find the corresponding config file and rename it
        try:
            for emulator in supported_emulators:
                new_config_path = os.path.join(config_dir, emulator, new_config_filename)
                old_config_path = os.path.join(config_dir, emulator, old_config_filename)
                # Check if old_config_path exists
                if not os.path.exists(old_config_path):
                    if not QUIET:
                        print(f'Bezel Project Config not found, skipping ROM: {rom_filename}')
                    break
                if not DRY_RUN:
                    os.rename(old_config_path, new_config_path)
                if DEBUG:
                    print(f'Renamed: {old_config_path} to {new_config_path}')
        except Exception as e:
            if not QUIET:
                print(f'Error renaming config: {e}')
    else:
        if not QUIET:
            print("No CRC found for ROM in DATs: ", rom_filename)
        missing_crcs.append(rom_filename)

if len(missing_crcs) > 0:
    open("missing_crcs_%s.txt" % main_system, "w").write("\n".join(missing_crcs) + "\n")

if not QUIET:
    print("Renaming completed.")

    if len(missing_crcs) > 0:
        print("Missing CRCs written to missing_crcs_%s.txt" % main_system)