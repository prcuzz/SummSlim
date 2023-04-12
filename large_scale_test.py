import json
import os
import time

import docker
from bs4 import BeautifulSoup
from requests_html import HTMLSession

import shell_script_dynamic_analysis
import summslim

TEST_SUCCESS = "success"
TEST_FAIL = "fail"
ORIGINAL_IMAGE_TEST_FAIL = "original image test fail"
summslim_IMAGE_TEST_FAIL = "summslim image test fail"
summslim_FAIL = "summslim fail"
ERROR = "error"
DOWNLOAD_TOO_SLOW = "download too slow"

docker_client = docker.from_env()
docker_apiclient = docker.APIClient(base_url='unix://var/run/docker.sock')


def get_image_list_in_current_page(docker_hub_explore_url):
    """
    get a image name list from the given url
    :param docker_hub_explore_url: the given url
    :return: list
    """

    print("[summslim] trying to get the image list in", docker_hub_explore_url)

    session = HTMLSession()
    image_list_in_current_page = []

    try:
        web_session = session.get(docker_hub_explore_url)
        web_session.html.render(timeout=256)
        web_content = web_session.html.html
        soup = BeautifulSoup(web_content, features="html.parser")
        image_item = soup.find_all("div", class_="styles__name___2198b")
        for i in range(len(image_item)):
            image_list_in_current_page.append(image_item[i].contents[0].rstrip())
        print("[summslim] image_list_in_current_page:", image_list_in_current_page)
    except Exception as e:
        print("[error] access docker_hub_explore_url or get image_list_in_current_page fail. Exception:", e)
        exit(0)
    return image_list_in_current_page


def test_image(image_name):
    """
    Test if the given image can be run with the sample command.
    :param: image_name: the image need to be tested
    """

    docker_run_example = shell_script_dynamic_analysis.get_docker_run_example(image_name)

    # find this image in docker
    try:
        docker_client.images.get(image_name)
    except docker.errors.ImageNotFound as e:
        print("[error] ImageNotFound. Exception:", e)
        try:
            print("[summslim] downloading", image_name)
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
    for single_docker_run_example in docker_run_example:
        environment = shell_script_dynamic_analysis.get_env_from_docker_run_example(single_docker_run_example)

        try:
            # container_process = subprocess.Popen(docker_run_example, stderr=container_output_file)
            container_process = docker_client.containers.run(image_name, publish_all_ports=True,
                                                             detach=True, environment=environment)

            # wait, get status, and make http request
            time.sleep(30)
            container_process.reload()
        except Exception as e:
            print("[error] run and reload container fail. Exception:", e)
            return ": ".join((ERROR, repr(e)))
        if container_process.status == "running":
            # kill container process
            container_process.stop()
            container_process.remove()
            return TEST_SUCCESS
        else:
            container_process.stop()
            container_process.remove()

    return TEST_FAIL


def test_original_image(image_name):
    print("[summslim] testing original image", image_name)
    return test_image(image_name)


def test_summslim_image(image_name):
    print("[summslim] testing slimed image", image_name)
    return test_image(image_name + ".summslim")


def summslim_image(image_name):
    print("[summslim] sliming image", image_name)
    try:
        result = summslim.summslim(image_name)
    except Exception as e:
        print("[error]", repr(e))
        return ": ".join((summslim_FAIL, repr(e)))
    else:
        return result


