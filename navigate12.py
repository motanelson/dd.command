import struct
import sys
import os

SECTOR_SIZE = 512

def u8(b,o):  return b[o]
def u16(b,o): return struct.unpack_from("<H", b, o)[0]

class FAT12:
    def __init__(self, img):
        self.f = open(img, "rb")
        self.read_bpb()
        self.read_fat()

    def read_bpb(self):
        b = self.f.read(SECTOR_SIZE)
        self.bps = u16(b,11)
        self.spc = u8(b,13)
        self.res = u16(b,14)
        self.fats = u8(b,16)
        self.root_entries = u16(b,17)
        self.spf = u16(b,22)

        self.root_sectors = (self.root_entries*32 + self.bps-1)//self.bps
        self.fat_start = self.res * self.bps
        self.root_start = (self.res + self.fats*self.spf) * self.bps
        self.data_start = self.root_start + self.root_sectors*self.bps

    def read_fat(self):
        self.f.seek(self.fat_start)
        self.fat = self.f.read(self.spf * self.bps)

    def fat12_entry(self, n):
        o = n + n//2
        if n & 1:
            return ((self.fat[o] >> 4) | (self.fat[o+1] << 4)) & 0xFFF
        else:
            return (self.fat[o] | ((self.fat[o+1] & 0x0F) << 8)) & 0xFFF

    def cluster_offset(self, cl):
        return self.data_start + (cl-2)*self.spc*self.bps

    def read_chain(self, cl):
        data = bytearray()
        while cl < 0xFF8:
            self.f.seek(self.cluster_offset(cl))
            data += self.f.read(self.spc*self.bps)
            cl = self.fat12_entry(cl)
        return data

    def read_dir(self, cl=None):
        if cl is None:
            self.f.seek(self.root_start)
            data = self.f.read(self.root_sectors*self.bps)
        else:
            data = self.read_chain(cl)

        entries = []
        for i in range(0,len(data),32):
            e = data[i:i+32]
            if e[0] == 0x00: break
            if e[0] == 0xE5 or e[11] == 0x0F: continue
            name = e[0:8].decode("ascii","ignore").rstrip()
            ext  = e[8:11].decode("ascii","ignore").rstrip()
            fullname = name + ("."+ext if ext else "")
            attr = e[11]
            clus = u16(e,26)
            size = struct.unpack_from("<I",e,28)[0]
            entries.append((fullname,attr,clus,size))
        return entries

# ---------------- SHELL ----------------

def shell(img):
    fs = FAT12(img)
    cwd = None
    path = "/"

    while True:
        cmd = input(f"{path}> ").strip().split()
        if not cmd: continue

        if cmd[0] == "exit":
            break

        if cmd[0] == "dir":
            for n,a,c,s in fs.read_dir(cwd):
                t = "<DIR>" if a & 0x10 else f"{s} bytes"
                print(f"{n:12} {t}")

        elif cmd[0] == "cd":
            if len(cmd)<2: continue
            if cmd[1]=="..":
                cwd=None
                path="/"
                continue
            for n,a,c,s in fs.read_dir(cwd):
                if n.lower()==cmd[1].lower() and a & 0x10:
                    cwd=c
                    path+=n+"/"
                    break

        elif cmd[0] == "type":
            if len(cmd)<2: continue
            for n,a,c,s in fs.read_dir(cwd):
                if n.lower()==cmd[1].lower() and not (a & 0x10):
                    data=fs.read_chain(c)[:s]
                    try:
                        print(data.decode("ascii"))
                    except:
                        print(data)
                    break

        else:
            print("Comandos: dir, cd, type, exit")

if __name__ == "__main__":
    if len(sys.argv)!=2:
        print("Uso: python fat12_shell.py disco.img")
        sys.exit(1)
    shell(sys.argv[1])
