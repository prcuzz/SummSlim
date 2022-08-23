import json
import os
import time

import docker
from bs4 import BeautifulSoup
from requests_html import HTMLSession

import shell_script_dynamic_analysis
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
    docker_run_example = shell_script_dynamic_analysis.get_docker_run_example(image_name)

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
    print("[zzcslim] testing original image", image_name)
    return test_image(image_name)


def test_zzcslim_image(image_name):
    print("[zzcslim] testing slimed image", image_name)
    return test_image(image_name + ".zzcslim")


def zzcslim_image(image_name):
    print("[zzcslim] sliming image", image_name)
    return zzcslim.zzcslim(image_name)


if __name__ == "__main__":
    '''
    page_num = 14
    docker_hub_explore_url = "https://hub.docker.com/search?q=&image_filter=official%2Cstore&type=image&operating_system=linux&page=" + str(
        page_num)

    image_list_in_current_page = get_image_list_in_current_page(docker_hub_explore_url)
    '''

    # This list is captured directly with a crawler, so I don't have to go to dockerhub to get it every time
    image_list_in_current_page = ['redmine', 'jruby', 'rethinkdb', 'odoo', 'elixir', 'phpmyadmin', 'kapacitor', 'jetty',
                                  'amazoncorretto', 'mono', 'erlang', 'websphere-liberty', 'clojure', 'mediawiki',
                                  'oraclelinux', 'swift', 'arangodb', 'haxe', 'znc', 'xwiki', 'django', 'iojs', 'crate',
                                  'gcc', 'piwik', 'yourls', 'archlinux', 'hylang', 'ros', 'eclipse-temurin', 'julia',
                                  'tomee', 'photon', 'aerospike', 'monica', 'ibmjava', 'bonita', 'orientdb', 'varnish',
                                  'neurodebian', 'rails', 'fluentd', 'open-liberty', 'irssi', 'r-base', 'convertigo',
                                  'storm', 'haskell', 'lightstreamer', 'plone', 'fluentd', 'convertigo', 'geonetwork',
                                  'nuxeo', 'php-zendserver', 'postfixadmin', 'gazebo', 'fsharp', 'eggdrop',
                                  'lightstreamer', 'friendica', 'express-gateway', 'hello-seattle', 'spiped', 'thrift',
                                  'rockylinux', 'rapidoid', 'celery', 'swipl', 'almalinux', 'rakudo-star', 'silverpeas',
                                  'Kaazing Gateway', 'hola-mundo', 'glassfish',
                                  'percona/percona-xtradb-cluster-operator', 'wallarm/api-firewall', 'bitnami/mongodb',
                                  'grafana/promtail', 'amazon/amazon-ecs-agent', 'portainer/portainer-ce',
                                  'grafana/loki', 'docker/ucp-agent', 'bitnami/external-dns', 'amazon/cloudwatch-agent',
                                  'dynatrace/oneagent', 'amazon/aws-xray-daemon', 'docker/ucp-auth', 'portainer/agent',
                                  'bitnami/mariadb', 'amazon/aws-for-fluent-bit', 'bitnami/rabbitmq',
                                  'docker/aci-hostnames-sidecar', 'circleci/postgres', 'circleci/node',
                                  'amazon/aws-cli', 'rancher/pause', 'datadog/docker-dd-agent', 'hashicorp/terraform',
                                  'sysdig/agent', 'lacework/datacollector', 'circleci/ruby', 'cockroachdb/cockroach',
                                  'google/cloud-sdk', 'bitnami/nginx', 'circleci/mysql', 'mirantis/ucp-agent',
                                  'bitnami/kafka', 'bitnami/zookeeper', 'amazon/dynamodb-local', 'circleci/redis',
                                  'rancher/rancher', 'circleci/python', 'newrelic/infrastructure-bundle',
                                  'docker/dockerfile', 'bitnami/minideb', 'amazon/amazon-ecs-sample',
                                  'docker/ucp-interlock-proxy', 'hashicorp/consul-template', 'bitnami/redis-sentinel',
                                  'docker/ecs-searchdomain-sidecar', 'bitnami/mysql', 'cimg/node', 'bitnami/ghost',
                                  'ibmcom/ibm-common-service-catalog', 'rancher/metrics-server',
                                  'bitnami/metrics-server', 'bitnami/redis-exporter', 'mirantis/ucp-auth',
                                  'atlassian/pipelines-agent', 'atlassian/pipelines-dvcstools', 'ibmcom/pause',
                                  'amazon/aws-node-termination-handler', 'datadog/cluster-agent', 'rancher/agent',
                                  'newrelic/php-daemon', 'bitnami/etcd', 'atlassian/pipelines-docker-daemon',
                                  'bitnami/memcached', 'newrelic/infrastructure', 'newrelic/infrastructure-k8s',
                                  'ibmcom/ibm-operator-catalog', 'rancher/fleet-agent', 'bitnami/elasticsearch',
                                  'atlassian/pipelines-auth-proxy', 'rancher/local-path-provisioner', 'rancher/server',
                                  'rancher/net', 'amazon/aws-efs-csi-driver', 'bitnami/wordpress',
                                  'bitnami/oauth2-proxy', 'atlassian/default-image', 'circleci/docker-gc',
                                  'rancher/coredns-coredns', 'rancher/shell', 'amazon/aws-alb-ingress-controller',
                                  'bitnami/cassandra', 'bitnami/phpmyadmin', 'rancher/rke-tools', 'rancher/calico-node',
                                  'circleci/openjdk', 'atlassian/confluence-server', 'docker/compose', 'cimg/ruby',
                                  'bitnami/kubewatch', 'grafana/fluent-bit-plugin-loki', 'cimg/python',
                                  'puppet/continuous-delivery-for-puppet-enterprise', 'bitnami/postgres-exporter',
                                  'circleci/golang', 'bitnami/dokuwiki', 'rancher/hyperkube', 'rancher/mirrored-pause',
                                  'rancher/nginx-ingress-controller', 'balena/aarch64-supervisor', 'cimg/base',
                                  'grafana/agent', 'rancher/klipper-lb', 'hashicorp/http-echo', 'bitnami/node-exporter',
                                  'docker/ucp', 'circleci/frontend', 'bitnami/kube-state-metrics', 'bitnami/fluentd',
                                  'bitnami/mongodb-exporter', 'bitnami/postgresql-repmgr', 'bitnami/prometheus',
                                  'amazon/opendistro-for-elasticsearch', 'bitnami/grafana', 'rancher/calico-cni',
                                  'circleci/mongo', 'rancher/istio-proxyv2', 'rancher/mirrored-istio-proxyv2',
                                  'docker/dockerfile-copy', 'circleci/php', 'docker/getting-started', 'bitnami/node',
                                  'amazon/aws-ebs-csi-driver', 'rancher/lb-service-haproxy', 'hashicorp/packer',
                                  'rancher/os', 'rancher/coreos-flannel', 'circleci/android',
                                  'bitnami/kubeapps-asset-syncer', 'rancher/fleet', 'rancher/network-manager',
                                  'bitnami/testlink', 'balena/armv7hf-supervisor', 'rancher/metadata', 'rancher/gitjob',
                                  'rancher/klipper-helm', 'rancher/dns', 'docker/ucp-interlock', 'rancher/healthcheck',
                                  'bitnami/alertmanager', 'puppet/puppetserver', 'atlassian/bitbucket-server',
                                  'bitnami/mariadb-galera', 'bitnami/ruby', 'hashicorp/tfc-agent', 'docker/ucp-pause',
                                  'bitnami/nats', 'percona/percona-xtradb-cluster', 'docker/ucp-controller',
                                  'docker/ucp-auth-store', 'docker/ucp-etcd', 'docker/ucp-swarm', 'bitnami/git',
                                  'cimg/postgres', 'docker/ucp-cfssl', 'docker/ucp-dsinfo', 'docker/ucp-metrics',
                                  'docker/ucp-compose', 'docker/ucp-hyperkube', 'docker/ucp-interlock-extension',
                                  'docker/ucp-calico-node', 'docker/ucp-calico-cni', 'percona/percona-server',
                                  'continuumio/miniconda3', 'bitnami/nginx-ingress-controller', 'bitnami/kibana',
                                  'docker/ucp-kube-compose', 'docker/ucp-calico-kube-controllers',
                                  'atlassian/jira-software', 'docker/ucp-kube-dns-sidecar', 'docker/ucp-kube-dns',
                                  'grafana/grafana-image-renderer', 'docker/ucp-kube-dns-dnsmasq-nanny',
                                  'amazon/aws-otel-collector', 'bitnami/redis-cluster',
                                  'rancher/calico-pod2daemon-flexvol', 'newrelic/newrelic-fluentbit-output',
                                  'hashicorp/consul', 'datadog/dogstatsd', 'rancher/log-aggregator', 'bitnami/apache',
                                  'cimg/openjdk', 'dynatrace/dynatrace-oneagent-operator', 'kasmweb/firefox',
                                  'ibmcom/mq', 'newrelic/nri-ecs', 'kasmweb/chrome', 'docker/kube-compose-api-server',
                                  'rancher/fluentd', 'bitnami/moodle', 'datadog/synthetics-private-location-worker',
                                  'rancher/prom-prometheus', 'cimg/go', 'rancher/prom-node-exporter',
                                  'launchdarkly/ld-relay', 'rancher/rancher-operator', 'bitnami/matomo',
                                  'rancher/cluster-proportional-autoscaler', 'docker/ucp-kube-compose-api',
                                  'atlassian/pipelines-awscli', 'docker/ucp-azure-ip-allocator',
                                  'bitnami/kubeapps-dashboard', 'bitnami/minio', 'rancher/library-traefik',
                                  'bitnami/pgpool', 'bitnami/prometheus-operator', 'hashicorp/vault-k8s',
                                  'docker/kube-compose-controller', 'circleci/dynamodb', 'bitnami/bitnami-shell',
                                  'kasmweb/tor-browser', 'hashicorp/vault', 'rancher/longhorn-manager',
                                  'kasmweb/desktop-deluxe', 'rancher/nginx-ingress-controller-defaultbackend',
                                  'ibmcom/cloudant-developer', 'docker/dtr-registry', 'rancher/mirrored-metrics-server',
                                  'percona/percona-server-mongodb-operator', 'docker/dtr-rethink',
                                  'rancher/jimmidyson-configmap-reload', 'datadog/squid', 'rancher/k3s',
                                  'docker/dtr-jobrunner', 'docker/highland_builder', 'newrelic/k8s-events-forwarder',
                                  'rancher/kube-api-auth', 'purestorage/k8s', 'docker/dtr-notary-server',
                                  'docker/dtr-notary-signer', 'rancher/mirrored-calico-cni', 'docker/dtr-nginx',
                                  'kasmweb/desktop', 'rancher/system-agent-installer-rke2', 'circleci/buildpack-deps',
                                  'rancher/mirrored-coredns-coredns', 'circleci/picard',
                                  'rancher/mirrored-library-nginx', 'rancher/scheduler', 'vmware/powerclicore',
                                  'bitnami/apache-exporter', 'ibmcom/icp-swift-sample', 'rancher/grafana-grafana',
                                  'bitnami/jmx-exporter', 'ibmcom/ibm-db2uoperator-catalog',
                                  'bitnami/elasticsearch-curator', 'bitnami/neo4j', 'ibmcom/icp-nodejs-sample',
                                  'appdynamics/cluster-agent-operator', 'rancher/library-busybox',
                                  'bitnami/elasticsearch-exporter', 'bitnami/solr', 'ibmcom/mcm-ui',
                                  'rancher/mirrored-calico-node', 'ibmcom/guestbook',
                                  'rancher/mirrored-calico-pod2daemon-flexvol', 'formio/formio-enterprise',
                                  'ibmcom/pipeline-base-image', 'pingidentity/pingfederate',
                                  'bitnami/sealed-secrets-controller', 'hashicorp/consul-k8s', 'rancher/k8s',
                                  'datadog/agent-dev', 'rancher/coreos-prometheus-config-reloader',
                                  'rancher/security-scan', 'percona/percona-server-mongodb', 'bitnami/kafka-exporter',
                                  'bitnami/mysqld-exporter', 'rancher/container-crontab', 'rancher/prometheus-auth',
                                  'bitnami/discourse', 'circleci/clojure', 'atlassian/artifactory-sidekick',
                                  'dynatrace/dynatrace-operator', 'bitnami/magento', 'continuumio/anaconda3',
                                  'newrelic/nri-prometheus', 'snyk/kubernetes-monitor', 'docker/dtr-api',
                                  'bitnami/consul', 'portainer/templates', 'rancher/istio-kubectl', 'puppet/puppetdb',
                                  'rancher/mirrored-prometheus-node-exporter', 'rancher/metrics-server-amd64',
                                  'ubuntu/nginx', 'bitnami/thanos', 'percona/pmm-server', 'rancher/rancher-webhook',
                                  'appdynamics/machine-agent-analytics', 'bitnami/spark', 'grafana/tempo',
                                  'snyk/broker', 'circleci/mariadb', 'bitnami/jasperreports',
                                  'rancher/configmap-reload', 'docker/desktop-kubernetes', 'cimg/php',
                                  'bitnami/nginx-exporter', 'circleci/builder-base']

    large_scale_test_record_file = "large_scale_test_record"

    # Read image_test_record from the file
    if os.path.exists(large_scale_test_record_file):
        with open(large_scale_test_record_file, 'r') as fd:
            image_test_record = json.load(fd)
    else:
        image_test_record = {}

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
