import sys
import os
import subprocess
import re
import stat


# check if the file is elf file
def is_ELFfile(filepath):
    if (not os.path.exists(filepath)):
        print("is_ELFfile() file not exist")
        return False
    # 文件可能被损坏，捕捉异常
    try:
        FileStates = os.stat(filepath)
        FileMode = FileStates[stat.ST_MODE]
        if not stat.S_ISREG(FileMode) or stat.S_ISLNK(FileMode):  # 如果文件既不是普通文件也不是链接文件
            return False
        with open(filepath, 'rb') as f:
            header = (bytearray(f.read(4))[1:4]).decode(encoding="utf-8")
            # logger.info("header is {}".format(header))
            if header in ["ELF"]:
                # print header
                return True
    except UnicodeDecodeError as e:
        # logger.info("is_ELFfile UnicodeDecodeError {}".format(filepath))
        # logger.info(str(e))
        pass

    return False


def clear_file_list(file_list, PATH_list):
    file_list = list(set(file_list))
    for i in range(len(file_list)):
        # check if the file exists
        if (not os.path.exists(file_list[i])):
            file_list[i] = ''
        if (os.path.isdir(file_list[i])):
            file_list[i] = ''
        # ignore /dev/xxx
        if (re.match(r'(/dev)', file_list[i])):
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


def parse_binary(file_path, PATH_list):
    file_list = []

    # ldd find /xxx/xxxx
    status, output = subprocess.getstatusoutput("ldd %s" % file_path)
    re_match = re.findall(r"((\/[a-z0-9-_\.]+)+)", output)
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

    file_list = clear_file_list(file_list, PATH_list)
    return file_list


if (__name__ == '__main__'):
    print("[zzcstalim] parse_binary() test")
    print("[zzcstalim] argv: ", sys.argv)
    file_path = sys.argv[1]
    print("[zzcstalim] file_path: ", file_path)
    if (not is_ELFfile(file_path)):
        print("[zzcstalim] %s is not elf file" % file_path)
    PATH = "/home/zzc/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/bin"  # need more process
    file_list = parse_binary(file_path, PATH.split(':'))
    print("[zzcstalim] parse result: ", file_list)
