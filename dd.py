k=1024
m=k*k
cc=b"\x00"
print("\033c\033[40;37m\n")
kk=b""
mm=b""
def retk(c,value):
    a=b""
    a=c*value
    return a
def retm(c,value):
    a=b""
    a=c*value
    return a
kk=retk(cc,k)
mm=retm(kk,k)
f1=open("k.bin","bw")
f1.write(kk)
f1.close()
f1=open("m.bin","bw")
f1.write(mm)
f1.close()


    
