import os
import subprocess
import time

stderr_output = open("./stderr_output", "w")
pid = os.popen('ps -ef | grep containerd ').readlines()[0].split()[1]
print(pid)

p = subprocess.Popen(["strace", "-f", "-e", "trace=file", "-p", pid], stderr=stderr_output)
# p = subprocess.Popen(["strace", "-f", "-p", pid], stderr=stderr_output)

p1 = subprocess.Popen(["docker", "run", "--rm", "mongo"])
time.sleep(1.5)
p1.terminate()

time.sleep(0.5)
p.terminate()

stderr_output.close()
stderr_output = open("./stderr_output", "r")
line = stderr_output.readline()
while line:
    print(line)
    line = stderr_output.readline()
