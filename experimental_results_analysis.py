import os
import queue
import subprocess

import some_general_functions


def get_file_quantity(folder: str):
    """
    获取文件夹下文件的总数量
    最初参考了：https://segmentfault.com/a/1190000019120755，但运行时会闪退
    """

    status, output = subprocess.getstatusoutput("ls -lR %s | grep \"^-\" | wc -l" % folder)
    return output


def get_sys_binary_file_quantity(dir_path: str) -> int:
    """
    获取系统二进制文件的总数量
    """

    cnt = 0

    status, output = subprocess.getstatusoutput("ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "bin"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    status, output = subprocess.getstatusoutput("ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "sbin"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    status, output = subprocess.getstatusoutput("ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "usr/bin"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    status, output = subprocess.getstatusoutput("ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "usr/sbin"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    status, output = subprocess.getstatusoutput(
        "ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "usr/local/bin"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    status, output = subprocess.getstatusoutput(
        "ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "usr/local/sbin"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    return cnt


def get_shared_library_file_quantity(dir_path: str) -> int:
    cnt = 0

    status, output = subprocess.getstatusoutput(
        "ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "lib/x86_64-linux-gnu"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    status, output = subprocess.getstatusoutput(
        "ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "usr/lib/x86_64-linux-gnu"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    return cnt


def get_file_quantity_in_usr_include(dir_path):
    cnt = 0

    status, output = subprocess.getstatusoutput(
        "ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "usr/include"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    return cnt


def get_perl_file_quantity(dir_path):
    cnt = 0

    status, output = subprocess.getstatusoutput(
        "ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "usr/lib/x86_64-linux-gnu/perl-base"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    status, output = subprocess.getstatusoutput(
        "ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "usr/share/perl"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    status, output = subprocess.getstatusoutput(
        "ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "usr/lib/x86_64-linux-gnu/perl"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    return cnt


def get_python_file_quantity(dir_path):
    cnt = 0

    status, output = subprocess.getstatusoutput(
        "ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "/usr/local/lib/python*"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    status, output = subprocess.getstatusoutput(
        "ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "usr/lib/python*"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    status, output = subprocess.getstatusoutput(
        "ls -lR %s | grep \"^-\" | wc -l" % os.path.join(dir_path, "usr/lib64/python*"))
    if status == 0 and "zzc" not in output:
        cnt = cnt + int(output)

    return cnt


def compare_file_count_differences():
    analysis_path = os.path.join(os.getcwd(), "image_files")
    result_file_path = os.path.join(os.getcwd(), "experimental_results_analysis", "compare_file_count_differences")
    for each_dir in os.listdir(analysis_path):
        dir_path = os.path.join(analysis_path, each_dir)
        if "directory" in some_general_functions.get_file_type(dir_path) and os.path.exists(
                dir_path) and os.path.exists(dir_path + ".zzcslim"):
            with open(result_file_path, "a") as fd:
                fd.write(each_dir + ": " + str(get_file_quantity(dir_path)) + "\n")
                fd.write(each_dir + ".zzcslim: " + str(get_file_quantity(dir_path + ".zzcslim")) + "\n")
                fd.write("difference value: " + str(
                    int(get_file_quantity(dir_path)) - int(get_file_quantity(dir_path + ".zzcslim"))) + "\n")
                fd.write("sys binary file quantity in %s: %d\n" % (dir_path, get_sys_binary_file_quantity(dir_path)))
                fd.write("sys binary file quantity in %s: %d\n" % (
                    dir_path + ".zzcslim", get_sys_binary_file_quantity(dir_path + ".zzcslim")))
                fd.write(
                    "shared library file quantity in %s: %d\n" % (dir_path, get_shared_library_file_quantity(dir_path)))
                fd.write("shared library file quantity in %s: %d\n" % (
                    dir_path + ".zzcslim", get_shared_library_file_quantity(dir_path + ".zzcslim")))
                fd.write("\n")
                print(each_dir)
        elif "directory" in some_general_functions.get_file_type(dir_path) and os.path.exists(dir_path):
            for child_dir in os.listdir(dir_path):
                child_dir_path = os.path.join(dir_path, child_dir)
                if "directory" in some_general_functions.get_file_type(child_dir_path) and os.path.exists(
                        child_dir_path) and os.path.exists(child_dir_path + ".zzcslim"):
                    with open(result_file_path, "a") as fd:
                        fd.write(each_dir + "/" + child_dir + ": " + str(get_file_quantity(child_dir_path)) + "\n")
                        fd.write(each_dir + "/" + child_dir + ".zzcslim: " + str(
                            get_file_quantity(child_dir_path + ".zzcslim")) + "\n")
                        fd.write(
                            "difference value: " + str(int(get_file_quantity(child_dir_path)) - int(get_file_quantity(
                                child_dir_path + ".zzcslim"))) + "\n")
                        fd.write("sys binary file quantity in %s: %d\n" % (
                            child_dir_path, get_sys_binary_file_quantity(child_dir_path)))
                        fd.write("sys binary file quantity in %s: %d\n" % (
                            child_dir_path + ".zzcslim", get_sys_binary_file_quantity(child_dir_path + ".zzcslim")))
                        fd.write("shared library file quantity in %s: %d\n" % (
                            child_dir_path, get_shared_library_file_quantity(child_dir_path)))
                        fd.write("shared library file quantity in %s: %d\n" % (
                            child_dir_path + ".zzcslim", get_shared_library_file_quantity(child_dir_path + ".zzcslim")))
                        fd.write("\n")
                        print(each_dir, "/", child_dir)


def find_useless_code_file():
    analysis_path = os.path.join(os.getcwd(), "image_files")
    result_file_path = os.path.join(os.getcwd(), "experimental_results_analysis", "find_useless_code_file")
    for each_dir in os.listdir(analysis_path):
        dir_path = os.path.join(analysis_path, each_dir)
        if "directory" in some_general_functions.get_file_type(dir_path) and os.path.exists(
                dir_path) and os.path.exists(dir_path + ".zzcslim"):
            with open(result_file_path, "a") as fd:
                fd.write(
                    "file quantity in usr/include in %s: %d\n" % (dir_path, get_file_quantity_in_usr_include(dir_path)))
                fd.write(
                    "perl file quantity in %s: %d\n" % (dir_path, get_perl_file_quantity(dir_path)))
                fd.write("python file quantity in %s: %d\n" % (dir_path, get_python_file_quantity(dir_path)))
                fd.write("\n")
                print(each_dir)
        elif "directory" in some_general_functions.get_file_type(dir_path) and os.path.exists(dir_path):
            for child_dir in os.listdir(dir_path):
                child_dir_path = os.path.join(dir_path, child_dir)
                if "directory" in some_general_functions.get_file_type(child_dir_path) and os.path.exists(
                        child_dir_path) and os.path.exists(child_dir_path + ".zzcslim"):
                    with open(result_file_path, "a") as fd:
                        fd.write("file quantity in usr/include in %s: %d\n" % (
                            child_dir_path, get_file_quantity_in_usr_include(child_dir_path)))
                        fd.write(
                            "perl file quantity in %s: %d\n" % (child_dir_path, get_perl_file_quantity(child_dir_path)))
                        fd.write("python file quantity in %s: %d\n" % (
                            child_dir_path, get_python_file_quantity(child_dir_path)))
                        fd.write("\n")
                        print(each_dir, "/", child_dir)


def organize_and_summarize_important_path():
    analysis_path = os.path.join(os.getcwd(), "image_files")
    result_file_path = os.path.join(os.getcwd(), "experimental_results_analysis",
                                    "organize_and_summarize_important_path")
    cmd_and_entrypoint_image_list = []
    volume_image_list = []
    workdir_image_list = []
    PATH_image_list = []
    reserved_paths_in_images = []

    for each_dockerfile in os.listdir(analysis_path):
        if "dockerfile" in each_dockerfile:
            image_name = each_dockerfile.replace("_dockerfile", "").replace("_", "/")
            with open(os.path.join(analysis_path, each_dockerfile)) as fd:
                while True:
                    line = fd.readline()
                    if not line: break
                    if ("CMD" in line or "ENTRYPOINT" in line) and (
                            ".conf" in line or ".yaml" in line or ".yml" in line):
                        cmd_and_entrypoint_image_list.append(image_name)
                        reserved_paths_in_images.append(": ".join([image_name, line]))
                    if "VOLUME" in line:
                        volume_image_list.append(image_name)
                        reserved_paths_in_images.append(": ".join([image_name, line]))
                    if "WORKDIR" in line:
                        workdir_image_list.append(image_name)
                        reserved_paths_in_images.append(": ".join([image_name, line]))
                    if "PATH" in line and "ENV" in line:
                        PATH = line[line.find('"') + 1: line.find('"', line.find('"') + 1)]
                        PATH_list = PATH.split(":")
                        for each_PATH in PATH_list:
                            if each_PATH not in ["/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin", "/sbin",
                                                 "/bin"]:
                                PATH_image_list.append(image_name)
                                reserved_paths_in_images.append(": ".join([image_name, line]))

    with open(result_file_path, "a") as fd:
        fd.write("cmd_and_entrypoint_image_list: %s\n" % cmd_and_entrypoint_image_list)
        fd.write("volume_image_list: %s\n" % volume_image_list)
        fd.write("workdir_image_list: %s\n" % workdir_image_list)
        fd.write("PATH_image_list: %s\n" % PATH_image_list)
        fd.write("reserved_paths_in_images: %s\n" % reserved_paths_in_images)


if __name__ == "__main__":
    # print(get_file_quantity("/home/zzc/Desktop/zzc/zzcslim/image_files/balena"))
    # print(get_shared_library_file_quantity("/home/zzc/Desktop/zzc/zzcslim/image_files/hitch"))
    compare_file_count_differences()
    find_useless_code_file()
    organize_and_summarize_important_path()
