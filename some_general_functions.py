import sys
import os
import subprocess
import magic


# Check whether the file exists (Temporarily abandoned)
def is_file_exist(file, image_name, PATH_list=None):
    if PATH_list == None:
        return os.path.exists(os.getcwd() + "/image_files" + "/" + image_name.replace("/", "-") + "/" + file)
    else:
        for i in range(len(PATH_list)):
            if os.path.exists(os.getcwd() + PATH_list[i] + "/" + file) == True:
                return True
        return False


# Determines whether the file exists and gets its absolute path
def get_the_absolute_path(file, image_name, PATH_list):
    if file == None:
        return False, None

    file = file.replace("'", "")  # get rid of the single quotes
    file = file.replace("\n", "")  # get rid of the line break
    if "/" in file:  # If this is already a half-complete path
        file_path = os.getcwd() + "/image_files/" + image_name.replace("/", "-") + file
        if os.path.exists(file_path) == True:
            return True, file_path
        else:
            return False, None
    elif ("/" not in file and PATH_list == None):
        print("[error]get_the_absolute_path(): process file %s without PATH_list" % file)
        pass
    else:  # If this is just a file name
        for i in range(len(PATH_list)):
            file_path = os.getcwd() + "/image_files/" + image_name.replace("/", "-") + PATH_list[i] + "/" + file
            if os.path.exists(file_path) == True:
                return True, file_path

    return False, None


# Gets the soft link target of the file
def get_linked_file(file):
    status, output = subprocess.getstatusoutput("file %s" % file)
    if status != 0:
        return None
    elif status == 0 and "symbolic link to" in output:
        return output.split(" ")[-1]


# Determine the file type
def get_file_type(file):
    if os.path.exists(file) == False:
        return None
    else:
        return magic.from_file(file)


# Gets the soft link target of the file
def get_link_target_file(file_path, image_name):
    if file_path == None or os.path.islink(file_path) == False:
        return None

    status, output = subprocess.getstatusoutput("file %s" % file_path)
    if "symbolic link" in output:
        target_file = (output.split(" "))[-1]
        if os.path.isabs(target_file):
            return os.getcwd() + "/image_files/" + image_name.replace("/", "-") + target_file
        else:
            return os.getcwd() + "/image_files/" + image_name.replace("/", "-") + os.path.dirname(
                file_path) + "/" + target_file
    return None


if __name__ == "__main__":
    print(get_link_target_file(
        "/home/zzc/Desktop/zzc/zzcslim/image_files/mongo.zzcslim/lib/x86_64-linux-gnu/libwind.so.0", "mongo"))
    # print(magic.from_file("/home/zzc/Desktop/zzc/zzcslim/image_files/mongo.zzcslim/etc/os-release"))
