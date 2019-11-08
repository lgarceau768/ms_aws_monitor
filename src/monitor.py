import os, sys, subprocess

hostname = 'iotc-edbc3300-b4bb-4461-8328-e2d8bf17d7a9.azure-devices.net'

# returns True/False based on if the service is running
def getStatus(process):
    p = subprocess.Popen(['systemctl', 'is-active', process], stdout=subprocess.PIPE)
    (output, err) = p.communicate()
    output = output.decode('utf-8')
    if 'in-active' in output:
        return False
    else:
        return True

def nslookup(ip):
    p = subprocess.Popen(['nslookup', ip], stdout=subprocess.PIPE)
    (output, err) = p.communicate()
    print(output)


### Main Loop
nslookup(hostname)


