import os
import re
import signal
import subprocess
import sys
import time
from sys import exit

import docker
from requests_html import HTMLSession

main_procedure = ""

# handle sys.path
for i in range(len(sys.path)):
    if "ptrace" in sys.path[i]:
        del sys.path[i]
        break
sys.path[0], sys.path[-1] = sys.path[-1], sys.path[0]
sys.path.append(os.getcwd() + "/python_ptrace")


def analyse_strace_line(line, entrypoint_and_cmd):
    global main_procedure

    if not entrypoint_and_cmd:
        print("[error]analyse_strace_line()")
        exit(0)

    if ("newfstatat" in line or "execve" in line or "access" in line
        or "openat" in line or "open(" in line or "lstat" in line) \
            and "No such file or directory" not in line:
        if "execve" in line and "execve resumed" not in line and "/runc" not in line and "containerd-shim" not in line:
            main_procedure = line[line.find('"') + 1: line.find('"', line.find('"') + 1)]
        return line[line.find('"') + 1: line.find('"', line.find('"') + 1)]  # Returns the content between double quotes
    return None


def get_docker_run_example(image_name):
    file = "docker_run_example/" + image_name
    if os.path.exists(file):
        fd = open(file, "r")
        example = fd.readline()
        fd.close()
        return example
    else:
        # determine docker hub url
        if ("/" in image_name):
            docker_hub_url = "https://hub.docker.com/r/" + image_name
        else:
            docker_hub_url = "https://hub.docker.com/_/" + image_name

        # get html content
        session = HTMLSession()
        try:
            web_session = session.get(docker_hub_url)
            web_session.html.render(timeout=256)
        except:
            print("[error]access docker hub or render fail")
            exit(0)

        # Find all docker run examples (not including multiple lines)
        env = []
        if "docker run " in web_session.html.full_text:
            re_match_docker_run = re.findall(r"docker run [^\n]*\n",
                                             web_session.html.full_text.replace("\\\n", " ").replace("\t", ""))
            print("[zzcslim]find docker run example:", re_match_docker_run)
            re_match_env = re.findall(r"((-e|--env) [\S]*)",
                                      re_match_docker_run[0])  # Only the first one has been selected here
            if re_match_env:
                for i in range(len(re_match_env)):
                    env.append(re_match_env[i][0].replace("-e ", "").replace("--env ", ""))
                print("[zzcslim]env:", env)
            # TODO: not finished here
            docker_run_example = re_match_docker_run[0].replace("\n", "")
        else:
            print("[zzcslim]can not find docker run example")
            docker_run_example = "docker run --rm " + image_name
        fd = open(file, "w")
        fd.write(docker_run_example)
        fd.close()
        return docker_run_example


def shell_script_dynamic_analysis(image_name, image_path, entrypoint, cmd, env):
    file_list = []
    entrypoint_and_cmd = []
    if entrypoint:
        for i in range(len(entrypoint)):
            entrypoint_and_cmd.append(entrypoint[i])
    if cmd:
        for i in range(len(cmd)):
            entrypoint_and_cmd.append(cmd[i])

    # get containerd pid
    pid = os.popen('ps -ef | grep containerd ').readlines()[0].split()[1]
    print(pid)

    starce_stderr_output_file = open("./starce_stderr_output_file", "w")
    container_output_file = open("./container_output_file", "w")

    # get docker run example
    docker_run_example = get_docker_run_example(image_name)

    # create strace process
    strace_process = subprocess.Popen(["strace", "-f", "-e", "trace=file", "-p", pid], stderr=starce_stderr_output_file)
    # p = subprocess.Popen(["strace", "-f", "-p", pid], stderr=starce_stderr_output_file)

    # create container process, wait, and kill it
    docker_run_example = docker_run_example.split()
    if "--rm" not in docker_run_example:
        docker_run_example.insert(2, "--rm")
    container_process = subprocess.Popen(docker_run_example, stderr=container_output_file)
    time.sleep(15)
    # TODO: This does not kill the container process
    container_process.kill()
    container_output_file.close()

    # kill strace process
    strace_process.kill()
    starce_stderr_output_file.close()

    starce_stderr_output_file = open("./starce_stderr_output_file", "r")
    line = starce_stderr_output_file.readline()
    while line:
        # TODO: Some filters are also needed
        # print(line)
        file = analyse_strace_line(line, entrypoint_and_cmd)
        if file is not None:
            file_list.append(file)
        line = starce_stderr_output_file.readline()

    starce_stderr_output_file.close()

    return file_list, main_procedure


# for debug
if __name__ == "__main__":
    image_name = "httpd"
    image_path = "/home/zzc/Desktop/zzc/zzcslim/image_files/" + image_name

    # get docker interface
    docker_client = docker.from_env()
    docker_apiclient = docker.APIClient(base_url='unix://var/run/docker.sock')

    # print basic info
    print("[zzcslim]image_name: ", image_name)
    # print("[zzcslim]docker version: ", docker_client.version())
    # print("[zzcslim]docker_client.images.list: ", docker_client.images.list())
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
    entrypoint = docker_inspect_info['Config']['Entrypoint']
    cmd = docker_inspect_info['Config']['Cmd']
    if (entrypoint == None) and (cmd == None):
        print("[error]no Entrypoint and cmd")
        exit(0)
    print("[zzcslim]Entrypoint: ", entrypoint)
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
    print("[zzcslim]main_binary:", main_procedure)
