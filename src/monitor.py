import os, sys, subprocess

p = subprocess.Popen(['systemctl', 'is-active', 'msIot'], stdout=subprocess.PIPE)
(output, err) = p.communicate()
output = output.decode('utf-8')

print(output)