if __name__ == "__main__":
    '''
    page_num = 14
    docker_hub_explore_url = "https://hub.docker.com/search?q=&image_filter=official%2Cstore&type=image&operating_system=linux&page=" + str(
        page_num)

    image_list_in_current_page = get_image_list_in_current_page(docker_hub_explore_url)
    '''

    # This list is captured directly with a crawler, so I don't have to go to dockerhub to get it every time
    image_list = ['linuxserver/cloud9', 'envoyproxy/envoy-alpine', 'crossplane/provider-gcp',
     'linuxserver/clarkson', 'openebs/rawfile-localpv', 'itisfoundation/puppeteer', 'databack/mysql-backup',
     'jhipster/jhipster-alerter', 'jhipster/jhipster-import-dashboards', 'jenkins4eval/jnlp-agent-maven',
     'jupyterhub/configurable-http-proxy', 'osrf/ubuntu_armhf', 'linuxserver/synclounge', 'crossplane/provider-alibaba',
     'envoyproxy/envoy', 'fluxcd/flux-recv', 'fluent/fluentd', 'staphb/kraken2', 'fluxcd/image-reflector-controller',
     'droidwiki/concourse-ssh-resource', 'stackstorm/st2api', 'drud/ddev-webserver', 'linuxserver/duckdns',
     'webdevops/php-nginx-dev', 'vitess/vtctl', 'linuxserver/minetest', 'homeassistant/armv7-hassio-supervisor',
     'linuxserver/cardigann', 'openebs/snapshot-controller', 'staphb/pangolin', 'linuxserver/taisun',
     'linuxserver/freshrss', 'itisfoundation/rabbitmq', 'moby/buildkit', 'linuxserver/gazee',
     'apache/cassandra-testing-ubuntu2004-java11-w-dependencies', 'linuxserver/dokuwiki', 'linuxserver/pydio',
     'apache/nifi', 'photoprism/photoprism', 'stackstorm/st2actionrunner', 'linuxserver/syncthing',
     'openstax/chromedriver-version-resource', 'dockage/tor-privoxy', 'layer5/meshery-consul',
     'sitespeedio/sitespeed.io', 'linuxserver/calibre-web', 'linuxserver/hydra', 'coredns/coredns',
     'edirom/vife-meigarage-webclient', 'edirom/measure-editor', 'linuxserver/mstream', 'purplei2p/i2pd',
     'owasp/zap2docker-weekly', 'linuxserver/openssh-server', 'alpinelinux/gitlab-runner-helper', 'webdevops/php-nginx',
     'homeassistant/raspberrypi2-homeassistant', 'openebs/snapshot-provisioner', 'linuxserver/apache', 'mgibio/cle',
     'linuxserver/jackett', 'linuxserver/grocy', 'openebs/jiva', 'gluufederation/oxtrust', 'opendronemap/nodeodm',
     'jhipster/jhipster-console', 'nextstrain/nextclade', 'homeassistant/armhf-hassio-dns',
     'homeassistant/aarch64-addon-mosquitto', 'apache/skywalking-oap-server', 'antrea/antrea-ubuntu',
     'jupyter/tensorflow-notebook', 'linuxserver/libresonic', 'homeassistant/amd64-hassio-observer',
     'linuxserver/sabnzbd', 'linuxserver/librespeed', 'lancachenet/lancache-dns', 'apache/apisix-dashboard',
     'ensemblorg/ensembl-vep', 'linuxserver/openvpn-as', 'linuxserver/organizr', 'homeassistant/amd64-hassio-dns',
     'apache/flink', 'linuxserver/domoticz', 'tezos/tezos-bare', 'bitwardenrs/server-postgresql', 'linuxkit/kernel',
     'jenkins/slave', 'opendatacube/datacube-alchemist', 'cm2network/csgo',
     'apache/cassandra-testing-ubuntu2004-java11', 'pactfoundation/pact-cli', 'opendatacube/explorer',
     'edirom/project.zenmem.de', 'openpolicyagent/kube-mgmt', 'vitess/vtctld', 'linuxserver/diskover',
     'authelia/authelia', 'homeassistant/qemux86-64-homeassistant', 'homeassistant/amd64-addon-samba',
     'homeassistant/amd64-hassio-multicast', 'wurmlab/sequenceserver', 'edirom/vife-website', 'openstax/prowler',
     'linuxserver/nzbget', 'clearlinux/iperf', 'layer5/meshery-cpx', 'linuxkit/metadata', 'layer5/meshery',
     'apache/beam_java11_sdk', 'openebs/node-disk-operator', 'linuxserver/resilio-sync', 'linuxserver/mysql',
     'homeassistant/armv7-addon-mosquitto', 'jupyterhub/singleuser', 'stackstorm/st2garbagecollector',
     'lancachenet/sniproxy', 'openpolicyagent/opa', 'itisfoundation/director', 'linuxserver/nano',
     'linuxserver/snapdrop', 'homeassistant/aarch64-addon-ssh', 'elyra/kernel-spark-r', 'linuxserver/rdesktop',
     'fluxcd/flux-prerelease', 'fluxcd/image-automation-controller', 'jupyter/base-notebook',
     'pipelinecomponents/ansible-lint', 'openstax/output-producer-resource', 'linuxserver/nginx', 'linuxserver/boinc',
     'apache/couchdb', 'jupyter/nbviewer', 'linuxserver/mcmyadmin2', 'photoprism/photoprism-arm64',
     'linuxserver/bazarr', 'lycheeorg/lychee', 'homeassistant/armv7-hassio-audio',
     'openstax/concourse-resource-github-milestone', 'fluent/fluent-bit', 'apache/fineract',
     'opendronemap/webodm_webapp', 'edirom/measure-detector', 'openebs/zfs-driver', 'litmuschaos/chaos-operator',
     'openebs/admission-server', 'linuxserver/embystat', 'edirom/music-diff', 'linuxserver/unifi',
     'jenkinsciinfra/inbound-agent-ruby', 'linuxkit/mkimage-iso-bios', 'secoresearch/apache-varnish',
     'linuxserver/duplicati', 'apache/superset', 'curlimages/curl', 'jhipster/jdl-studio',
     'litmuschaos/litmusportal-event-tracker', 'homeassistant/amd64-addon-ssh', 'kindest/kindnetd',
     'blackflysolutions/dovecot', 'homeassistant/armv7-hassio-observer', 'ocaml/opam2', 'kope/kops-controller',
     'linuxserver/plexpy', 'jupyterhub/jupyterhub', 'linuxserver/davos', 'linuxserver/homeassistant',
     'itisfoundation/api-server', 'distribution/registry', 'jupyter/all-spark-notebook',
     'homeassistant/aarch64-hassio-cli', 'linuxserver/transmission', 'webdevops/php-apache', 'fluxcd/helm-operator',
     'linuxserver/calibre', 'jupyter/datascience-notebook', 'linuxserver/smokeping', 'opendatacube/wps',
     'jupyter/pyspark-notebook', 'homeassistant/raspberrypi4-64-homeassistant', 'linuxserver/projectsend',
     'crossplane/provider-aws-controller', 'layer5/meshery-nsm', 'linuxserver/prowlarr', 'linuxserver/lidarr',
     'biocontainers/bcftools', 'homeassistant/raspberrypi4-homeassistant', 'linuxserver/unifi-controller',
     'opendatacube/wms', 'envoyproxy/envoy-alpine-debug', 'jupyterhub/k8s-singleuser-sample',
     'stackstorm/st2sensorcontainer', 'kindest/base', 'openebs/m-apiserver', 'homeassistant/amd64-addon-mosquitto',
     'openebs/m-exporter', 'edirom/odd-api', 'sonobuoy/systemd-logs', 'linuxserver/sickgear', 'apache/tika',
     'openstax/concourse-resource-rex-release', 'linuxserver/ffmpeg', 'fluxcd/source-controller',
     'droidwiki/mediawiki-version-resource', 'openebs/openebs-k8s-provisioner', 'elyra/kernel-tf-py',
     'litmuschaos/litmusportal-subscriber', 'linuxserver/snipe-it', 'owasp/zap2docker-stable', 'linuxkit/containerd',
     'jhipster/jhipster-logstash', 'linuxserver/ldap-auth', 'homeassistant/raspberrypi3-64-homeassistant',
     'linuxserver/musicbrainz', 'linuxkit/ca-certificates', 'clearlinux/os-core', 'jenkins/jnlp-slave',
     'drud/ddev-ssh-agent', 'drud/ddev-router', 'kope/protokube', 'homeassistant/aarch64-hassio-supervisor',
     'rclone/rclone', 'openebs/provisioner-localpv', 'openpolicyagent/gatekeeper',
     'homeassistant/aarch64-homeassistant', 'staphb/vadr', 'stackstorm/stackstorm', 'openebs/linux-utils',
     'owasp/dependency-check', 'kope/dns-controller', 'pipelinecomponents/shellcheck',
     'homeassistant/raspberrypi-homeassistant', 'clearlinux/redis', 'kubernetes/pause', 'jenkins/jnlp-agent-docker',
     'openstax/cnx-recipes-output', 'homeassistant/raspberrypi3-homeassistant', 'linuxserver/hydra2',
     'itisfoundation/dask-sidecar', 'fluxcd/kustomize-controller', 'vitess/base', 'jenkins/jenkins',
     'linuxserver/wikijs', 'edirom/zenmem.de', 'linuxserver/lychee', 'crossplane/provider-helm',
     'fluxcd/helm-controller', 'edirom/ehinman', 'linuxserver/ubooquity', 'verdaccio/verdaccio', 'composer/satis',
     'elyra/kernel-tf-gpu-py', 'linuxkit/mkimage-iso-efi', 'staphb/samtools', 'openstax/cnx-automation',
     'opendatacube/datacube-index', 'stackstorm/st2scheduler', 'linuxserver/sickchill',
     'opendatacube/datacube-statistician', 'staphb/ivar', 'linuxserver/netbootxyz', 'webdevops/php-apache-dev',
     'linuxserver/muximux', 'itisfoundation/webserver', 'domoticz/domoticz', 'homeassistant/armhf-homeassistant',
     'openstax/concourse-stub-resource', 'envoyproxy/envoy-build-ubuntu', 'linuxserver/tautulli', 'linuxkit/sysctl',
     'jenkins/ssh-slave', 'dockage/phppgadmin', 'envoyproxy/ratelimit', 'homeassistant/amd64-addon-configurator',
     'elyra/kernel-r', 'tezos/tezos', 'vitess/vtgate', 'crossplane/crossplane', 'linuxserver/booksonic-air',
     'apache/zeppelin', 'jenkins/inbound-agent', 'homeassistant/qemuarm-64-homeassistant', 'machines/filestash',
     'linuxserver/letsencrypt', 'linuxkit/go-compile', 'vitess/guestbook', 'linuxserver/emby', 'docksal/cli',
     'linuxserver/booksonic', 'linuxserver/heimdall', 'drud/watchtower', 'layer5/meshery-kuma',
     'webdevops/azure-devops-exporter', 'stanfordoval/almond-server', 'linuxserver/nextcloud', 'linuxkit/init',
     'linuxserver/papermerge', 'crossplane/provider-sql', 'linuxserver/swag', 'linuxserver/remmina',
     'homeassistant/armv7-hassio-multicast', 'sitespeedio/graphite', 'apache/druid', 'linuxserver/bookstack',
     'layer5/meshery-istio', 'linuxserver/mysql-workbench', 'linuxserver/airsonic', 'homeassistant/amd64-addon-mariadb',
     'itisfoundation/catalog', 'linuxserver/lazylibrarian', 'itisfoundation/storage', 'nfcore/sarek', 'sopelirc/sopel',
     'linuxserver/headphones', 'linuxserver/couchpotato', 'linuxserver/kodi-headless', 'stackstorm/st2timersengine',
     'stackstorm/st2auth', 'openwhisk/controller', 'linuxserver/plex', 'openwhisk/action-nodejs-v10',
     'elyra/kernel-scala', 'lancachenet/monolithic', 'linuxserver/radarr', 'linuxserver/qbittorrent',
     'linuxserver/wireshark', 'clearlinux/python', 'fortio/fortio', 'sqlpad/sqlpad', 'linuxserver/medusa',
     'openpolicyagent/conftest', 'stackstorm/st2web', 'homeassistant/armv7-hassio-dns', 'linuxserver/deluge',
     'linuxserver/codimd', 'homeassistant/armhf-hassio-supervisor', 'linuxserver/ddclient', 'linuxserver/habridge',
     'linuxserver/rutorrent', 'litmuschaos/go-runner', 'openstax/concourse-resource-github-issue', 'gromacs/gromacs',
     'bitwardenrs/server-mysql', 'openwhisk/nodejs6action', 'linuxserver/wireguard', 'jhipster/jhipster-registry',
     'stackstorm/st2workflowengine', 'linuxserver/sickrage', 'linuxserver/mylar3', 'linuxserver/photoshow',
     'shokoanime/server', 'linuxserver/tvheadend', 'linuxserver/minisatip', 'kalilinux/kali-rolling',
     'bitwardenrs/server', 'dockage/mailcatcher', 'openebs/cstor-csi-driver', 'linuxserver/cops',
     'pipelinecomponents/markdownlint', 'openstax/concourse-history-txt-resource', 'fluxcd/flux', 'litmuschaos/mongo',
     'homeassistant/armv7-hassio-cli', 'stackstorm/st2stream', 'apache/apisix', 'fluent/fluentd-kubernetes-daemonset',
     'linuxserver/quassel-core', 'pravega/zookeeper', 'linuxkit/runc', 'homeassistant/aarch64-hassio-dns',
     'linuxserver/thelounge', 'linuxkit/binfmt', 'homeassistant/aarch64-addon-configurator', 'testcontainers/ryuk',
     'jupyter/r-notebook', 'fluxcd/helm-operator-prerelease', 'itisfoundation/apihub', 'jenkins/jnlp-agent-maven',
     'fluxcd/notification-controller', 'litmuschaos/upgrade-agent-cp', 'linuxserver/oscam', 'openebs/node-disk-manager',
     'linuxserver/sickbeard', 'envoyproxy/envoy-alpine-dev', 'testcontainers/sshd', 'cbioportal/session-service',
     'webdevops/php', 'linuxserver/webtop', 'itisfoundation/static-webserver', 'homeassistant/armhf-hassio-audio',
     'jhipster/jhipster', 'linuxserver/beets', 'homeassistant/amd64-hassio-audio', 'apache/airflow',
     'linuxserver/healthchecks', 'linuxserver/guacd', 'corpusops/node', 'jupyterhub/k8s-hub', 'linuxserver/piwigo',
     'jenkins/jnlp-agent-ruby', 'jupyter/minimal-notebook', 'linuxserver/pwndrop', 'linuxserver/daapd',
     'homeassistant/home-assistant', 'mgibio/samtools-cwl', 'owasp/modsecurity-crs', 'kope/confluentschemaregistry',
     'linuxserver/readarr', 'crossplane/provider-azure', 'itisfoundation/director-v2', 'linuxserver/doublecommander',
     'homeassistant/amd64-addon-duckdns', 'openebs/cstor-volume-mgmt', 'homeassistant/aarch64-hassio-audio',
     'linuxserver/codiad', 'linuxserver/jellyfin', 'freshrss/freshrss', 'homeassistant/aarch64-hassio-observer',
     'openwhisk/dockerskeleton', 'osrf/ros', 'jenkins/ssh-agent', 'linuxserver/ombi', 'pipelinecomponents/yamllint',
     'homeassistant/amd64-hassio-supervisor', 'apache/arrow-dev', 'sonobuoy/sonobuoy', 'webdevops/apache',
     'linuxserver/sonarr', 'homeassistant/armv7-addon-ssh', 'linuxserver/scrutiny', 'homeassistant/ci-azure',
     'pactfoundation/pact-broker', 'linuxserver/mylar', 'gluufederation/oxauth', 'jenkins/agent',
     'jenkinsciinfra/inbound-agent-node', 'litmuschaos/litmusportal-auth-server', 'linuxserver/nzbhydra2',
     'edirom/meigarage', 'linuxserver/overseerr', 'osrf/ubuntu_arm64', 'jhipster/jhipster-elasticsearch',
     'staphb/fastqc', 'jenkinsciinfra/inbound-agent-maven', 'vitess/lite', 'homeassistant/armv7-addon-configurator',
     'linuxserver/raneto', 'linuxserver/htpcmanager', 'projectcontour/contour', 'gluufederation/cr-rotate',
     'linuxserver/dillinger', 'ocaml/opam2-staging', 'tacc/slapd', 'itisfoundation/sidecar', 'owasp/dependency-track',
     'homeassistant/aarch64-hassio-multicast', 'cwrc/cwrc-validator', 'stackstorm/st2notifier', 'openwhisk/invoker',
     'apache/skywalking-base', 'jupyterhub/k8s-network-tools', 'webdevops/pagerduty-exporter',
     'apache/dolphinscheduler', 'opendatacube/ows', 'crossplane/provider-aws', 'openebs/cstor-istgt',
     'edirom/ess-website', 'stackstorm/st2rulesengine', 'geopython/geohealthcheck', 'openebs/cstor-pool-mgmt',
     'itisfoundation/migration', 'layer5/meshery-linkerd', 'homeassistant/amd64-hassio-cli',
     'homeassistant/intel-nuc-homeassistant', 'apache/nifi-registry', 'kindest/node', 'jupyter/scipy-notebook',
     'envoyproxy/envoy-dev', 'openstax/concourse-resource-git', 'treehouses/couchdb', 'linuxserver/kanzi',
     'nlnetlabs/routinator', 'linuxserver/mariadb', 'litmuschaos/litmusportal-server', 'layer5/meshery-osm',
     'linuxserver/foldingathome', 'pipelinecomponents/jsonlint', 'mautic/mautic', 'openebs/cstor-pool',
     'linuxserver/pyload', 'linuxserver/code-server', 'linuxserver/znc', 'jhipster/jhipster-curator',
     'itisfoundation/datcore-adapter', 'webdevops/azure-metrics-exporter', 'linuxkit/rngd', 'silintl/ecs-deploy',
     'projectcontour/contour-operator']

    large_scale_test_record_file = "large_scale_test_record"

    # Read image_test_record from the file
    if os.path.exists(large_scale_test_record_file):
        with open(large_scale_test_record_file, 'r') as fd:
            image_test_record = json.load(fd)
    else:
        image_test_record = {}

    for single_image in image_list:
        if single_image not in image_test_record.keys() or (
                single_image in image_test_record.keys() and "error" in image_test_record[single_image]) or (
                single_image in image_test_record.keys() and "KeyError('LowerDir" in image_test_record[single_image]):
            print("------------------------------ [summslim] test", single_image, "------------------------------")
            test_result = test_original_image(single_image)
            if test_result == TEST_FAIL:
                image_test_record[single_image] = ORIGINAL_IMAGE_TEST_FAIL
            elif test_result == TEST_SUCCESS:
                summslim_result = summslim_image(single_image)
                if summslim_result is True:  # if summslim_result is True
                    test_result = test_summslim_image(single_image)
                    if test_result == TEST_SUCCESS:
                        image_test_record[single_image] = TEST_SUCCESS
                    elif test_result == TEST_FAIL:
                        image_test_record[single_image] = summslim_IMAGE_TEST_FAIL
                    else:
                        image_test_record[single_image] = test_result
                elif summslim_result:  # if there is exception info in summslim_result
                    image_test_record[single_image] = summslim_result
                else:  # if summslim_result is False
                    image_test_record[single_image] = summslim_FAIL
            else:
                image_test_record[single_image] = test_result
        else:
            print("------------------------------ [summslim] skip", single_image, "------------------------------")
        with open(large_scale_test_record_file, 'w') as fd:
            (json.dump(image_test_record, fd))

    # Write image_test_record to the file
    with open(large_scale_test_record_file, 'w') as fd:
        (json.dump(image_test_record, fd))

    print("[summslim] This test is completed")
