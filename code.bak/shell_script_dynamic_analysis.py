import os
from sys import exit

import docker
import python_ptrace.strace


def shell_script_dynamic_analysis(merged_path, entrypoint, cmd):
    # python strace.py -f /bin/bash entrypoint cmd
    python_ptrace.strace.SyscallTracer()

    pass

# for debug
if __name__ == "__main__":
    image_name = "registry"

    # get docker interface
    docker_client = docker.from_env()
    docker_apiclient = docker.APIClient(base_url='unix://var/run/docker.sock')

    # print basic info
    print("[zzcslim]image_name: ", image_name)
    print("[zzcslim]docker version: ", docker_client.version())
    print("[zzcslim]docker_client.images.list: ", docker_client.images.list())
    current_work_path = os.getcwd()
    print("[zzcslim] current_work_path: ", current_work_path)

    # try to get the image
    try:
        image = docker_client.images.get(image_name)
    except:
        print("[error]can not find image ", image_name)
        exit(0)
    else:
        print("[zzcslim]image: ", image)
        print("[zzcslim]find image", image_name)

    # get inspect info
    docker_inspect_info = docker_apiclient.inspect_image(image_name)

    # try to get entrypoint
    entrypoint = docker_inspect_info['Config']['Entrypoint'][0]
    if (entrypoint == None):
        print("[error]no Entrypoint")
        exit(0)
    print("Entrypoint: ", entrypoint)

    # try to get cmd
    cmd = docker_inspect_info['Config']['Entrypoint'][0]
    if (cmd == None):
        print("[error]no cmd")
        exit(0)
    print("cmd: ", cmd)

    # try to get PATH and PATH_list
    Env = docker_inspect_info['Config']['Env']
    if (Env == None):
        print("[error]no Env")
        exit(0)
    PATH = Env[0][5:]
    print("PATH: ", PATH)
    PATH_list = PATH.split(':')
    for i in range(len(PATH_list)):
        PATH_list[i] = "./merged" + PATH_list[i]
