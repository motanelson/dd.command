import struct
import sys
import math

SECTOR_SIZE = 512
NUM_FATS = 2
RESERVED_SECTORS = 1
ROOT_ENTRIES = 512
MEDIA_DESCRIPTOR = 0xF8   # disco removível grande

MIN_FAT16_CLUSTERS = 4085
MAX_FAT16_CLUSTERS = 65524

def write_sector(f, sector, data):
    f.seek(sector * SECTOR_SIZE)
    f.write(data)

def choose_sectors_per_cluster(total_sectors):
    for spc in [1, 2, 4, 8, 16, 32, 64]:
        clusters = total_sectors // spc
        if MIN_FAT16_CLUSTERS <= clusters <= MAX_FAT16_CLUSTERS:
            return spc
    raise RuntimeError("Tamanho inválido para FAT16")

def calc_sectors_per_fat(clusters):
    fat_bytes = (clusters + 2) * 2   # FAT16 = 2 bytes por entrada
    return math.ceil(fat_bytes / SECTOR_SIZE)

def mkfs_fat16(filename, size_mb):
    total_bytes = size_mb * 1024 * 1024
    total_sectors = total_bytes // SECTOR_SIZE

    spc = choose_sectors_per_cluster(total_sectors)
    root_dir_sectors = (ROOT_ENTRIES * 32 + SECTOR_SIZE - 1) // SECTOR_SIZE

    # estimativa inicial
    data_sectors = total_sectors - RESERVED_SECTORS - root_dir_sectors
    clusters = data_sectors // spc
    sectors_per_fat = calc_sectors_per_fat(clusters)

    # recalcular com FATs
    data_sectors = total_sectors - RESERVED_SECTORS - NUM_FATS * sectors_per_fat - root_dir_sectors
    clusters = data_sectors // spc
    sectors_per_fat = calc_sectors_per_fat(clusters)

    print("FAT16 parameters:")
    print(" size:", size_mb, "MB")
    print(" sectors:", total_sectors)
    print(" sectors/cluster:", spc)
    print(" clusters:", clusters)
    print(" sectors/FAT:", sectors_per_fat)

    with open(filename, "wb+") as f:
        f.seek(total_bytes - 1)
        f.write(b"\x00")

        # ---------------- BOOT SECTOR ----------------
        boot = bytearray(SECTOR_SIZE)
        boot[0:3] = b'\xEB\x3C\x90'
        boot[3:11] = b'MKFSF16 '

        struct.pack_into("<H", boot, 11, SECTOR_SIZE)
        boot[13] = spc
        struct.pack_into("<H", boot, 14, RESERVED_SECTORS)
        boot[16] = NUM_FATS
        struct.pack_into("<H", boot, 17, ROOT_ENTRIES)
        struct.pack_into("<H", boot, 19, total_sectors if total_sectors < 65536 else 0)
        boot[21] = MEDIA_DESCRIPTOR
        struct.pack_into("<H", boot, 22, sectors_per_fat)

        struct.pack_into("<H", boot, 24, 63)    # fake geometry
        struct.pack_into("<H", boot, 26, 255)

        boot[510:512] = b'\x55\xAA'
        write_sector(f, 0, boot)

        # ---------------- FATs ----------------
        fat = bytearray(SECTOR_SIZE)
        fat[0] = MEDIA_DESCRIPTOR
        fat[1] = 0xFF
        fat[2] = 0xFF
        fat[3] = 0xFF

        fat_start = RESERVED_SECTORS
        write_sector(f, fat_start, fat)
        write_sector(f, fat_start + sectors_per_fat, fat)

        # ---------------- ROOT DIRECTORY ----------------
        root_start = RESERVED_SECTORS + NUM_FATS * sectors_per_fat
        zero = bytes(SECTOR_SIZE)

        for i in range(root_dir_sectors):
            write_sector(f, root_start + i, zero)

    print("Imagem FAT16 criada com sucesso.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python mini_mkfs_fat16.py <imagem.img> <tamanho_MB>")
        sys.exit(1)

    mkfs_fat16(sys.argv[1], int(sys.argv[2]))
