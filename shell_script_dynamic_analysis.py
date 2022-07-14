import os
from sys import exit
import sys
from requests_html import HTMLSession
import re
import docker
import json

# handle sys.path
for i in range(len(sys.path)):
    if "ptrace" in sys.path[i]:
        del sys.path[i]
        break
sys.path[0], sys.path[-1] = sys.path[-1], sys.path[0]
sys.path.append(os.getcwd() + "/python_ptrace")
from python_ptrace import strace


def shell_script_dynamic_analysis(image_name, image_path, entrypoint, cmd, env):
    # determine docker hub url
    if ("/" in image_name):
        docker_hub_url = "https://hub.docker.com/r/" + image_name
    else:
        docker_hub_url = "https://hub.docker.com/_/" + image_name

    # get html content
    session = HTMLSession()
    try:
        r = session.get(docker_hub_url)
        r.html.render(timeout=256)
    except:
        print("[error]access docker hub or render fail")
        exit(0)

    # Find all docker run examples (not including multiple lines)
    if "docker run " in r.html.full_text:
        re_match = re.findall(r"docker run [^\n]*\n", r.html.full_text)
        print("[zzcslim]find docker run example:", re_match)
    else:
        print("[zzcslim]can not find docker run example")
        # exit(0)

    # get -e arg from html
    # But in some images with just one -e parameter, the container will not start, here you also need to modify
    re_match = re.findall(r"docker run [^\n]* (-e [^\s]+)+ [^\n]*\n", r.html.full_text)
    if re_match:
        #env.append(re_match[0][3:])  # just get one -e here
        print("[zzcslim]env:", env)
    else:
        print("[zzcslim]no -e(env) args")

    # set env and image_path, env must be dictionary
    os.environ['image_path'] = image_path
    env_dict = {}
    for i in range(len(env)):
        env_dict[env[i].split('=')[0]] = env[i].split('=')[1]
    os.environ['imgag_env_serialized'] = json.dumps(env_dict)

    # init the SyscallTracer
    app = strace.SyscallTracer()
    app.options.fork = True
    app.options.trace_exec = True
    app.options.trace_clone = True
    app.program = []
    app.program.append(entrypoint)
    if cmd is not None:
        for i in range(len(cmd)):
            app.program.append(cmd[i])

    # run the dynamic analysis
    app.main()

    return app.file_list


# for debug
if __name__ == "__main__":
    image_name = "redis"
    image_path = "/home/zzc/Desktop/zzc/zzcslim/image_files/" + image_name

    # get docker interface
    docker_client = docker.from_env()
    docker_apiclient = docker.APIClient(base_url='unix://var/run/docker.sock')

    # print basic info
    print("[zzcslim]image_name: ", image_name)
    print("[zzcslim]docker version: ", docker_client.version())
    print("[zzcslim]docker_client.images.list: ", docker_client.images.list())
    current_work_path = os.getcwd()
    print("[zzcslim]current_work_path:", current_work_path)

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

    # try to get the entrypoint
    entrypoint = docker_inspect_info['Config']['Entrypoint'][0]
    if (entrypoint == None):
        print("[error]no Entrypoint")
        exit(0)
    print("[zzcslim]Entrypoint: ", entrypoint)

    # try to get the cmd
    cmd = docker_inspect_info['Config']['Cmd']
    if (cmd == None):
        print("[error]no cmd")
        exit(0)
    print("[zzcslim]cmd: ", cmd)

    # try to get env, PATH and PATH_list
    env = docker_inspect_info['Config']['Env']
    if (env == None):
        print("[error]no Env")
        exit(0)
    print("[zzcslim]env: ", env)
    PATH = env[0][5:]
    print("[zzcslim]PATH: ", PATH)
    PATH_list = PATH.split(':')
    for i in range(len(PATH_list)):
        PATH_list[i] = "./merged" + PATH_list[i]

    file_list = shell_script_dynamic_analysis(image_name, image_path, entrypoint, cmd, env)
    print("[zzcslim]file_list:", file_list)
    print("[zzcslim]main_binary:", os.environ['main_binary'])
