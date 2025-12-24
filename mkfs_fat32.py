import struct
import sys
import math

SECTOR_SIZE = 512
NUM_FATS = 2
RESERVED_SECTORS = 32
MEDIA_DESCRIPTOR = 0xF8
ROOT_CLUSTER = 2

def u16(x): return struct.pack("<H", x)
def u32(x): return struct.pack("<I", x)

def choose_spc(total_sectors):
    for spc in [1,2,4,8,16,32,64,128]:
        clusters = total_sectors // spc
        if clusters >= 65525:
            return spc
    raise RuntimeError("Disco pequeno demais para FAT32")

def calc_fat_sectors(clusters):
    fat_bytes = (clusters + 2) * 4
    return math.ceil(fat_bytes / SECTOR_SIZE)

def mkfs_fat32(filename, size_mb):
    total_bytes = size_mb * 1024 * 1024
    total_sectors = total_bytes // SECTOR_SIZE

    spc = choose_spc(total_sectors)

    data_sectors = total_sectors - RESERVED_SECTORS
    clusters = data_sectors // spc
    fat_sectors = calc_fat_sectors(clusters)

    data_sectors = total_sectors - RESERVED_SECTORS - NUM_FATS * fat_sectors
    clusters = data_sectors // spc
    fat_sectors = calc_fat_sectors(clusters)

    print("FAT32 parameters:")
    print(" Size:", size_mb, "MB")
    print(" Sectors:", total_sectors)
    print(" Sectors/cluster:", spc)
    print(" Clusters:", clusters)
    print(" Sectors/FAT:", fat_sectors)

    with open(filename, "wb+") as f:
        f.seek(total_bytes - 1)
        f.write(b"\x00")

        # ---------------- BOOT SECTOR ----------------
        boot = bytearray(SECTOR_SIZE)
        boot[0:3] = b'\xEB\x58\x90'
        boot[3:11] = b'MKFSF32 '

        boot[11:13] = u16(SECTOR_SIZE)
        boot[13] = spc
        boot[14:16] = u16(RESERVED_SECTORS)
        boot[16] = NUM_FATS
        boot[17:19] = u16(0)
        boot[19:21] = u16(0)
        boot[21] = MEDIA_DESCRIPTOR
        boot[22:24] = u16(0)
        boot[24:26] = u16(63)
        boot[26:28] = u16(255)
        boot[28:32] = u32(0)
        boot[32:36] = u32(total_sectors)

        boot[36:40] = u32(fat_sectors)
        boot[40:42] = u16(0)
        boot[42:44] = u16(0)
        boot[44:48] = u32(ROOT_CLUSTER)
        boot[48:50] = u16(1)
        boot[50:52] = u16(6)

        boot[64] = 0x80
        boot[66] = 0x29
        boot[67:71] = u32(12345678)
        boot[71:82] = b'NO NAME    '
        boot[82:90] = b'FAT32   '

        boot[510:512] = b'\x55\xAA'
        f.seek(0)
        f.write(boot)

        # ---------------- FSINFO ----------------
        fsinfo = bytearray(SECTOR_SIZE)
        fsinfo[0:4] = b'RRaA'
        fsinfo[484:488] = b'rrAa'
        fsinfo[488:492] = u32(0xFFFFFFFF)
        fsinfo[492:496] = u32(0xFFFFFFFF)
        fsinfo[510:512] = b'\x55\xAA'
        f.seek(SECTOR_SIZE)
        f.write(fsinfo)

        # ---------------- FATs ----------------
        fat = bytearray(SECTOR_SIZE)
        fat[0:4] = u32(MEDIA_DESCRIPTOR | 0xFFFFFF00)
        fat[4:8] = u32(0xFFFFFFFF)
        fat[8:12] = u32(0x0FFFFFFF)

        fat_start = RESERVED_SECTORS * SECTOR_SIZE
        f.seek(fat_start)
        f.write(fat)
        f.seek(fat_start + fat_sectors * SECTOR_SIZE)
        f.write(fat)

    print("Imagem FAT32 criada com sucesso.")
print("\033c\033[40;37m\n")
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python mini_mkfs_fat32.py <imagem.img> <tamanho_MB>")
        sys.exit(1)

    mkfs_fat32(sys.argv[1], int(sys.argv[2]))

