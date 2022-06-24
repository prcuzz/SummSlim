import os
from sys import exit
from requests_html import HTMLSession
import re
import docker
import python_ptrace.strace


def shell_script_dynamic_analysis(image_name):
    # determine docker hub url
    if ("/" in image_name):
        docker_hub_url = "https://hub.docker.com/r/" + image_name
    else:
        docker_hub_url = "https://hub.docker.com/_/" + image_name

    # get html content
    session = HTMLSession()
    try:
        r = session.get(docker_hub_url)
    except:
        print("access docker hub fail")
        exit(0)
    r.html.render(timeout=256)

    if "docker run " in r.html.full_text:
        re_match = re.findall(r"docker run [^\n]*\n", r.html.full_text)
        print("[zzcslim]find exec example: ")
        print(re_match)
    else:
        print("do not find exec example")
        exit(0)

    # get -e arg from html
    re_match = re.findall(r"docker run [^\n]* (-e [^\s]+)+ [^\n]*\n", r.html.full_text)
    if re_match:
        env = re_match[0][3:]
        print("[zzcslim]env: " + env)
    else:
        print("[zzcslim]no -e(env) args")

    # python strace.py -f /bin/bash entrypoint cmd
    # python_ptrace.strace.SyscallTracer()

    pass


# for debug
if __name__ == "__main__":
    image_name = "curlimages/curl"
    shell_script_dynamic_analysis(image_name)

'''
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
'''
