import os
import pathlib
import subprocess

import docker

import binary_static_analysis
import shell_script_dynamic_analysis
import some_general_functions


def print_help():
    print("[zzcslim] usage: python3 zzcslim.py image_name")


def copy_image_original_files(image_original_dir_path):
    # copy image original files
    exitcode, output = subprocess.getstatusoutput("cp -r -n -p ./merged/* %s" % image_original_dir_path)
    if exitcode != 0:
        print("[error] cp fails.")
        # umount ./merged/
        exitcode, output = subprocess.getstatusoutput("umount ./merged/")
        if exitcode != 0:
            print("[error] umount fails.")
        return False

    # umount ./merged/
    exitcode, output = subprocess.getstatusoutput("umount ./merged/")
    if exitcode != 0:
        print("[error] umount fails.")
        return False


def zzcslim(image_name):
    # get docker interface
    docker_client = docker.from_env()
    docker_apiclient = docker.APIClient(base_url='unix://var/run/docker.sock')

    # try to get inspect info
    image_inspect_info = docker_apiclient.inspect_image(image_name)

    # print basic info
    print("[zzcslim] image_name:", image_name)
    current_work_path = os.getcwd()
    # os.environ['image_name'] = image_name
    # print("[zzcslim]docker version:", docker_client.version())
    # print("[zzcslim]docker_client.images.list:", docker_client.images.list())

    # try to get the image
    try:
        image = docker_client.images.get(image_name)
    except Exception as e:
        print("[error] can not find image %s. Exception:" % image_name, e)
        return False
    else:
        print("[zzcslim] find image", image)

    # try to get the entrypoint and cmd
    workingdir = image_inspect_info['Config']['WorkingDir']
    entrypoint = image_inspect_info['Config']['Entrypoint']
    if entrypoint:
        print("[zzcslim] Entrypoint:", entrypoint)
    cmd = image_inspect_info['Config']['Cmd']
    if cmd:
        print("[zzcslim] Cmd:", cmd)
    if not entrypoint and not cmd:
        print("[error] cmd and entrypoint are both empty")
        return False

    # try to get PATH and PATH_list
    env = image_inspect_info['Config']['Env']
    if env == None:
        print("[error] no Env")
        return False
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
    workdir = image_inspect_info['GraphDriver']['Data']['WorkDir']
    if not lowerdir or not upperdir or not workdir:
        print("[error] empty lowerdir, upperdir, or workdir")
        return False
    exitcode, output = subprocess.getstatusoutput(
        "mount -t overlay -o lowerdir=%s,upperdir=%s,workdir=%s overlay ./merged/ " % (lowerdir, upperdir, workdir))
    if exitcode != 0:
        print("[error] mount fails.")
        return False

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
                 "/lib64/ld-linux-x86-64.so.2", "/usr/lib/x86_64-linux-gnu/ld-2.31.so",
                 "/lib/x86_64-linux-gnu/ld-2.31.so",
                 "/lib/x86_64-linux-gnu/ld-2.28.so", "/lib/x86_64-linux-gnu/ld-2.24.so",
                 "/lib/x86_64-linux-gnu/libtinfo.so.6", "/lib/x86_64-linux-gnu/libnss_dns.so.2"]

    if workingdir:
        file_list.append(workingdir)

    # Get the list of files for the dynamic analysis shell section
    file_list1, main_binary = shell_script_dynamic_analysis.shell_script_dynamic_analysis(docker_client, image_name,
                                                                                          entrypoint, cmd)
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
    except Exception as e:
        print("[error] main_binary is empty or can not be analyzed. Exception:", e)

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
        absolute_path = some_general_functions.get_the_absolute_path(file_list[i], image_original_dir_path,
                                                                     PATH_list=None)
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
            if "#!" not in line:
                i = i + 1
                continue
            file = line.split()[0]
            file = file.replace("#!", "")
            if not file:  # For example, #! /usr/bin/env python3
                file = line.split()[1]
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
        elif file_type and "ASCII text" in file_type and \
                (".conf" in file_list_with_absolute_path[i] or ".cfg" in file_list_with_absolute_path[i]):
            file_list1 = some_general_functions.analysis_configure_file(file_list_with_absolute_path[i])
            if file_list1:
                for j in range(len(file_list1)):
                    file = some_general_functions.get_the_absolute_path(file_list1[j], image_original_dir_path,
                                                                        PATH_list)
                    if file and file not in file_list_with_absolute_path:
                        file_list_with_absolute_path.append(file)

        i = i + 1

    # Remove the folder path from the root directory
    path_need_to_be_removed = ["/bin", "/etc", "/lib", "/sbin", "/usr", "/var", "/usr/bin", "/usr/sbin", "/var/lib",
                               "/usr/include", "/usr/local", "/usr/share", "/usr/lib", "/usr/lib/x86_64-linux-gnu"]
    i = 0
    while i < len(file_list_with_absolute_path):
        file_list_with_absolute_path[i] = some_general_functions.simplif_path(file_list_with_absolute_path[i])
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
        if not os.path.lexists(file_list_with_absolute_path[i]):
            continue

        path_in_slim = file_list_with_absolute_path[i].replace(image_name, image_name + ".zzcslim", 1)
        upper_level_path_in_slim = os.path.dirname(path_in_slim)

        exitcode, output = subprocess.getstatusoutput("mkdir -p %s" % upper_level_path_in_slim)
        if exitcode != 0:
            print("[error] mkdir fail. upper_level_path_in_slim: %s" % upper_level_path_in_slim)
            return False

        exitcode, output = subprocess.getstatusoutput(
            "cp -r -n %s %s" % (file_list_with_absolute_path[i], upper_level_path_in_slim))
        if exitcode != 0:
            print("[error] cp fail. file_list_with_absolute_path[%s]: %s, path_in_slim: %s; output: %s" %
                  (i, file_list_with_absolute_path[i], path_in_slim, output))
            # return False

    print("[zzcslim] copy complete")
    dockerfile = some_general_functions.generate_dockerfile(image_inspect_info)
    print("[zzcslim] generate dockerfile %s complete" % dockerfile)

    # make tar file
    output_tar_file = os.path.join(current_work_path, "image_files", image_name.replace("/", "_") + ".zzcslim.tar.xz")
    image_slim_dir = os.path.join(current_work_path, "image_files", image_name + ".zzcslim")
    exitcode, output = subprocess.getstatusoutput("chmod -R 777 %s" % image_slim_dir)
    some_general_functions.make_tarxz(output_tar_file, image_slim_dir)
    print("[zzcslim] packing tar file complete")

    # docker build
    # docker_client.images.build() keep raising error here
    build_dir = os.path.join(current_work_path, "image_files", "0_build_dir")
    exitcode, output = subprocess.getstatusoutput("rm -r %s/*" % build_dir)
    if exitcode:
        print("[error] empty build_dir fail.", output)
    exitcode, output = subprocess.getstatusoutput("cp %s %s" % (dockerfile, build_dir))
    if exitcode:
        print("[error] copy dockerfile fail.", output)
    exitcode, output = subprocess.getstatusoutput("cp %s %s" % (output_tar_file, build_dir))
    if exitcode:
        print("[error] copy tar_file fail.", output)
    # build xxx.zzcslim or xxx/xxx.zzcslim
    exitcode, output = subprocess.getstatusoutput(
        "docker build -f %s -t %s %s" % (dockerfile, image_name + ".zzcslim", build_dir))
    if exitcode:
        print("[error] docker build fail.", output)
        return False

    return True


if __name__ == "__main__":
    image_name = "bitnami/solr"
    print("[zzcslim] slim", image_name, zzcslim(image_name))
