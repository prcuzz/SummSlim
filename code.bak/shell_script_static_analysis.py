import sys
import re
import os


def is_sh_script_file(filepath):
    if(not os.path.exists(filepath)):
        print("is_sh_script_file() file not exist")
        return False

    if (re.search(r'(\.sh$)', filepath)):
        return True

    try:
        f = open(filepath, mode='r')
    except:
        print("[error] open file error")
        return False

    content = f.readline()
    if (("#!/bin/sh" in content) or ("#!/bin/bash" in content)):
        return True

    return False


def find_absolute_path(file_list, PATH_list):
    file_list = list(set(file_list))
    for i in range(len(file_list)):
        for j in range(len(PATH_list)):
            # check if the path is in the PATH
            if (os.path.exists(PATH_list[j] + '/' + file_list[i])):
                file_list[i] = PATH_list[j] + '/' + file_list[i]
                break
    return file_list


def is_not_keyword(str):
    keyword_list = ['local', 'exit', 'return', 'break', 'alias', 'bg', 'if', 'else', 'for', 'help', 'set', 'fi',
                    'while', 'done', 'exec']
    if str not in keyword_list:
        return True
    return False


def parse_sh(file_path, PATH_list):
    # open file
    try:
        f = open(file_path, mode='r')
    except:
        print("[error] open file error")
        exit(0)

    file_list = []

    # parse the file line by line
    content = f.readline()
    while (content):
        print("[zzcstalim] content: ", content)

        # try to find /bin/sh or /bin/bash
        if "#!" in content:
            file_list.append(content.replace('#!', '').replace('\n', ''))

        # find comments and delete
        re_match = re.findall(r'#.*', content)
        print("[zzcstalim] re_match: ", re_match)
        if re_match:
            content = content.replace(re_match[0], '')

        # try to delete $XXX/xxx/xxx
        re_match = re.findall(r'((\$[a-zA-Z0-9_]+){1}(/[a-z0-9-]+)+([\.][a-z]+)?)', content)
        if re_match:
            print("[zzcstalim] $XXX/xxx/xxx re_match: ", re_match)
            if i in range(len(re_match)):
                content = content.replace(re_match[i][0], " ")

        # try to find /xxx/xxx/xxx
        re_match = re.findall(r"((\/[a-z0-9-]+)+([\.][a-z]+)?)", content)
        if re_match:
            print("[zzcstalim] re_match: ", re_match)
            for i in range(len(re_match)):
                file_list.append(re_match[i][0])

        # try to find "set -- xxxx"
        re_match = re.findall(r'(set -- [a-z0-9-]+)', content)
        if re_match:
            print("[zzcstalim] re_match: ", re_match)
            file_list.append(re_match[0].replace('set -- ', ''))

        # try to find $(xxx)
        re_match = re.findall(r'((\$\()([a-z0-9]+))', content)
        if re_match:
            for i in range(len(re_match)):
                file_list.append(re_match[i][2])

        # try to find xxx(binary) yyyy
        re_match = re.findall(r'^\s*([a-z]+)\s+', content)
        if (re_match and is_not_keyword(re_match[0])):
            file_list.append(re_match[0])

        content = f.readline()

    f.close()
    file_list = find_absolute_path(file_list, PATH_list)
    return file_list


if (__name__ == '__main__'):
    print("[zzcstalim] parse_sh() test")
    print("[zzcstalim] argv: ", sys.argv)
    file_path = sys.argv[1]
    print("[zzcstalim] file_path: ", file_path)
    if (not is_sh_script_file(file_path)):
        print("[zzcstalim] %s is not sh file" % file_path)
    PATH = "/home/zzc/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/bin"  # need more process
    file_list = parse_sh(file_path, PATH.split(':'))
    print("[zzcstalim] parse result: ", file_list)
