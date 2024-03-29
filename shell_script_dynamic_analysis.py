import os
import re
import subprocess
import sys
import time
from sys import exit

import docker
import requests
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

    # lstat are deleted here
    if "\"" in line and \
            ("newfstatat(" in line or "execve(" in line or "access(" in line or "statx(" in line
            or "openat(" in line or "open(" in line or "stat(" in line or "chdir(" in line) \
            and "No such file or directory" not in line:
        if "execve" in line and "execve resumed" not in line and "/runc" not in line and "containerd-shim" not in line:
            main_procedure = line[line.find('"') + 1: line.find('"', line.find('"') + 1)]
        return line[line.find('"') + 1: line.find('"', line.find('"') + 1)]  # Returns the content between double quotes
    return None


def get_docker_run_example(image_name):
    '''
    This function returns a list, each element of which is a docker run command
    '''
    if image_name[-8:] == ".summslim":
        image_name = image_name[:-8]

    file = "docker_run_example/" + image_name
    dir = os.path.dirname(file)

    if os.path.exists(file):
        with open(file, "r") as fd:
            docker_run_example = fd.readlines()
    else:
        # determine docker hub url
        if ("/" in image_name):
            docker_hub_url = "https://hub.docker.com/r/" + image_name
        else:
            docker_hub_url = "https://hub.docker.com/_/" + image_name

        # get html content
        session = HTMLSession()
        try:
            print("[summslim]", sys._getframe().f_code.co_name, ": visiting url", docker_hub_url)
            web_session = session.get(docker_hub_url)
            web_session.html.render(timeout=256)
        except:
            print("[error]", sys._getframe().f_code.co_name, ": access docker hub or render fail")
            exit(0)

        # Find all docker run examples
        if "docker run " in web_session.html.full_text:
            # TODO: Wrong Extraction in bitnami/mongodb, "docker run command to attach the MongoDB® container to the app-tier network."
            re_match_docker_run = re.findall(r"docker run [^\n]*\n",
                                             web_session.html.full_text.replace("\\\n", " ").replace("\t", ""))
            print("[summslim]", sys._getframe().f_code.co_name, ": find docker run example:", re_match_docker_run)
            docker_run_example = re_match_docker_run
        else:
            print("[summslim]", sys._getframe().f_code.co_name, ": can not find docker run example, use default command")
            docker_run_example = "docker run --rm " + image_name
            docker_run_example = [docker_run_example]

        for i in range(len(docker_run_example)):
            docker_run_example[i] = docker_run_example[i].rstrip("\n") + "\n"

        if not os.path.exists(dir):
            os.makedirs(dir)
        with open(file, "w") as fd:
            fd.writelines(docker_run_example)

    for i in range(len(docker_run_example)):
        docker_run_example[i] = docker_run_example[i].rstrip()

    return docker_run_example


def make_http_requests(docker_client, image_name):
    filters = {'ancestor': image_name}
    docker_list = docker_client.containers.list(filters=filters)
    if docker_list:
        for i in range(len(docker_list[0].ports.values())):
            # Without the -p argument, this would be None
            # TODO: report an error sometime
            port = (list(docker_list[0].ports.values())[i])[0]['HostPort']
            # print(port)
            url = "http://localhost:" + port
            try:
                req = requests.get(url, timeout=5)
                # TODO: need to add a function to find all links to visit next here
                print("[summslim] access port %s with http" % port)
                time.sleep(5)
            except:
                print("[summslim] can not access port %s with http" % port)
    else:
        print("[error] no %s docker running" % image_name)


def get_env_from_docker_run_example(docker_run_example):
    env = []

    docker_run_example = docker_run_example.split()
    if "-e" in docker_run_example:
        for index in [i for i, x in enumerate(docker_run_example) if x == "-e"]:
            env.append(docker_run_example[index + 1])
    if "--env" in docker_run_example:
        for index in [i for i, x in enumerate(docker_run_example) if x == "--env"]:
            env.append(docker_run_example[index + 1])

    return env


