from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os


def get_dockerfile(image_name):
    driver = webdriver.Firefox(
        executable_path=r"C:\Users\ZZC\Desktop\geckodriver-v0.32.2-win64\geckodriver.exe")  # Firefox浏览器
    # driver = webdriver.Firefox("驱动路径")
    driver.maximize_window()

    # 打开网页
    url = "https://hub.docker.com/_/" + image_name + "/tags"
    driver.get(url)  # 打开url网页 比如 driver.get("http://www.baidu.com")

    time.sleep(3)
    driver.implicitly_wait(20)
    ele = driver.find_element(By.CSS_SELECTOR,
                              "[class='MuiTypography-root MuiTypography-inherit MuiLink-root MuiLink-underlineAlways css-w4l1vf']")
    if ele.is_displayed():
        ele.click()

    time.sleep(3)
    driver.implicitly_wait(20)
    commands_elements = driver.find_elements(By.CSS_SELECTOR,
                                             "[data-field='command']>[class='MuiTypography-root MuiTypography-body1 css-12w6iwm']")

    commands = []
    for element in commands_elements:
        commands.append(element.text)
    print(commands)

    size_elements = driver.find_elements(By.CSS_SELECTOR,
                                         "[data-field='size'][class='MuiDataGrid-cell--withRenderer MuiDataGrid-cell MuiDataGrid-cell--textRight']")

    sizes = []
    for element in size_elements:
        sizes.append(element.text)
    print(sizes)

    with open(".\\dockerfiles\\" + image_name, 'w') as f:
        for i in range(len(commands)):
            f.write(commands[i] + "||" + sizes[i] + "\n")

    driver.close()


official_image_list = ['clojure', 'piwik', 'logstash', 'redis', 'silverpeas',
                       'websphere-liberty', 'hola-mundo', 'maven', 'eggdrop', 'julia', 'ros',
                       'gradle', 'jetty', 'neurodebian', 'hello-seattle', 'wordpress', 'zookeeper', 'crate', 'mysql',
                       'geonetwork', 'spiped', 'haxe', 'orientdb', 'phpmyadmin', 'erlang', 'postgres',
                       'gcc', 'swipl', 'telegraf', 'yourls', 'r-base', 'neo4j', 'oraclelinux', 'monica', 'photon',
                       'rapidoid', 'arangodb', 'rakudo-star', 'celery', 'amazonlinux', 'odoo', 'nextcloud', 'drupal',
                       'joomla', 'thrift', 'influxdb', 'satosa', 'redmine', 'tomee',
                       'groovy', 'archlinux', 'fsharp', 'nuxeo', 'django', 'fluentd', 'eclipse-temurin',
                       'ibm-semeru-runtimes', 'haskell', 'ibmjava', 'swift', 'lightstreamer', 'ruby', 'pypy', 'python',
                       'kibana', 'node', 'perl', 'mediawiki', 'friendica', 'postfixadmin',
                       'aerospike', 'rethinkdb', 'express-gateway', 'convertigo', 'elixir',
                       'tomcat', 'gazebo', 'varnish', 'jruby', 'matomo', 'openjdk', 'solr', 'amazoncorretto', 'xwiki',
                       'elasticsearch', 'znc', 'golang', 'rails', 'open-liberty', 'hylang', 'cassandra', 'almalinux',
                       'irssi', 'kapacitor', 'bonita', 'rockylinux', 'php-zendserver', 'plone', 'ghost', 'mariadb',
                       'rust', 'storm', 'mono', 'mongo', 'iojs']
for image in official_image_list:
    if (not os.path.exists(".\\dockerfiles\\" + image) or os.path.getsize(".\\dockerfiles\\" + image) < 50):
        try:
            print("get_dockerfile(): ", image)
            get_dockerfile(image)
        except Exception as e:
            print(e)
            continue
