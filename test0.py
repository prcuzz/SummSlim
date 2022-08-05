import docker
import requests


def http_requests(docker_client, image_name):
    filters = {'ancestor': image_name}
    docker_list = docker_client.containers.list(filters=filters)
    if docker_list:
        for i in range(len(docker_list[0].ports.values())):
            port = (list(docker_list[0].ports.values())[i])[0]['HostPort']
            # print(port)
            url = "http://localhost:" + port
            try:
                req = requests.get(url)
                print(req.content)
                print("[zzcslim] access port %s with http" % port)
            except:
                print("[zzcslim] can not access port %s with http" % port)
    else:
        print("[error] no %s docker running" % image_name)


docker_client = docker.from_env()
image_name = "phpmyadmin"
http_requests(docker_client, image_name)
