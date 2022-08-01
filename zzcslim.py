import os
import pathlib
import subprocess
import sys

import docker

import binary_static_analysis
import shell_script_dynamic_analysis
import some_general_functions


def print_help():
    print("[zzcslim] usage: python3 zzcslim.py image_name")


def copy_image_original_files(image_original_dir_path):
    # copy image original files
    status, output = subprocess.getstatusoutput("cp -r -n ./merged/* %s" % image_original_dir_path)
    if status != 0:
        print("[error] cp fails.")
        # umount ./merged/
        status, output = subprocess.getstatusoutput("umount ./merged/")
        if status != 0:
            print("[error] umount fails.")
        exit(0)

    # umount ./merged/
    status, output = subprocess.getstatusoutput("umount ./merged/")
    if status != 0:
        print("[error] umount fails.")
        exit(0)


# check argv numbers
if len(sys.argv) != 2:
    print_help()
    exit(0)
image_name = sys.argv[1]
print("[zzcslim] argv:", sys.argv)

# get docker interface
docker_client = docker.from_env()
docker_apiclient = docker.APIClient(base_url='unix://var/run/docker.sock')

# try to get inspect info
image_inspect_info = docker_apiclient.inspect_image(image_name)

# print basic info
print("[zzcslim] image_name:", image_name)
# os.environ['image_name'] = image_name
# print("[zzcslim]docker version:", docker_client.version())
# print("[zzcslim]docker_client.images.list:", docker_client.images.list())
# print("[zzcslim] current_work_path:", os.getcwd())

# try to get the image
try:
    image = docker_client.images.get(image_name)
except:
    print("[error] can not find image ", image_name)
    exit(0)
else:
    print("[zzcslim] image: ", image)
    print("[zzcslim] find image", image_name)

# try to get the entrypoint and cmd
workingdir = image_inspect_info['Config']['WorkingDir']
entrypoint = image_inspect_info['Config']['Entrypoint']
if entrypoint:
    print("[zzcslim] Entrypoint:", entrypoint)
cmd = image_inspect_info['Config']['Cmd']
if cmd:
    print("[zzcslim] cmd:", cmd)
if not entrypoint and not cmd:
    print("[error] cmd and entrypoint are both empty")
    exit(0)

# try to get PATH and PATH_list
env = image_inspect_info['Config']['Env']
if env == None:
    print("[error] no Env")
    exit(0)
PATH = env[0][5:]
print("[zzcslim] PATH:", PATH)
PATH_list = PATH.split(':')
# os.environ['PATH_list'] = json.dumps(PATH_list)

# Determine the original and slim image file paths
# image_original_dir_path = os.path.join(os.getcwd(), "image_files", image_name.replace("/", "-"))
image_original_dir_path = os.path.join(os.getcwd(), "image_files", image_name)
image_slim_dir_path = image_original_dir_path.replace(image_name, image_name + ".zzcslim")

# mount overlay dir and copy files
lowerdir = image_inspect_info['GraphDriver']['Data']['LowerDir']
upperdir = image_inspect_info['GraphDriver']['Data']['UpperDir']
if not lowerdir:
    print("[error] no lowerdir")
    exit(0)
status, output = subprocess.getstatusoutput(
    "mount -t overlay -o lowerdir=%s overlay ./merged/ " % (lowerdir + ':' + upperdir))
if status != 0:
    print("[error] mount fails.")
    exit(0)

# create two path
if (os.path.exists(image_original_dir_path) == True) and (pathlib.Path(image_original_dir_path).is_dir() == True):
    print("[zzcslim]", image_original_dir_path, "already exists")
else:
    os.makedirs(image_original_dir_path)
    copy_image_original_files(image_original_dir_path)

if (os.path.exists(image_slim_dir_path) == True) and (pathlib.Path(image_slim_dir_path).is_dir() == True):
    print("[zzcslim]", image_slim_dir_path, "already exists")
else:
    os.makedirs(image_slim_dir_path)

# Initialize some fixed files
file_list = ["/bin/sh", "/bin/bash", "/usr/bin/bash", "/bin/dash", "/usr/bin/env", "/bin/env", "/bin/chown",
             "/lib64/ld-linux-x86-64.so.2", "/usr/lib/x86_64-linux-gnu/ld-2.31.so", "/lib/x86_64-linux-gnu/ld-2.31.so",
             "/lib/x86_64-linux-gnu/ld-2.28.so", "/lib/x86_64-linux-gnu/ld-2.24.so"]
if workingdir:
    file_list.append(workingdir)

# Get the list of files for the dynamic analysis shell section
file_list1, main_binary = shell_script_dynamic_analysis.shell_script_dynamic_analysis(image_name,
                                                                                      image_original_dir_path,
                                                                                      entrypoint,
                                                                                      cmd,
                                                                                      env)
print("[zzcslim] file list from shell dynamic analysis:", file_list1)
file_list = file_list + file_list1

