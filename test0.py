import time

import docker

TEST_SUCCESS = "success"
ORIGINAL_IMAGE_TEST_FAIL = "original image test fail"
ZZCSLIM_IMAGE_TEST_FAIL = "zzcslim image test fail"
ERROR = "error"
docker_client = docker.from_env()
docker_apiclient = docker.APIClient(base_url='unix://var/run/docker.sock')


def test_original_image(image_name):
    try:
        docker_client.images.get(image_name)
    except docker.errors.ImageNotFound as e:
        print(e)
        try:
            docker_client.images.pull(image_name)
        except Exception as e:
            print(e)
            return ERROR
        else:
            docker_client.images.get(image_name)
    except Exception as e:
        print(e)
        return ERROR

    try:
        container = docker_client.containers.run(image_name, detach=True, publish_all_ports=True)
        time.sleep(10)
        container.reload()
    except Exception as e:
        print(e)
        return ERROR

    if container.status == "running":
        container.stop()
        container.remove()
        return TEST_SUCCESS
    else:
        container.remove()
        print(container.status)
        return ORIGINAL_IMAGE_TEST_FAIL


print(test_original_image("mysql"))
