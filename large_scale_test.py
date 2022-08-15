import json
import os
import time

import docker
from bs4 import BeautifulSoup
from requests_html import HTMLSession

import zzcslim

TEST_SUCCESS = "success"
TEST_FAIL = "fail"
ORIGINAL_IMAGE_TEST_FAIL = "original image test fail"
ZZCSLIM_IMAGE_TEST_FAIL = "zzcslim image test fail"
ZZCSLIM_FAIL = "zzcslim fail"
ERROR = "error"
DOWNLOAD_TOO_SLOW = "download too slow"

docker_client = docker.from_env()
docker_apiclient = docker.APIClient(base_url='unix://var/run/docker.sock')


def get_image_list_in_current_page(docker_hub_explore_url):
    print("[zzcslim] trying to get the image list in", docker_hub_explore_url)

    session = HTMLSession()
    image_list_in_current_page = []

    try:
        web_session = session.get(docker_hub_explore_url)
        web_session.html.render(timeout=256)
        web_content = web_session.html.html
        # print(web_content)
        soup = BeautifulSoup(web_content, features="html.parser")
        image_item = soup.find_all("div", class_="styles__name___2198b")
        for i in range(len(image_item)):
            image_list_in_current_page.append(image_item[i].contents[0].rstrip())
        print("[zzcslim] image_list_in_current_page:", image_list_in_current_page)
    except Exception as e:
        print("[error] access docker_hub_explore_url or get image_list_in_current_page fail. Exception:", e)
        exit(0)
    return image_list_in_current_page


def test_image(image_name):
    # find this image in docker
    try:
        docker_client.images.get(image_name)
    except docker.errors.ImageNotFound as e:
        print("[error] ImageNotFound. Exception:", e)
        try:
            print("[zzcslim] downloading", image_name)
            # docker_client.images.pull(image_name)
            os.system("docker pull " + image_name)
            docker_client.images.get(image_name)
        except Exception as e:
            print("[error] pull and get image fail. Exception:", e)
            return ": ".join((ERROR, repr(e)))
    except Exception as e:
        print("[error] get image fail. Exception:", e)
        return ": ".join((ERROR, repr(e)))

    # run the image
    try:
        # docker run -d -P xxx
        container = docker_client.containers.run(image_name, detach=True, publish_all_ports=True)
        time.sleep(25)
        container.reload()
    except Exception as e:
        print("[error] run and reload container fail. Exception:", e)
        return ": ".join((ERROR, repr(e)))

    # check if it's running
    if container.status == "running":
        container.stop()
        container.remove()
        return TEST_SUCCESS
    else:
        container.remove()
        print(container.status)
        return TEST_FAIL


def test_original_image(image_name):
    print("[zzcslim] testing original image", image_name)
    return test_image(image_name)


def test_zzcslim_image(image_name):
    print("[zzcslim] testing slimed image", image_name)
    return test_image(image_name + ".zzcslim")


def zzcslim_image(image_name):
    print("[zzcslim] sliming image", image_name)
    return zzcslim.zzcslim(image_name)


if __name__ == "__main__":
    page_num = 5
    docker_hub_explore_url = "https://hub.docker.com/search?q=&image_filter=official%2Cstore&type=image&operating_system=linux&page=" + str(
        page_num)
    large_scale_test_record_file = "large_scale_test_record"

    # Read image_test_record from the file
    if os.path.exists(large_scale_test_record_file):
        with open(large_scale_test_record_file, 'r') as fd:
            image_test_record = json.load(fd)
    else:
        image_test_record = {}

    image_list_in_current_page = get_image_list_in_current_page(docker_hub_explore_url)

    for single_image in image_list_in_current_page:
        if single_image not in image_test_record.keys() or (
                single_image in image_test_record.keys() and "error" in image_test_record[single_image]):
            print("------------------------------ [zzcslim] test", single_image, "------------------------------")
            test_result = test_original_image(single_image)
            if test_result == TEST_FAIL:
                image_test_record[single_image] = ORIGINAL_IMAGE_TEST_FAIL
            elif test_result == TEST_SUCCESS:
                zzcslim_result = zzcslim_image(single_image)
                if zzcslim_result:
                    test_result = test_zzcslim_image(single_image)
                    if test_result == TEST_SUCCESS:
                        image_test_record[single_image] = TEST_SUCCESS
                    elif test_result == TEST_FAIL:
                        image_test_record[single_image] = ZZCSLIM_IMAGE_TEST_FAIL
                    else:
                        image_test_record[single_image] = test_result
                else:
                    image_test_record[single_image] = ZZCSLIM_FAIL
            else:
                image_test_record[single_image] = test_result
        else:
            print("------------------------------ [zzcslim] skip", single_image, "------------------------------")
        with open(large_scale_test_record_file, 'w') as fd:
            (json.dump(image_test_record, fd))

    # Write image_test_record to the file
    with open(large_scale_test_record_file, 'w') as fd:
        (json.dump(image_test_record, fd))

    print("[zzcslim] This test is completed")
