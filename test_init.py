import sys
import os
import subprocess

p = subprocess.Popen(["uv", "run", "gitty", "init"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
out, err = p.communicate(input="Lucas\nlucas@gitty.org\n")
print(out)
