import fs
import sys


print("\033c\033[40;37m\ngive me a file name image .img")
i=input().strip()


import struct
import sys
import os

SECTOR_SIZE = 512

def u8(b, o):  return b[o]
def u16(b, o): return struct.unpack_from("<H", b, o)[0]

def format_name(entry):
    name = entry[0:8].decode("ascii", errors="ignore").rstrip()
    ext  = entry[8:11].decode("ascii", errors="ignore").rstrip()
    return f"{name}.{ext}" if ext else name

def attr_string(attr):
    flags = []
    if attr & 0x01: flags.append("R")
    if attr & 0x02: flags.append("H")
    if attr & 0x04: flags.append("S")
    if attr & 0x08: flags.append("V")
    if attr & 0x10: flags.append("D")
    if attr & 0x20: flags.append("A")
    return "".join(flags)

def mdir_fat12(img):
    with open(img, "rb") as f:
        boot = f.read(SECTOR_SIZE)

        bytes_per_sector = u16(boot, 11)
        reserved = u16(boot, 14)
        fats = u8(boot, 16)
        root_entries = u16(boot, 17)
        sectors_per_fat = u16(boot, 22)

        root_dir_sectors = (root_entries * 32 + bytes_per_sector - 1) // bytes_per_sector
        root_start_sector = reserved + fats * sectors_per_fat

        f.seek(root_start_sector * bytes_per_sector)
        root = f.read(root_dir_sectors * bytes_per_sector)

    print(f" Directory of {img}\n")

    files = 0
    for i in range(0, len(root), 32):
        entry = root[i:i+32]

        if entry[0] == 0x00:
            break            # fim do diretório
        if entry[0] == 0xE5:
            continue         # apagado
        if entry[11] == 0x0F:
            continue         # LFN (ignorar)

        name = format_name(entry)
        attr = entry[11]
        size = struct.unpack_from("<I", entry, 28)[0]

        print(f"{name:12} {attr_string(attr):6} {size:8} bytes")
        files += 1

    print(f"\n{files} file(s)")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python mdir_fat12.py <imagem.img>")
        sys.exit(1)

    if not os.path.exists(sys.argv[1]):
        print("Erro: ficheiro não existe.")
        sys.exit(1)

    mdir_fat12(sys.argv[1])
