import sys
import os

for i in range(len(sys.path)):
    if "ptrace" in sys.path[i]:
        del sys.path[i]
        break
sys.path[0], sys.path[-1] = sys.path[-1], sys.path[0]
sys.path.append(os.getcwd() + "/python_ptrace")

from python_ptrace import strace

sys.argv.append("/bin/bash")
sys.argv.append("/zzc.sh")
app = strace.SyscallTracer()
app.main()

print("pause")
