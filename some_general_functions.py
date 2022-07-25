import fnmatch
import os
import subprocess

import docker
import magic


# Determines whether the file exists and gets its absolute path;
# If the file does not exist, return None;
# If it's a non-existent shared library file, try to find another version of it in the same directory.
def get_the_absolute_path(file, image_original_dir_path, PATH_list):
    if not file:
        return None

    file = file.replace("'", "")  # get rid of the single quotes
    file = file.replace("\n", "")  # get rid of the line break

    # Handling shared library files with version differences
    file_path = image_original_dir_path + file
    if "lib" in file and ".so" in file and os.path.exists(file_path) == False:
        if os.path.exists(os.path.dirname(file_path)) == False:
            return None  # If the corresponding folder path does not exist, then return None
        patten = os.path.basename(file_path)
        patten = patten[0:patten.rfind(".so")] + ".so*"  # it should be libxxx*
        files = list(sorted(os.listdir(os.path.dirname(file_path))))  # this is all the files under this dir
        files_with_different_version = fnmatch.filter(files, patten)
        if len(files_with_different_version) != 0:
            return os.path.join(os.path.dirname(file_path), files_with_different_version[0])
        else:
            return None

    if "/" == file[0]:  # If this is already a full path within a container
        file_path = image_original_dir_path + file
        if os.path.exists(file_path) == True:
            return file_path
        else:
            return None
    elif file == ".":
        print("[zzcslim]get_the_absolute_path(): process file '.'")
        return None
    elif ("/" not in file and not PATH_list):
        # This handles the case where there is only a filename and no PATH environment variable
        print("[error]get_the_absolute_path(): process file %s without PATH_list" % file)
        pass
    elif (PATH_list):  # If this is just a file name
        for i in range(len(PATH_list)):
            file_path = image_original_dir_path + PATH_list[i] + "/" + file
            if os.path.exists(file_path) == True:
                return file_path

    return None


# Gets the soft link target of the file
def get_linked_file(file):
    status, output = subprocess.getstatusoutput("file %s" % file)
    if status != 0:
        return None
    elif status == 0 and "symbolic link to" in output:
        return output.split(" ")[-1]


# Determine the file type
def get_file_type(file):
    if file == None or os.path.exists(file) == False:
        return None
    else:
        return magic.from_file(file)


# Gets the soft link target of the file
def get_link_target_file(file_path, image_original_dir_path):
    if file_path == None:
        return None

    if os.path.exists(file_path) == True and os.path.islink(file_path) == True:  # Here's the majority of the cases
        status, output = subprocess.getstatusoutput("file %s" % file_path)
        if status == 0 and "symbolic link" in output:
            target_file = (output.split(" "))[-1]
            if os.path.isabs(target_file):  # some links to /xxx/xxx/xxx
                return image_original_dir_path + target_file
            else:  # some links to xxx
                return os.path.dirname(file_path) + "/" + target_file

    '''    elif "lib" in file_path and ".so" in file_path and not os.path.exists(
            file_path):  # The case of inconsistent shared library version numbers is handled here
        patten = os.path.basename(file_path)
        patten = patten[0:patten.rfind(".so")] + "*"  # it should be libxxx*
        files = list(sorted(os.listdir(os.path.dirname(file_path))))  # this is all the files under this dir
        files_with_different_version = fnmatch.filter(files, patten)
        for i in range(len(files_with_different_version)):
            files_with_different_version[i] = os.path.join(os.path.dirname(file_path), files_with_different_version[i])
        return files_with_different_version'''
    return None


# Copy the folder structure, but leave soft link files
def copy_dir_structure(src, dst):
    if src == None or dst == None:
        print("[error]copy_dir_structure(): src == None or dst == None")
        exit(0)

    src = src + "/*"
    # copy dir structure and file attributes
    status, output = subprocess.getstatusoutput("cp -R --attributes-only %s %s" % (src, dst))
    if status:
        print("[error]copy_dir_structure() fail.")
        print(output)
        exit(0)
    # remove files
    status, output = subprocess.getstatusoutput("find %s -type f -exec rm {} \;" % dst)
    if status:
        print("[error]copy_dir_structure() fail.")
        print(output)
        exit(0)


def generate_dockerfile(image_inspect_info):
    if not image_inspect_info['Id'] or not image_inspect_info['RepoTags'] or not image_inspect_info['Config']['Image']:
        # Check whether image_inspect_info is available
        print("[error]image_inspect_info fault")
        exit(0)

    image_name = image_inspect_info['RepoTags'][0].split(":")[0]
    env = image_inspect_info['Config']['Env']
    entrypoint = image_inspect_info['Config']['Entrypoint']
    cmd = image_inspect_info['Config']['Cmd']
    if image_inspect_info['Config'].get('ExposedPorts'):
        expose = image_inspect_info['Config']['ExposedPorts']
    else:
        expose = None
    workdir = image_inspect_info['Config']['WorkingDir']
    volume = image_inspect_info['Config']['Volumes']

    dockerfile_name = "./image_files/" + image_name.replace("/", "_") + "dockerfile"
    fd = open(dockerfile_name, "w")
    fd.write("FROM scratch\n")
    fd.write("ADD %s.zzcslim.tar.xz /\n" % image_name.replace("/", "_"))
    if env:
        for i in range(len(env)):
            fd.write("ENV %s\n" % env[i])
    if entrypoint:
        fd.write("ENTRYPOINT %s\n" % entrypoint)
    if cmd:
        fd.write("CMD %s\n" % cmd)
    if expose:
        for i in range(len(expose)):
            fd.write("EXPOSE %s\n" % list(expose.keys())[i])
    if workdir:
        fd.write("WORKDIR %s\n" % workdir)
    if volume:
        for i in range(len(volume)):
            fd.write("VOLUME %s\n" % list(volume.keys())[i])

    fd.close()

    return dockerfile_name


if __name__ == "__main__":
    docker_client = docker.from_env()
    docker_apiclient = docker.APIClient(base_url='unix://var/run/docker.sock')

    image_name = "influxdb"

    # try to get inspect info
    docker_inspect_info = docker_apiclient.inspect_image(image_name)
    generate_dockerfile(docker_inspect_info)
