import fnmatch
import os
import subprocess
import tarfile

import docker


def get_the_absolute_path(file, image_original_dir_path, PATH_list):
    """
    Determines whether the file exists and gets its absolute path;
    If the file does not exist, return None;
    If it's a non-existent shared library file, try to find another version of it in the same directory.
    """

    if not file:
        return None

    file = file.replace("'", "")  # get rid of the single quotes
    file = file.replace("\n", "")  # get rid of the line break

    # Handling shared library files with version differences
    file_path = image_original_dir_path + file
    # TODO: Can os.path.exist be changed to os.path.lexist?
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
        if os.path.lexists(file_path) == True:
            return file_path
        else:
            return None
    elif file == ".":
        print("[summslim] get_the_absolute_path(): process file '.'")
        return None
    elif ("/" not in file and not PATH_list):
        # This handles the case where there is only a filename and no PATH environment variable
        print("[error] get_the_absolute_path(): process file %s without PATH_list" % file)
        pass
    elif (PATH_list):  # If this is just a file name
        for i in range(len(PATH_list)):
            file_path = image_original_dir_path + PATH_list[i] + "/" + file
            if os.path.lexists(file_path) == True:
                return file_path

    return None


def find_the_actual_so_file(file_path):
    """
    Some files are linked to xxx.so, but the actual file is something like xxx.so.3
    It is not clear why this is happening, so I had to write this function to handle it first
    """

    if "lib" in file_path and ".so" in file_path and os.path.exists(file_path) == False:
        if os.path.exists(os.path.dirname(file_path)) == False:
            return None  # If the corresponding folder path does not exist, then return None
        patten = os.path.basename(file_path)
        patten = patten[0:patten.rfind(".so")] + ".so*"  # it should be libxxx*
        files = list(sorted(os.listdir(os.path.dirname(file_path))))  # this is all the files under this dir
        files_with_different_version = fnmatch.filter(files, patten)
        if len(files_with_different_version) != 0:
            # TODO: only the 0th is returned here
            return os.path.join(os.path.dirname(file_path), files_with_different_version[0])
        else:
            return None
    else:
        return None


def get_file_type(file):
    """
    Determine the file type
    """

    if not file or os.path.lexists(file) == False:
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


def get_link_target_file(file_path, image_original_dir_path):
    """
    Gets the soft link target of the file
    """

    if file_path == None:
        return None

    if os.path.lexists(file_path) and os.path.islink(file_path):  # Here's the majority of the cases
        status, output = subprocess.getstatusoutput("file %s" % file_path)
        if status == 0 and "symbolic link" in output:
            target_file = (output.split(" "))[-1]
            if os.path.isabs(target_file):  # some links to /xxx/xxx/xxx
                target_file = image_original_dir_path + target_file
            else:  # some links to xxx
                target_file = os.path.dirname(file_path) + "/" + target_file

            if os.path.lexists(target_file):
                return target_file
            else:
                return find_the_actual_so_file(target_file)

    return None


# Copy the folder structure, but leave soft link files
def copy_dir_structure(src, dst):
    if src == None or dst == None:
        print("[error] copy_dir_structure(): src == None or dst == None")
        exit(0)

    src = src + "/*"
    # copy dir structure and file attributes
    status, output = subprocess.getstatusoutput("cp -R --attributes-only %s %s" % (src, dst))
    if status:
        print("[error] copy_dir_structure() fail. output:", output)
        exit(0)
    # remove files
    status, output = subprocess.getstatusoutput("find %s -type f -exec rm {} \;" % dst)
    if status:
        print("[error] copy_dir_structure() fail. output:", output)
        exit(0)