# Gets the list of files for the static analysis binary section
try:
    print("[zzcslim] main_binary:", main_binary)
    file_list.append(main_binary)
    main_binary = some_general_functions.get_the_absolute_path(main_binary, image_original_dir_path, PATH_list)
    main_binary_file_type = some_general_functions.get_file_type(main_binary)
    if "ELF" in main_binary_file_type:
        # Get the result of analyzing the binary file
        file_list1 = binary_static_analysis.analysis_binary(main_binary)
        print("[zzcslim] file list from binary static analysis:", file_list1)
        file_list = file_list + file_list1
    elif "ASCII text executable" in main_binary_file_type:
        pass  # TODO: The case where the final program is an executable script is handled here
except:
    print("[error] main_binary is empty or can not be analyzed")

file_list = list(set(file_list))  # Remove duplicate items
# Remove the root directory
for i in range(len(file_list)):
    file_list[i] = file_list[i].replace("\n", "")
if "/" in file_list:
    file_list.remove("/")
pass  # Check if the file exists
print("[zzcslim] file_list:", file_list)

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

# Add interpreter files for scripting languages, object files for multiple link files,
# library files for individual binaries
i = 0
while (i < len(file_list_with_absolute_path)):
    file_type = some_general_functions.get_file_type(file_list_with_absolute_path[i])
    if file_type and ("ASCII text executable" in file_type or "script text executable" in file_type):
        fd = open(file_list_with_absolute_path[i], "r")
        line = fd.readline()
        file = line.split()[0]
        file = file.replace("#!", "")
        file = some_general_functions.get_the_absolute_path(file, image_original_dir_path, PATH_list)
        if file and file not in file_list_with_absolute_path:
            file_list_with_absolute_path.append(file)
    elif file_type and "symbolic link to" in file_type:
        file = some_general_functions.get_link_target_file(file_list_with_absolute_path[i], image_original_dir_path)
        if file and file not in file_list_with_absolute_path:
            file_list_with_absolute_path.append(file)
        pass
    elif file_type and "ELF" in file_type:
        file_list1 = binary_static_analysis.analysis_binary(file_list_with_absolute_path[i])
        for j in range(len(file_list1)):
            file = some_general_functions.get_the_absolute_path(file_list1[j], image_original_dir_path,
                                                                PATH_list)
            if file and file not in file_list_with_absolute_path:
                file_list_with_absolute_path.append(file)
    elif file_type and "ASCII text" in file_type and ".conf" in file_list_with_absolute_path[i]:
        file_list1 = some_general_functions.analysis_configure_file(file_list_with_absolute_path[i])
        if file_list1:
            for j in range(len(file_list1)):
                file = some_general_functions.get_the_absolute_path(file_list1[j], image_original_dir_path, PATH_list)
                if file and file not in file_list_with_absolute_path:
                    file_list_with_absolute_path.append(file)

    i = i + 1

# Remove the folder path from the root directory
path_need_to_be_removed = ["/bin", "/etc", "/sbin", "/usr", "/var", "/usr/bin", "/var/lib", "/usr/include", "/usr/sbin",
                           "/usr/local", "/usr/share", "/usr/lib/x86_64-linux-gnu"]
i = 0
while i < len(file_list_with_absolute_path):
    for j in range(len(path_need_to_be_removed)):
        if file_list_with_absolute_path[i] == image_original_dir_path + path_need_to_be_removed[j]:
            file_list_with_absolute_path.remove(file_list_with_absolute_path[i])
            break
    else:
        i = i + 1

file_list_with_absolute_path = list(set(file_list_with_absolute_path))  # Remove duplicate items
print("[zzcslim] file_list_with_absolute_path:", file_list_with_absolute_path)

# Copy the folder structure
some_general_functions.copy_dir_structure(image_original_dir_path, image_slim_dir_path)

# copy files in file_list_with_absolute_path into slim dir
for i in range(len(file_list_with_absolute_path)):
    if not os.path.exists(file_list_with_absolute_path[i]):
        continue

    path_in_slim = file_list_with_absolute_path[i].replace(image_name, image_name + ".zzcslim", 1)
    upper_level_path_in_slim = os.path.dirname(path_in_slim)

    status, output = subprocess.getstatusoutput("mkdir -p %s" % upper_level_path_in_slim)
    if status != 0:
        print("[error] mkdir fail. upper_level_path_in_slim: %s" % upper_level_path_in_slim)
        exit(0)

    status, output = subprocess.getstatusoutput(
        "cp -r %s %s" % (file_list_with_absolute_path[i], upper_level_path_in_slim))
    if status != 0:
        print("[error] cp fail. file_list_with_absolute_path[%s]: %s, path_in_slim: %s; output: %s" % (i,
                                                                                                       file_list_with_absolute_path[
                                                                                                           i],
                                                                                                       path_in_slim,
                                                                                                       output))
        # exit(0)

print("[zzcslim] copy complete")
print("[zzcslim] generate dockerfile %s complete" % some_general_functions.generate_dockerfile(image_inspect_info))
