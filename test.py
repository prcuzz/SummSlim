import sys
import magic
import os
import sys
from requests_html import HTMLSession
import re
import docker
import json
import fnmatch

session = HTMLSession()
docker_hub_url = "https://hub.docker.com/_/postgres"
try:
    r = session.get(docker_hub_url)
    r.html.render(timeout=256)
except:
    print("[error]access docker hub or render fail")
    exit(0)

re_match = re.findall(r"docker run [^\n]*\n", r.html.full_text.replace("\\\n", " ").replace("\t", ""))
print(re_match)

for i in range(len(re_match)):
    re_match_1 = re.findall(r"-e [\S]*", re_match[i])
    print(re_match_1)
    env = {}
    for i in range(len(re_match_1)):
        re_match_1[i]=re_match_1[i].replace("-e ","")
        env[re_match_1[i].split('=')[0]] = re_match_1[i].split('=')[1]
    print(env)