def generate_dockerfile(image_inspect_info):
    """
    生成dockerfile
    """

    # Check whether image_inspect_info is available
    if not image_inspect_info['Id'] or not image_inspect_info['RepoTags']:
        print("[error] generate_dockerfile(): image_inspect_info fault")
        exit(0)

    # Get each variable
    image_name = image_inspect_info['RepoTags'][0].split(":")[0]
    env = image_inspect_info['Config']['Env']
    for i in range(len(env)):
        env[i] = env[i].split("=", 1)  # just divide the first equal sign
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
    if image_inspect_info['Config'].get('User'):
        user = image_inspect_info['Config']['User']
    else:
        user = None

    # Create a dockerfile and write to it
    dockerfile_name = "./image_files/" + image_name.replace("/", "_") + "_dockerfile"
    fd = open(dockerfile_name, "w")
    fd.write("FROM scratch\n")
    fd.write("ADD %s.summslim.tar.xz /\n" % image_name.replace("/", "_"))
    if env:
        for i in range(len(env)):
            fd.write("ENV %s\n" % env[i])
    if entrypoint:
        fd.write("ENTRYPOINT [")
        for each_single_entrypoint in entrypoint:
            if each_single_entrypoint != entrypoint[-1]:
                fd.write("\"%s\", " % each_single_entrypoint)
            else:
                fd.write("\"%s\"" % each_single_entrypoint)
        fd.write("]\n")
    if cmd:
        fd.write("CMD [")
        for each_single_cmd in cmd:
            if each_single_cmd != cmd[-1]:
                fd.write("\"%s\", " % each_single_cmd)
            else:
                fd.write("\"%s\"" % each_single_cmd)
        fd.write("]\n")
    if expose:
        for i in range(len(expose)):
            fd.write("EXPOSE %s\n" % list(expose.keys())[i])
    if workdir:
        fd.write("WORKDIR %s\n" % workdir)
    if volume:
        for i in range(len(volume)):
            fd.write("VOLUME %s\n" % list(volume.keys())[i])
    if user:
        fd.write("USER %s\n" % user)

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
        print("[summslim] image: ", image)
        print("[summslim] find image", image_name)

    return image, image_inspect_info


def analysis_configure_file(file):
    """
    处理配置文件，从中找出带/（可能是文件路径）但不只是单个/的字符串
    :return: list
    """

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
                print("[summslim] analysis_configure_file(): find", aaa[i], "in config file")
        line = fd.readline()

    return file_list


def make_tarxz(output_filename, source_dir):
    """
    一次性打包目录为tar.xz;
    需要确保 source_dir 的最后是个 / ,来指代这个路径下的所有文件而不是这个文件夹
    :param output_filename: 压缩文件名
    :param source_dir: 需要打包的目录
    :return: bool
    """
    source_dir = source_dir.rstrip("/") + "/"
    try:
        with tarfile.open(output_filename, "w:xz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))

        return True
    except Exception as e:
        print(e)
        return False


def simplif_path(path):
    """
    简化路径，将.、..和多余的斜杠都去掉
    :param path: 需要做简化的路径
    """
    stack = []
    for i in path.split('/'):  # 以左斜线分隔
        if i not in ['', '.', '..']:  # 遇到了目录名
            stack.append(i)  # 入栈
        elif i == '..' and stack:  # 返回上一级目录
            stack.pop()  # 出栈
    return "/" + "/".join(stack)  # 连接栈中元素


def looks_for_binaries_depending_on_specified_library(rootdir, lib_file):
    # Looks for binaries in a folder that depend on a specified shared library file
    for root, dirs, files in os.walk(rootdir):
        for dir in dirs:
            # print(os.path.join(root, dir))
            pass
        for file in files:
            # print(os.path.join(root, file))
            exitcode, output = subprocess.getstatusoutput("ldd %s | grep %s" % (os.path.join(root, file), lib_file))
            if not exitcode and output:
                print(os.path.join(root, file))


if __name__ == "__main__":
    # get docker interface
    docker_client = docker.from_env()
    docker_apiclient = docker.APIClient(base_url='unix://var/run/docker.sock')

    # try to get inspect info
    image_name = "odoo"
    image_inspect_info = docker_apiclient.inspect_image(image_name)

    generate_dockerfile(image_inspect_info)
