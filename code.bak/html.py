import sys
import os
import subprocess
import re


def clear_file_list(file_list, PATH):
    file_list = list(set(file_list))
    PATH_list = PATH.split(':')
    for i in range(len(file_list)):
        # check if the file exists
        if (not os.path.exists(file_list[i])):
            file_list[i] = ''
        if(os.path.isdir(file_list[i])):
            file_list[i] = ''
        # ignore /dev/xxx
        if(re.match(r'(/dev)',file_list[i])):
            file_list[i] = ''
        # ignore /proc/xxx
        if (re.match(r'(/proc)', file_list[i])):
            file_list[i] = ''
        # ignore /..
        if (re.match(r'(/\.\.)', file_list[i])):
            file_list[i] = ''

    # remove empty item
    while '' in file_list:
        file_list.remove('')

    return file_list


def parse_html(file_path, PATH):
    file_list = []

    # ldd find /xxx/xxxx
    status, output = subprocess.getstatusoutput("ldd %s" % file_path)
    re_match = re.findall(r"((\/[a-z0-9-\.]+)+)", output)
    if re_match:
        print("[zzcstalim] re_match: ", re_match)
        for i in range(len(re_match)):
            file_list.append(re_match[i][0])

    # strings find /xxx/xxxx
    status, output = subprocess.getstatusoutput("strings %s" % file_path)
    re_match = re.findall(r"((\/[a-z0-9-\.]+)+)", output)
    if re_match:
        print("[zzcstalim] re_match: ", re_match)
        for i in range(len(re_match)):
            file_list.append(re_match[i][0])

    file_list = clear_file_list(file_list, PATH)
    return file_list


if (__name__ == '__main__'):
    print("[zzcstalim] parse_html() test")
    print("[zzcstalim] argv: ", sys.argv)
    file_path = sys.argv[1]
    print("[zzcstalim] file_path: ", file_path)
    PATH = "/home/zzc/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/bin"  # need more process
    file_list = parse_binary(file_path, PATH)
    print("[zzcstalim] parse result: ", file_list)