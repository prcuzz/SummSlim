import json
import os
import pathlib
import subprocess
import sys

import docker

import binary_static_analysis
import shell_script_dynamic_analysis
import some_general_functions


def print_help():
    print("[zzcslim]usage: python3 zzcslim.py image_name")


# get docker interface
docker_client = docker.from_env()
docker_apiclient = docker.APIClient(base_url='unix://var/run/docker.sock')

# check argv numbers
if (len(sys.argv) != 2):
    print_help()
    exit(0)

# print basic info
print("[zzcslim]argv:", sys.argv)
image_name = sys.argv[1]
print("[zzcslim]image_name:", image_name)
os.environ['image_name'] = image_name
# print("[zzcslim]docker version:", docker_client.version())
# print("[zzcslim]docker_client.images.list:", docker_client.images.list())
print("[zzcslim]current_work_path:", os.getcwd())

# try to get inspect info
docker_inspect_info = docker_apiclient.inspect_image(image_name)

# try to get the image
try:
    image = docker_client.images.get(image_name)
except:
    print("[error]can not find image ", image_name)
    exit(0)
else:
    print("[zzcslim]image: ", image)
    print("[zzcslim]find image", image_name)

# try to get the entrypoint and cmd
entrypoint = docker_inspect_info['Config']['Entrypoint']
if entrypoint:
    print("[zzcslim]Entrypoint:", entrypoint)
cmd = docker_inspect_info['Config']['Cmd']
if cmd:
    print("[zzcslim]cmd:", cmd)
if entrypoint == None and cmd == None:
    print("[error]cmd and entrypoint are both empty")
    exit(0)

# try to get PATH and PATH_list
env = docker_inspect_info['Config']['Env']
if (env == None):
    print("[error]no Env")
    exit(0)
PATH = env[0][5:]
print("[zzcslim]PATH:", PATH)
PATH_list = PATH.split(':')
os.environ['PATH_list'] = json.dumps(PATH_list)

# Determine the original and slim image file paths
image_original_dir_path = os.path.join(os.getcwd(), "image_files", image_name.replace("/", "-"))
os.environ['image_original_dir_path'] = image_original_dir_path
image_slim_dir_path = image_original_dir_path.replace(image_name, image_name + ".zzcslim")

# mount overlay dir and copy files
lowerdir = docker_inspect_info['GraphDriver']['Data']['LowerDir']
upperdir = docker_inspect_info['GraphDriver']['Data']['UpperDir']
if (lowerdir == None):
    print("[error]no lowerdir")
    exit(0)
status, output = subprocess.getstatusoutput(
    "mount -t overlay -o lowerdir=%s overlay ./merged/ " % (lowerdir + ':' + upperdir))
if (status != 0):
    print("[error] mount fails.")
    exit(0)

# create two path
if (os.path.exists(image_original_dir_path) == True) and (pathlib.Path(image_original_dir_path).is_dir() == True):
    print("[zzcslim]", image_original_dir_path, "already exists")
else:
    os.makedirs(image_original_dir_path)

if (os.path.exists(image_slim_dir_path) == True) and (pathlib.Path(image_slim_dir_path).is_dir() == True):
    print("[zzcslim]", image_slim_dir_path, "already exists")
else:
    os.makedirs(image_slim_dir_path)

# copy image original files
status, output = subprocess.getstatusoutput("cp -r -n ./merged/* %s" % image_original_dir_path)
if (status != 0):
    print("[error] cp fails.")
    # umount ./merged/
    status, output = subprocess.getstatusoutput("umount ./merged/")
    if (status != 0):
        print("[error] umount fails.")
    exit(0)

# umount ./merged/
status, output = subprocess.getstatusoutput("umount ./merged/")
if (status != 0):
    print("[error] umount fails.")
    exit(0)

# Initialize some fixed files
file_list = ["/bin/bash", "/bin/dash", "/usr/bin/bash", "/lib64/ld-linux-x86-64.so.2",
             "/usr/lib/x86_64-linux-gnu/ld-2.31.so", "/lib/x86_64-linux-gnu/ld-2.31.so"]
# analysis shell and binary

