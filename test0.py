import os
import subprocess

rootdir = '/home/zzc/Desktop/zzc/zzcslim/image_files/phpmyadmin'
#Looks for binaries in a folder that depend on a specified shared library file
for root, dirs, files in os.walk(rootdir):
    for dir in dirs:
        # print(os.path.join(root, dir))
        pass
    for file in files:
        # print(os.path.join(root, file))
        exitcode, output = subprocess.getstatusoutput("ldd %s | grep libnss" % os.path.join(root, file))
        if not exitcode and output:
            print(os.path.join(root, file))
