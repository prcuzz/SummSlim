import subprocess

exitcode, output = subprocess.getstatusoutput("echo $(pwd)")
print(output)