file_list1, main_binary = shell_script_dynamic_analysis.shell_script_dynamic_analysis(image_name,
                                                                                      image_original_dir_path,
                                                                                      entrypoint,
                                                                                      cmd,
                                                                                      env)  # The results will be stored in os.environ['slim_images_files'] in serialized form
file_list = file_list + file_list1
try:
    print("[zzcslim]main_binary:", main_binary)
    file_list.append(main_binary)
    print("[zzcslim]main_binary:", main_binary)
    # file_list = json.loads(os.environ['slim_images_files'])  # Get the results of the analysis shell script
    pass  # TODO: Get the results of the analysis config file
    main_binary = some_general_functions.get_the_absolute_path(main_binary, image_original_dir_path, PATH_list)
    file_list = file_list + binary_static_analysis.parse_binary(
        main_binary)  # Get the result of analyzing the binary file
except:
    print("[error]main_binary is empty")

file_list = list(set(file_list))  # Remove duplicate items
file_list.remove("/")  # Removing access to the root directory
pass  # Check if the file exists
print("[zzcslim]file_list:", file_list)

# Find the absolute path of these files
file_list_with_absolute_path = []
for i in range(len(file_list)):
    absolute_path = some_general_functions.get_the_absolute_path(file_list[i], image_original_dir_path, PATH_list=None)
    if absolute_path is not None:
        absolute_path = absolute_path.rstrip("/")  # Remove the slash symbol at the end
        file_list_with_absolute_path.append(absolute_path)
    link_target_file = some_general_functions.get_link_target_file(absolute_path,
                                                                   image_original_dir_path)  # If it's a soft link, find the target file
    if link_target_file:
        if type(link_target_file) is str:
            file_list_with_absolute_path.append(link_target_file)
        elif type(link_target_file) is list:
            file_list_with_absolute_path = file_list_with_absolute_path + link_target_file
print("[zzcslim]file_list_with_absolute_path:", file_list_with_absolute_path)

# Copy the folder structure
some_general_functions.copy_dir_structure(image_original_dir_path, image_slim_dir_path)

# copy files in file_list into slim dir
for i in range(len(file_list_with_absolute_path)):
    if not os.path.exists(file_list_with_absolute_path[i]):
        continue

    path_in_slim = file_list_with_absolute_path[i].replace(image_name.replace("/", "-"),
                                                           image_name.replace("/", "-") + ".zzcslim", 1)
    upper_level_path_in_slim = os.path.dirname(path_in_slim)

    status, output = subprocess.getstatusoutput("mkdir -p %s" % upper_level_path_in_slim)
    if status != 0:
        print("[error]mkdir fail. upper_level_path_in_slim: %s" % upper_level_path_in_slim)
        exit(0)

    status, output = subprocess.getstatusoutput("cp -r %s %s" % (file_list_with_absolute_path[i], path_in_slim))
    if status != 0:
        print("[error]cp fail. file_list_with_absolute_path[%s]: %s, path_in_slim: %s; output: %s" % (i,
                                                                                                      file_list_with_absolute_path[
                                                                                                          i],
                                                                                                      path_in_slim,
                                                                                                      output))
        # exit(0)
print("[zzcslim]copy finish")

'''
# init file_list
file_list = []
file_list.append(entrypoint)
# get file path, if not exist, make it ""
file_list[0] = get_file_path_in_merged_dir(file_list[0], PATH_list)
if (not file_list[0]):
    print("[error] entrypoint does not exist")
    exit(0)


# process the items in the file_list in order, copy needed files
i = 0
while (i < len(file_list)):
    # parse binary file
    if (binary.is_ELFfile(file_list[i])):
        new_files = binary.parse_binary(file_list[i], PATH_list)
        for j in range(len(new_files)):
            new_files[j] = get_file_path_in_merged_dir(new_files[j], PATH_list)
            if (new_files[j] not in file_list):
                file_list.append(new_files[j])
    # parse sh file
    elif (sh.is_sh_script_file(file_list[i])):
        new_files = sh.parse_sh(file_list[i], PATH_list)
        for j in range(len(new_files)):
            new_files[j] = get_file_path_in_merged_dir(new_files[j], PATH_list)
            if (new_files[j] not in file_list):
                file_list.append(new_files[j])
    else:
        pass

    i += 1

print("[zzcslim] ", file_list)
'''
