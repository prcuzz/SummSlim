import sys
import os
import re
import magic

image_name = "mongo"
print(os.getcwd() + "/image_files/" + image_name + ".zzcslim")

path = "/home/zzc/Desktop/zzc/zzcslim/image_files/mongo/docker-entrypoint-initdb.d/"
print(os.path.dirname(path.rstrip('/')))