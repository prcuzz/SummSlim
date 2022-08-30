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
    """
    get a image name list from the given url
    :param docker_hub_explore_url: the given url
    :return: list
    """

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
    try:
        result = zzcslim.zzcslim(image_name)
    except Exception as e:
        print("[error]", repr(e))
        return ": ".join((ZZCSLIM_FAIL, repr(e)))
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
    image_list = ['crate', 'bitnami/promtail', 'intel/intel-gpu-initcontainer', 'grafana/tempo-query',
                  'bitnami/jupyterhub', 'bitnami/mysqld-exporter', 'hashicorp/consul-k8s', 'amazon/cloudwatch-agent',
                  'rancher/rke2-upgrade', 'snyk/kubernetes-operator', 'kasmweb/java-dev', 'puppet/puppet-agent',
                  'bitnami/parse-dashboard', 'portainer/portainer-ce', 'bitnami/harbor-core',
                  'rancher/opni-monitoring-ui-build', 'bitnami/alertmanager', 'atlassian/jira-software', 'kong/kuma-cp',
                  'bitnami/ksql', 'rapidfort/redis6-ib', 'bitnami/kube-state-metrics', 'astronomerinc/ap-commander',
                  'newrelic/synthetics-job-manager', 'kasmweb/core-ex', 'mysql',
                  'rancher/mirrored-calico-pod2daemon-flexvol', 'rancher/security-scan',
                  'rancher/mirrored-metrics-server', 'balenalib/amd64-ubuntu-golang', 'circleci/mongo',
                  'docker/ucp-dsinfo', 'grafana/tempo-vulture', 'geonetwork', 'bitnami/osclass', 'bitnami/sonarqube',
                  'ibmcom/icp-nodejs-sample', 'circleci/python', 'spiped', 'haxe',
                  'rancher/nginx-ingress-controller-defaultbackend', 'bitnami/elasticsearch', 'orientdb',
                  'bitnami/apache-exporter', 'datadog/synthetics-private-location-worker', 'kong/ubi-kuma-cp',
                  'rancher/mirrored-coredns-coredns', 'circleci/frontend', 'bitnami/mariadb', 'rancher/library-busybox',
                  'kasmweb/only-office', 'bitnami/grafana-operator', 'docker/ucp-pause', 'kasmweb/nginx',
                  'airbyte/source-sentry', 'docker/ucp-controller', 'phpmyadmin', 'datadog/dd-trace-py', 'erlang',
                  'pingidentity/pingdataconsole', 'bitnami/phpmyadmin', 'ibmcom/pipeline-base-image',
                  'kasmweb/rdesktop', 'grafana/oncall', 'kasmweb/libre-office', 'circleci/docker-gc',
                  'ibmcom/ibm-alm-web', 'pingidentity/apache-jmeter', 'balenalib/raspberrypi3-64-debian',
                  'intel/intel-idxd-config-initcontainer', 'wallarm/sysbindings',
                  'percona/percona-server-mongodb-operator', 'balena/balena-mdns-publisher', 'bitnami/express',
                  'rancher/longhorn-manager', 'circleci/golang', 'intel/intel-gpu-plugin', 'balena/armv7hf-supervisor',
                  'rancher/net', 'circleci/builder-base', 'bitnami/prometheus-operator', 'puppet/puppetdb',
                  'amazon/dynamodb-local', 'grafana/loki', 'postgres', 'airbyte/temporal', 'circleci/mysql',
                  'circleci/buildpack-deps', 'rancher/lb-service-haproxy', 'intel/opae-nlb-demo', 'gcc',
                  'ibmcom/mcm-ui', 'kasmweb/desktop', 'airbyte/source-paypal-transaction', 'kasmweb/remmina',
                  'bitnami/sealed-secrets-controller', 'rapidfort/nats', 'newrelic/infrastructure', 'docker/ucp-agent',
                  'percona/percona-xtradb-cluster', 'kasmweb/firefox', 'kasmweb/inkscape', 'bitnami/airflow',
                  'datadog/squid', 'bitnami/prometheus', 'pachyderm/pachd', 'bitnami/kubeapps-asset-syncer',
                  'docker/for-desktop-kernel', 'greenbone/gsad', 'docker/ucp-interlock', 'bitnami/grafana-loki',
                  'bitnami/cluster-autoscaler', 'balenalib/raspberrypi0-2w-64-debian',
                  'balenalib/beaglebone-green-gateway-alpine-golang', 'circleci/php', 'bitnami/cassandra-exporter',
                  'pingidentity/pingaccess', 'grafana/grafana-enterprise', 'docker/dtr-rethink',
                  'bitnami/wavefront-prometheus-storage-adapter', 'grafana/grafana', 'rapidfort/redis', 'swipl',
                  'telegraf', 'bitnami/haproxy', 'yourls', 'lacework/rti-test1', 'r-base', 'greenbone/doxygen',
                  'rancher/calico-node', 'neo4j', 'grafana/grafana-dev', 'kong/pulp-worker', 'kasmweb/chromium',
                  'circleci/dynamodb', 'bitnami/kubectl', 'bitnami/consul', 'kong/kong-build-tools', 'kumahq/kuma-cp',
                  'balena/open-balena-registry-proxy', 'docker/getting-started', 'bitnami/kubeapps-dashboard',
                  'oraclelinux', 'pachyderm/worker-arm64', 'bitnami/discourse', 'amazon/aws-alb-ingress-controller',
                  'kasmweb/hunchly', 'balenalib/beaglebone-green-wifi-alpine-golang', 'bitnami/oauth2-proxy',
                  'newrelic/newrelic-prometheus-configurator', 'kong/kuma-dp', 'dynatrace/oneagent',
                  'kasmweb/desktop-deluxe', 'monica', 'hashicorp/dev-portal', 'bitnami/ghost', 'bitnami/minideb',
                  'bitnami/testlink', 'docker/dockerfile-copy', 'rancher/agent', 'kasmweb/ubuntu-bionic-desktop',
                  'amazon/aws-xray-daemon', 'bitnami/pushgateway', 'kasmweb/edge', 'photon',
                  'rancher/opensearch-dashboards', 'intel/intel-vpu-plugin', 'grafana/metaconvert',
                  'docker/highland_builder', 'kasmweb/core-remnux-bionic', 'kong/ubi-kuma-cni', 'bitnami/chartmuseum',
                  'grafana/grafana-image-renderer', 'rapidoid', 'arangodb', 'rancher/coreos-prometheus-config-reloader',
                  'rancher/server', 'bitnami/redis-cluster', 'bitnami/phpbb', 'kasmweb/doom', 'cimg/base',
                  'rancher/mirrored-pause', 'kasmweb/core-opensuse-15', 'rapidfort/redis-cluster', 'bitnami/cainjector',
                  'bitnami/acmesolver', 'docker/ucp-calico-cni', 'datadog/agent', 'kasmweb/teams', 'circleci/postgres',
                  'rancher/mirrored-calico-node', 'newrelic/infrastructure-bundle', 'rakudo-star',
                  'airbyte/source-amazon-ads', 'celery', 'rancher/opni', 'amazonlinux', 'greenbone/gpg-data',
                  'kong/kong', 'docker/kube-compose-api-server', 'odoo', 'kong/ubi-kuma-dp',
                  'snyk/kubernetes-operator-bundle', 'nextcloud', 'pachyderm/pachctl-amd64', 'rancher/hyperkube',
                  'bitnami/fluentd', 'intel/intel-sgx-plugin', 'rancher/container-crontab',
                  'rancher/calico-pod2daemon-flexvol', 'kasmweb/audacity', 'ibmcom/ibm-alm-mssql',
                  'datadog/chaos-handler', 'grafana/agentctl', 'drupal', 'bitnami/mysql', 'kong/kuma-init',
                  'google/cloud-sdk', 'joomla', 'datadog/agent-dev', 'rancher/metrics-server', 'bitnami/envoy',
                  'bitnami/cassandra', 'bitnami/harbor-notary-server', 'kong/ubi-kuma-init', 'okteto/backend',
                  'atlassian/artifactory-sidekick', 'thrift', 'circleci/android', 'amazon/aws-cli', 'docker/ucp-swarm',
                  'influxdb', 'kasmweb/signal', 'airbyte/init', 'vmware/powerclicore', 'cimg/python', 'satosa',
                  'docker/dtr-notary-server', 'redmine', 'bitnami/schema-registry', 'rapidfort/postgresql12-ib',
                  'kong/konnect-migration', 'datadog/cluster-agent', 'kasmweb/core-centos-7', 'kasmweb/pinta',
                  'pingidentity/pingintelligence', 'bitnami/pgbouncer', 'tomee', 'bitnami/golang', 'kasmweb/vlc',
                  'newrelic/php-daemon', 'bitnami/dex', 'hashicorp/terraform', 'rancher/jimmidyson-configmap-reload',
                  'kasmweb/vs-code', 'groovy', 'pachyderm/worker', 'pingidentity/pingauthorizepap',
                  'continuumio/miniconda3', 'glassfish', 'newrelic/nri-prometheus', 'archlinux',
                  'grafana/loki-operator', 'airbyte/source-salesforce', 'kong/kuma-cni', 'newrelic/nri-ecs',
                  'intel/intel-qat-plugin', 'kumahq/kumactl', 'fsharp', 'rancher/library-traefik',
                  'intel/intel-deviceplugin-operator', 'grafana/fluent-bit-plugin-loki', 'ibmcom/pause',
                  'hashicorp/terraform-website', 'snyk/code-agent', 'bitnami/postgres-exporter', 'airbyte/octavia-cli',
                  'rancher/rancher', 'bitnami/metrics-server', 'nuxeo', 'kasmweb/terminal', 'rapidfort/influxdb',
                  'bitnami/jasperreports', 'datadog/cluster-agent-dev', 'pingidentity/pingcentral',
                  'appdynamics/cluster-agent-operator', 'greenbone/gvm-tools', 'bitnami/rabbitmq',
                  'kasmweb/core-cuda-bionic', 'docker/dtr-registry', 'django', 'rapidfort/mysql',
                  'docker/ucp-calico-kube-controllers', 'intel/intel-fpga-plugin', 'fluentd', 'bitnami/openldap',
                  'percona/percona-server-mongodb', 'bitnami/metallb-controller',
                  'percona/percona-xtradb-cluster-operator', 'kumahq/kuma-init', 'cimg/openjdk', 'uffizzi/app',
                  'balena/aarch64-supervisor', 'pachyderm/pachctl', 'amazon/aws-efs-csi-driver', 'kasmweb/tor-browser',
                  'rancher/mirrored-library-nginx', 'rancher/metrics-server-amd64', 'rancher/gitjob', 'cimg/ruby',
                  'airbyte/metrics-reporter', 'grafana/loki-canary', 'eclipse-temurin', 'sysdig/agent',
                  'rapidfort/nginx-ib', 'grafana/grafana-oss-dev', 'rancher/rancher-runtime', 'bitnami/kubewatch',
                  'bitnami/rclone', 'docker/ucp-kube-compose-api', 'ibm-semeru-runtimes',
                  'bitnami/wavefront-hpa-adapter', 'balenalib/beaglebone-black-alpine-golang', 'haskell',
                  'purestorage/ccm-go', 'atlassian/pipelines-auth-proxy', 'airbyte/worker',
                  'bitnami/harbor-notary-signer', 'bitnami/kiam', 'docker/ucp-auth-store', 'ibmjava', 'bitnami/ruby',
                  'portainer/agent', 'mirantis/ucp-agent', 'circleci/clojure', 'bitnami/harbor-jobservice',
                  'bitnami/kafka-exporter', 'grafana/grafana-oss-image-tags', 'bitnami/external-dns',
                  'airbyte/container-orchestrator', 'bitnami/pinniped', 'docker/aci-hostnames-sidecar', 'okteto/okteto',
                  'rancher/fleet', 'rapidfort/fluentd', 'greenbone/openvas-scanner', 'ibmcom/guestbook',
                  'kasmweb/core-oracle-7', 'rancher/pause', 'cimg/go', 'rancher/fluentd', 'atlassian/bitbucket-server',
                  'rapidfort/mongodb', 'rancher/klipper-helm', 'amazon/aws-for-fluent-bit',
                  'bitnami/nginx-ingress-controller', 'bitnami/mongodb-exporter', 'docker/volumes-backup-extension',
                  'rapidfort/airflow-scheduler', 'balenalib/raspberrypi4-64-debian', 'continuumio/anaconda3',
                  'datadog/apigentools', 'swift', 'formio/formio-enterprise', 'circleci/node',
                  'atlassian/bamboo-specs-runner', 'lightstreamer', 'bitnami/matomo', 'okteto/frontend', 'ruby',
                  'bitnami/bitnami-shell', 'pypy', 'bitnami/prometheus-rsocket-proxy', 'ubuntu/nginx',
                  'hashicorp/vault', 'kong/pulp-content', 'bitnami/mongodb', 'ibmcom/mq', 'bitnami/wordpress',
                  'bitnami/neo4j', 'bitnami/jmx-exporter', 'kong/pulp-core', 'rapidfort/rabbitmq',
                  'circleci/container-agent', 'cimg/node', 'airbyte/server', 'docker/ucp-cfssl',
                  'docker/dockerfile-upstream', 'kasmweb/atom', 'kasmweb/core', 'intel/intel-fpga-initcontainer',
                  'snyk/kubernetes-monitor', 'bitnami/kubernetes-event-exporter', 'pingidentity/pingdirectoryproxy',
                  'bitnami/metallb-speaker', 'intel/intel-qat-initcontainer', 'bitnami/keycloak-config-cli',
                  'hashicorp/packer', 'rapidfort/postgresql', 'pachyderm/haberdashery', 'Kaazing Gateway',
                  'circleci/mariadb', 'docker/ucp-metrics', 'pingidentity/pingtoolkit', 'atlassian/pipelines-agent',
                  'python', 'rancher/grafana-grafana', 'balenalib/raspberrypi3-64',
                  'balenalib/beaglebone-pocket-alpine-golang', 'bitnami/geode', 'bitnami/elasticsearch-exporter',
                  'controlm/workbench', 'kibana', 'node', 'hashicorp/http-echo', 'wallarm/api-firewall',
                  'grafana/enterprise-logs', 'docker/dtr-api', 'kasmweb/telegram', 'pachyderm/pachtf',
                  'bitnami/contour', 'rancher/prom-prometheus', 'perl', 'mediawiki', 'friendica', 'airbyte/bootloader',
                  'balenalib/beagleboard-xm-alpine-golang', 'bitnami/spring-cloud-dataflow-shell', 'grafana/mimir',
                  'rancher/metadata', 'docker/ucp-kube-dns', 'kong/nightly-ingress-controller', 'rancher/dns',
                  'balenalib/raspberrypi0-2w-64', 'kasmweb/steam', 'docker/ucp-kube-compose', 'rancher/k8s',
                  'docker/ucp-etcd', 'circleci/openjdk', 'rancher/docs', 'grafana/promtail', 'intel/intel-dlb-plugin',
                  'bitnami/openresty', 'appdynamics/machine-agent-analytics', 'balenalib/amd64-fedora-node',
                  'circleci/redis', 'postfixadmin', 'aerospike', 'rethinkdb', 'kasmweb/maltego', 'rapidfort/prometheus',
                  'kong/ubi-kumactl', 'hashicorp/vault-k8s', 'docker/ecs-searchdomain-sidecar', 'rancher/opensearch',
                  'datadog/chaos-injector', 'bitnami/magento', 'bitnami/kafka', 'kasmweb/core-ubuntu-focal',
                  'bitnami/haproxy-intel', 'rancher/network-manager', 'rancher/prom-node-exporter',
                  'amazon/aws-node-termination-handler', 'purestorage/k8s', 'bitnami/airflow-worker',
                  'percona/percona-server', 'rancher/mirrored-prometheus-node-exporter',
                  'rancher/cluster-proportional-autoscaler', 'rancher/calico-cni', 'bitnami/thanos',
                  'datadog/chaos-controller', 'express-gateway', 'airbyte/destination-s3', 'airbyte/webapp',
                  'rancher/scheduler', 'convertigo', 'ibmcom/ibm-db2uoperator-catalog', 'cockroachdb/cockroach',
                  'kumahq/kuma-dp', 'balenalib/raspberrypicm4-ioboard', 'bitnami/redis-exporter',
                  'balenalib/beaglebone-green-alpine-golang', 'balenalib/raspberrypi400-64-debian',
                  'greenbone/ospd-openvas', 'kasmweb/ubuntu-jammy-desktop', 'airbyte/db', 'bitnami/consul-exporter',
                  'datadog/dogstatsd-dev', 'bitnami/mediawiki', 'intel/intel-dsa-plugin', 'rancher/istio-kubectl',
                  'elixir', 'hashicorp/tfc-agent', 'bitnami/nginx', 'pachyderm/notebooks-user',
                  'rancher/mirrored-calico-cni', 'uffizzi/cli', 'grafana/agent-operator',
                  'snyk/kubernetes-operator-index', 'kasmweb/ubuntu-focal-dind',
                  'balenalib/raspberrypicm4-ioboard-debian', 'grafana/grafana-oss', 'rapidfort/apache',
                  'bitnami/suitecrm', 'bitnami/tensorflow-serving', 'bitnami/redis-sentinel',
                  'docker/desktop-kubernetes', 'hashicorp/consul-template', 'bitnami/blackbox-exporter',
                  'newrelic/nri-kube-events', 'tomcat', 'grafana/tempo', 'bitnami/harbor-adapter-trivy',
                  'docker/ucp-compose', 'newrelic/k8s-events-forwarder', 'amazon/opendistro-for-elasticsearch',
                  'kong/pulp-resource-manager', 'pingidentity/pingdatasync', 'kong/ubi-kuma-prometheus-sd',
                  'bitnami/odoo', 'grafana/grafana-plugin-ci', 'gazebo', 'bitnami/parse', 'datadog/docker-dd-agent',
                  'rancher/system-agent-installer-rke2', 'varnish', 'docker/ucp-auth', 'rancher/prometheus-auth',
                  'intel/intel-iaa-plugin', 'bitnami/nginx-intel', 'rancher/rancher-agent', 'jruby', 'matomo',
                  'kasmweb/brave', 'bitnami/spring-cloud-dataflow-composed-task-runner', 'rancher/shell',
                  'bitnami/pgpool', 'pachyderm/mount-server-amd64', 'pingidentity/pingdirectory',
                  'airbyte/source-asana', 'rancher/os', 'kasmweb/ubuntu-focal-dind-rootless', 'bitnami/logstash',
                  'kong/kuma-prometheus-sd', 'openjdk', 'solr', 'rancher/configmap-reload', 'amazon/aws-fsx-csi-driver',
                  'atlassian/pipelines-dvcstools', 'pachyderm/mount-server', 'bitnami/airflow-scheduler',
                  'rancher/rancher-operator', 'rancher/log-aggregator', 'rancher/opni-python-base',
                  'greenbone/notus-scanner', 'bitnami/memcached-exporter', 'bitnami/nats',
                  'pachyderm/mount-server-arm64', 'amazoncorretto', 'xwiki', 'atlassian/jira-servicemanagement',
                  'kasmweb/discord', 'lacework/datacollector', 'kasmweb/firefox-mobile', 'rancher/coredns-coredns',
                  'bitnami/cert-manager', 'elasticsearch', 'kasmweb/ubuntu-focal-desktop', 'bitnami/minio',
                  'docker/ucp-hyperkube', 'rancher/rke-tools', 'atlassian/pipelines-awscli', 'puppet/puppetserver',
                  'pingidentity/pingauthorize', 'znc', 'hashicorp/consul', 'golang', 'kasmweb/core-ubuntu-jammy',
                  'docker/ucp-azure-ip-allocator', 'bitnami/harbor-exporter', 'airbyte/cli', 'rails',
                  'bitnami/opencart', 'amazon/simpleiot-installer', 'kasmweb/centos-7-desktop', 'bitnami/memcached',
                  'cimg/php', 'amazon/amazon-ecs-agent', 'bitnami/node', 'rancher/healthcheck', 'open-liberty',
                  'dynatrace/dynatrace-operator', 'grafana/query-tee', 'hylang', 'pingidentity/pingdelegator',
                  'rapidfort/nginx', 'kumahq/kuma-cni', 'grafana/grafana-enterprise-dev',
                  'dynatrace/dynatrace-oneagent-operator', 'rancher/local-path-provisioner',
                  'grafana/fluent-plugin-loki', 'bitnami/harbor-registry', 'amazon/amazon-ecs-sample',
                  'bitnami/azure-cli', 'newrelic/nri-kubernetes', 'rancher/rancher-webhook',
                  'atlassian/confluence-server', 'bitnami/mxnet', 'lacework/datacollector-nightly', 'bitnami/solr',
                  'intel/intel-fpga-admissionwebhook', 'bitnami/symfony', 'bitnami/spark', 'kasmweb/chrome',
                  'cassandra', 'bitnami/redis', 'kasmweb/deluge', 'bitnami/jsonnet', 'kasmweb/postman',
                  'rancher/kube-api-auth', 'bitnami/airflow-exporter', 'newrelic/nri-forwarder', 'kasmweb/qbittorrent',
                  'almalinux', 'bitnami/jupyter-base-notebook', 'grafana/logstash-output-loki', 'bitnami/kibana',
                  'docker/ucp-calico-node', 'bitnami/java', 'pingidentity/pingfederate', 'amazon/aws-otel-collector',
                  'docker/kube-compose-controller', 'intel/crypto-perf', 'rancher/coreos-flannel',
                  'grafana/grafana-image-tags', 'bitnami/kong-ingress-controller', 'bitnami/cert-manager-webhook',
                  'bitnami/moodle', 'irssi', 'docker/ucp-interlock-extension', 'rancher/nginx-ingress-controller',
                  'circleci/ruby', 'docker/dtr-notary-signer', 'snyk/broker', 'bitnami/postgresql-repmgr',
                  'docker/compose', 'bitnami/etcd', 'percona/pmm-server', 'rapidfort/airflow', 'greenbone/mqtt-broker',
                  'rapidfort/wordpress', 'kapacitor', 'bonita', 'okteto/registry', 'rancher/system-agent-installer-k3s',
                  'rockylinux', 'kasmweb/core-oracle-8', 'kasmweb/vmware-horizon', 'kasmweb/insomnia',
                  'snyk/snyk-iac-rules', 'greenbone/redis-server', 'grafana/mimir-continuous-test', 'php-zendserver',
                  'plone', 'greenbone/gsad-build', 'grafana/logcli', 'kasmweb/core-remnux-focal', 'ghost',
                  'airbyte/source-sendgrid', 'puppet/continuous-delivery-for-puppet-enterprise',
                  'docker/ucp-kube-dns-dnsmasq-nanny', 'docker/dtr-jobrunner', 'kasmweb/opensuse-15-desktop',
                  'kasmweb/zoom', 'amazon/aws-ebs-csi-driver', 'kasmweb/filezilla', 'circleci/circleci-cli',
                  'kasmweb/core-ubuntu-bionic', 'intel/intel-sgx-admissionwebhook', 'ibmcom/ibm-operator-catalog',
                  'kasmweb/sublime-text', 'atlassian/dcapt', 'pachyderm/worker-amd64', 'bitnami/ejbca',
                  'docker/ucp-kube-dns-sidecar', 'mariadb', 'kasmweb/slack', 'rancher/klipper-lb', 'rust',
                  'bitnami/harbor-registryctl', 'rancher/fleet-agent', 'bitnami/configmap-reload', 'storm',
                  'kasmweb/tracelabs', 'grafana/loki-query-tee', 'kasmweb/core-cuda-focal', 'balenalib/raspberrypi4-64',
                  'rapidfort/etcd', 'mono', 'bitnami/git', 'lacework/lacebook', 'mongo', 'rapidfort/envoy',
                  'docker/dockerfile', 'piwik', 'logstash', 'redis', 'bitnami/node-exporter',
                  'puppet/puppet-agent-ubuntu', 'mirantis/ucp-auth', 'silverpeas', 'grafana/agent',
                  'rapidfort/airflow-worker', 'datadog/dogstatsd', 'intel/intel-sgx-initcontainer', 'websphere-liberty',
                  'atlassian/pipelines-docker-daemon', 'bitnami/zookeeper', 'rapidfort/mariadb',
                  'pachyderm/pachd-amd64', 'kasmweb/gimp', 'bitnami/grafana', 'hola-mundo', 'bitnami/dokuwiki', 'maven',
                  'eggdrop', 'docker/for-desktop-kernel-grpcfuse', 'docker/dtr-nginx', 'bitnami/postgresql',
                  'bitnami/mariadb-galera', 'ibmcom/cloudant-developer', 'newrelic/newrelic-fluentbit-output',
                  'clojure', 'rancher/rancher-csp-adapter', 'atlassian/jira-core', 'portainer/templates',
                  'docker/ucp-interlock-proxy', 'rancher/k3s', 'bitnami/gradle', 'julia', 'rancher/istio-proxyv2',
                  'docker/ucp', 'bitnami/elasticsearch-curator', 'ros', 'gradle', 'balenalib/raspberrypi400-64',
                  'launchdarkly/ld-relay', 'airbyte/cron', 'kong/pulp-api', 'atlassian/jira-servicedesk',
                  'atlassian/default-image', 'bitnami/percona-xtrabackup', 'ibmcom/ibm-common-service-catalog',
                  'cimg/postgres', 'rancher/rke2-runtime', 'pachyderm/pachd-arm64', 'kasmweb/thunderbird',
                  'bitnami/apache', 'snyk/ask-code', 'rapidfort/oncall', 'bitnami/nginx-exporter', 'jetty',
                  'pachyderm/pachctl-arm64', 'ibmcom/ibm-alm-api', 'neurodebian', 'circleci/picard',
                  'grafana/mimirtool', 'hello-seattle', 'bitnami/percona-mysql', 'kong/kumactl',
                  'newrelic/infrastructure-k8s', 'wordpress', 'astronomerinc/ap-houston-api',
                  'rancher/system-agent-installer-rancher', 'rancher/mirrored-istio-proxyv2', 'zookeeper',
                  'grafana/grafana-enterprise-image-tags', 'pingidentity/ldap-sdk-tools', 'ibmcom/icp-swift-sample',
                  'iojs']

    large_scale_test_record_file = "large_scale_test_record"

    # Read image_test_record from the file
    if os.path.exists(large_scale_test_record_file):
        with open(large_scale_test_record_file, 'r') as fd:
            image_test_record = json.load(fd)
    else:
        image_test_record = {}

    for single_image in image_list:
        if single_image not in image_test_record.keys() or (
                single_image in image_test_record.keys() and "error" in image_test_record[single_image]):
            print("------------------------------ [zzcslim] test", single_image, "------------------------------")
            test_result = test_original_image(single_image)
            if test_result == TEST_FAIL:
                image_test_record[single_image] = ORIGINAL_IMAGE_TEST_FAIL
            elif test_result == TEST_SUCCESS:
                zzcslim_result = zzcslim_image(single_image)
                if zzcslim_result is True:  # if zzcslim_result is True
                    test_result = test_zzcslim_image(single_image)
                    if test_result == TEST_SUCCESS:
                        image_test_record[single_image] = TEST_SUCCESS
                    elif test_result == TEST_FAIL:
                        image_test_record[single_image] = ZZCSLIM_IMAGE_TEST_FAIL
                    else:
                        image_test_record[single_image] = test_result
                elif zzcslim_result:  # if there is exception info in zzcslim_result
                    image_test_record[single_image] = zzcslim_result
                else:  # if zzcslim_result is False
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
