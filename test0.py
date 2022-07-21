import os
import subprocess
import time

stderr_output = open("./stderr_output", "w")
pid = os.popen('ps -ef | grep containerd ').readlines()[0].split()[1]
print(pid)
# p = subprocess.Popen(["strace", "-f", "-e", "trace=file", "-p", pid], stdout=stderr_file)
p = subprocess.Popen(["strace", "-f", "-p", pid], stderr=stderr_output)
time.sleep(0.5)
p.terminate()
stderr_output.close()
stderr_output = open("./stderr_output", "r")
print(stderr_output.readlines())
