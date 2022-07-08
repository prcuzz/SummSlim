import json
import sys
import docker
import os
import subprocess
import pathlib
import shell_script_dynamic_analysis
import binary_static_analysis
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
current_work_path = os.getcwd()
print("[zzcslim]current_work_path:", current_work_path)

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
os.environ['PATH_list']=json.dumps(PATH_list)

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

image_file_save_path = './image_files/' + image_name.replace('/', '-')
if (os.path.exists(image_file_save_path) == True) and (pathlib.Path(image_file_save_path).is_dir() == True):
    print("[zzcslim]", image_file_save_path, "already exists")
else:
    os.makedirs(image_file_save_path)

status, output = subprocess.getstatusoutput("cp -r -n ./merged/* %s" % image_file_save_path)
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

image_path = os.getcwd() + image_file_save_path[1:]

# analysis shell and binary
for i in range(len(entrypoint)):
    if entrypoint[i][-3:] == ".sh":
        file_list = shell_script_dynamic_analysis.shell_script_dynamic_analysis(image_name, image_path, entrypoint[i],
                                                                                cmd,
                                                                                env)  # The results will be stored in os.environ['slim_images_files'] in serialized form
try:
    main_binary = os.environ['main_binary']
    print("[zzcslim]main_binary:", main_binary)
    if_main_binary_exists, main_binary = some_general_functions.get_the_absolute_path(main_binary, image_name,
                                                                                      PATH_list)
    file_list.append(main_binary)
    print("[zzcslim]main_binary:", main_binary)
    # file_list = json.loads(os.environ['slim_images_files'])  # Get the results of the analysis shell script
    pass  # Get the results of the analysis config file
    file_list = file_list + binary_static_analysis.parse_binary(
        main_binary)  # Get the result of analyzing the binary file
except:
    print("[error]main_binary is empty")

file_list = list(set(file_list))  # Remove duplicate items
pass  # Check if the file exists
print("[zzcslim]file_list:", file_list)

file_list_with_absolute_path = []
for i in range(len(file_list)):  # Find the absolute path of these files
    if_exist, absolute_path = some_general_functions.get_the_absolute_path(file_list[i], image_name, PATH_list=None)
    if if_exist == True:
        file_list_with_absolute_path.append(absolute_path)
print("[zzcslim]file_list_with_absolute_path:", file_list_with_absolute_path)

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

# move files in file_list into new dir
pass
