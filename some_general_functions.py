import fnmatch
import os
import subprocess

import docker


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


# Determine the file type
def get_file_type(file):
    '''
    if file == None or os.path.exists(file) == False:
        return None
    else:
        return magic.from_file(file)
    '''

    if file == None or os.path.exists(file) == False:
        return None
    else:
        try:
            status, output = subprocess.getstatusoutput("file %s" % file)
            if not status:
                return output
            else:
                return None
        except:
            return None


# Gets the soft link target of the file
def get_link_target_file(file_path, image_original_dir_path):
    if file_path == None:
        return None

    if os.path.exists(file_path) and os.path.islink(file_path):  # Here's the majority of the cases
        status, output = subprocess.getstatusoutput("file %s" % file_path)
        if status == 0 and "symbolic link" in output:
            target_file = (output.split(" "))[-1]
            if os.path.isabs(target_file):  # some links to /xxx/xxx/xxx
                return image_original_dir_path + target_file
            else:  # some links to xxx
                return os.path.dirname(file_path) + "/" + target_file

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
    # Check whether image_inspect_info is available
    if not image_inspect_info['Id'] or not image_inspect_info['RepoTags']:
        print("[error]image_inspect_info fault")
        exit(0)

    # Get each variable
    image_name = image_inspect_info['RepoTags'][0].split(":")[0]
    env = image_inspect_info['Config']['Env']
    for i in range(len(env)):
        env[i] = env[i].split("=")
        env[i][1] = "\"" + env[i][1] + "\""
        env[i] = "=".join(env[i])
        env[i] = repr(env[i])
        env[i] = env[i][1:-1]
    entrypoint = image_inspect_info['Config']['Entrypoint']
    cmd = image_inspect_info['Config']['Cmd']
    if image_inspect_info['Config'].get('ExposedPorts'):
        expose = image_inspect_info['Config']['ExposedPorts']
    else:
        expose = None
    workdir = image_inspect_info['Config']['WorkingDir']
    volume = image_inspect_info['Config']['Volumes']

    # Create a dockerfile and write to it
    dockerfile_name = "./image_files/" + image_name.replace("/", "_") + "_dockerfile"
    fd = open(dockerfile_name, "w")
    fd.write("FROM scratch\n")
    fd.write("ADD %s.zzcslim.tar.xz /\n" % image_name.replace("/", "_"))
    if env:
        for i in range(len(env)):
            fd.write("ENV %s\n" % env[i])
    if entrypoint:
        # I don't know if there will be a problem with simply and roughly replacing single quotes with double quotes here
        entrypoint = str(entrypoint).replace("'", "\"")
        fd.write("ENTRYPOINT %s\n" % entrypoint)
    if cmd:
        cmd = str(cmd).replace("'", "\"")
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


def get_docker_image_interface(image_name):
    # get docker interface
    docker_client = docker.from_env()
    docker_apiclient = docker.APIClient(base_url='unix://var/run/docker.sock')

    # try to get inspect info
    image_inspect_info = docker_apiclient.inspect_image(image_name + ":latest")

    # try to get the image
    try:
        image = docker_client.images.get(image_name)
    except:
        print("[error] can not find image ", image_name)
        exit(0)
    else:
        print("[zzcslim] image: ", image)
        print("[zzcslim] find image", image_name)

    return image, image_inspect_info


def analysis_configure_file(file):
    file_list = []

    if not os.path.exists(file):
        return None

    fd = open(file)
    line = fd.readline()
    while (line):
        aaa = line.split()
        for i in range(len(aaa)):
            if "/" == aaa[i][0] and "/" is not aaa[i]:
                file_list.append(aaa[i].rstrip(";"))
                print(aaa[i])
        line = fd.readline()

    return file_list


if __name__ == "__main__":
    image_name = "haproxytech/haproxy-alpine"
    image, image_inspect_info = get_docker_image_interface(image_name)
    generate_dockerfile(image_inspect_info)

    exitcode, output = subprocess.getstatusoutput("echo $(pwd)")
    print(output)