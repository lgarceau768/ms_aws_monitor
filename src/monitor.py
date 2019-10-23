import os, sys, subprocess

# funciton to list runnig processes
def getMsStatus():
    command = ['systemctl', 'status', 'msIot', '-l']
    output = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True).communicate()[0]
    print(output)

getMsStatus()    