def container_run(docker_client, image_name, environment):
    # container_process = subprocess.Popen(docker_run_example, stderr=container_output_file)
    container_process = docker_client.containers.run(image_name, publish_all_ports=True, detach=True,
                                                     environment=environment)

    # wait, get status, and make http request
    time.sleep(80)
    container_process.reload()
    if container_process.status == "running":
        make_http_requests(docker_client, image_name)
        # kill container process
        container_process.stop()
        container_process.remove()


def shell_script_dynamic_analysis(docker_client, image_name, entrypoint, cmd):
    file_list = []
    entrypoint_and_cmd = []
    if entrypoint:
        for i in range(len(entrypoint)):
            entrypoint_and_cmd.append(entrypoint[i])
    if cmd:
        for i in range(len(cmd)):
            entrypoint_and_cmd.append(cmd[i])

    # get containerd pid
    containerd_pid = os.popen('ps -ef | grep containerd ').readlines()[0].split()[1]
    print("[summslim] containerd pid:", containerd_pid)

    starce_stderr_output_file = open("./starce_stderr_output_file", "w")
    container_output_file = open("./container_output_file", "w")

    # get docker run example
    docker_run_example = get_docker_run_example(image_name)

    # create strace process
    strace_process = subprocess.Popen(["strace", "-f", "-p", containerd_pid], stderr=starce_stderr_output_file)
    # strace_process = subprocess.Popen(["strace", "-f", "-p", containerd_pid, "-o", "starce_stderr_output_file"])

    # create container process, run all the commands we can find
    print("[summslim] shell_script_dynamic_analysis() testing default docker run example: docker run -P", image_name)
    container_run(docker_client, image_name, None)
    for single_docker_run_example in docker_run_example:
        print("[summslim] shell_script_dynamic_analysis() testing docker run example:", single_docker_run_example)

        environment = get_env_from_docker_run_example(single_docker_run_example)
        if environment:
            container_run(docker_client, image_name, environment)
        else:
            print("[summslim] no env, skip this example")

    container_output_file.close()

    # kill strace process
    strace_process.kill()
    starce_stderr_output_file.close()

    # Process strace result
    starce_stderr_output_file = open("./starce_stderr_output_file", "r")
    line = starce_stderr_output_file.readline()
    while line:
        # print(line)
        file = analyse_strace_line(line, entrypoint_and_cmd)
        if file is not None:
            file_list.append(file)
        line = starce_stderr_output_file.readline()

    starce_stderr_output_file.close()

    return file_list, main_procedure


# for debug
if __name__ == "__main__":
    image_name = "mysql"
    image_path = "./image_files/" + image_name

    # get docker interface
    docker_client = docker.from_env()
    docker_apiclient = docker.APIClient(base_url='unix://var/run/docker.sock')

    # print basic info
    print("[summslim]image_name: ", image_name)
    current_work_path = os.getcwd()
    print("[summslim]current_work_path:", current_work_path)

    # try to get the image
    try:
        image = docker_client.images.get(image_name)
    except:
        print("[error] can not find image ", image_name)
        exit(0)
    else:
        print("[summslim] image: ", image)
        print("[summslim] find image", image_name)

    # get inspect info
    docker_inspect_info = docker_apiclient.inspect_image(image_name)

    # try to get the entrypoint
    entrypoint = docker_inspect_info['Config']['Entrypoint']
    cmd = docker_inspect_info['Config']['Cmd']
    if (entrypoint == None) and (cmd == None):
        print("[error] no Entrypoint and cmd")
        exit(0)
    print("[summslim] Entrypoint: ", entrypoint)
    print("[summslim] cmd: ", cmd)

    # try to get env, PATH and PATH_list
    env = docker_inspect_info['Config']['Env']
    if (env == None):
        print("[error] no Env")
        exit(0)
    print("[summslim] env: ", env)
    PATH = env[0][5:]
    print("[summslim] PATH: ", PATH)
    PATH_list = PATH.split(':')
    for i in range(len(PATH_list)):
        PATH_list[i] = "./merged" + PATH_list[i]

    file_list = shell_script_dynamic_analysis(docker_client, image_name, entrypoint, cmd)
    print("[summslim] file_list:", file_list)
    print("[summslim] main_binary:", main_procedure)
