import os, sys, subprocess, logging, socket, datetime, time, psutil, urllib.request, json
from logging.handlers import RotatingFileHandler

# program variables
hostname = 'iotc-edbc3300-b4bb-4461-8328-e2d8bf17d7a9.azure-devices.net'

# setup logging
logPath = '/home/User1/ms_aws_monitor/src/logs/'
outPath = '/home/User1/out/'
deviceName = socket.gethostname()
fileName = '%s_%s_monitor.log' % (deviceName, datetime.datetime.now().isoformat())
fileName = os.path.join(logPath, fileName)

def moveOldLogs():
    for file in os.listdir(logPath):
        if file.endswith('.log') and file != fileName:
            try:
                os.system('mv %s %s' % (os.path.join(logPath, file), os.path.join(outPath, file)))
            except Exception as e:
                logging.error('Exception %s when moving %s' % (str(e), file)) 

# initial moving
moveOldLogs()
logging.basicConfig(filename=fileName, filemode='w', level=logging.DEBUG, format='%(asctime)s %(levelname)s\t %(message)s')
handler = RotatingFileHandler(fileName, maxBytes=10000000)
logging.getLogger().addHandler(handler)


# returns True/False based on if the service is running
def getStatus(process):
    p = subprocess.Popen(['systemctl', 'is-active', process], stdout=subprocess.PIPE)
    (output, err) = p.communicate()
    output = output.decode('utf-8')
    if 'inactive' in output:
        logging.info('Process %s is in-active' % process)
        return False
    else:
        logging.info('Process %s is active' % process)
        return True

def nslookup(ip):
    p = subprocess.Popen(['nslookup', ip], stdout=subprocess.PIPE)
    (output, err) = p.communicate()
    output = output.decode('utf-8')
    output = output.strip().split('Address: ')
    try:
        logging.info('MS IP: '+output[len(output)-1])
        return output[len(output)-1].strip()
    except Exception as e:
        logging.error('Exception %s in nslookup' % str(e))
    
def getMsStatus():
    if getStatus('msIot'):
        logging.info('getting the status from log file')
        for file in os.listdir('/home/User1/msV2/logs/'):
            file = file.strip()
            logging.info(file)
            if 'msLog' in file:
                logging.info('past first')
                with open(os.path.join('/home/User1/msV2/logs', file), 'r') as readFile:
                    logging.info('reading the file')
                    lines = readFile.readlines()
                    for line in lines:
                        #logging.info(line.lower())
                        error = False                        
                        if 'ProtocolClientError'.lower() in line.lower():
                            error = True
                        if 'out of memory' in line.lower():
                            error = True
                        if 'error' in line.lower():
                            split = line.lower().split(' ')
                            if len(split) >= 3:
                                if 'error' in split[2]:
                                    error = True
                        elif 'disconnected' in line.lower():
                            if 'with result code: 1' in line.lower():
                                error = False
                            else:
                                error = True
                        if error:
                            logging.info('Error in ms log: '+line.lower())
                            return False
        return getStatus('msIot')
    return getStatus('msIot')

def removeOldFiles():
    path = '/home/User1/aws-script/'
    try:
        os.system('rm -rf %s' % os.path.join(path, 'Logs'))
        os.system('rm -rf %s' % os.path.join(path, 'Analytics'))
    except Exception as e:
        logging.error('Exception %s in removeOldFiles' % str(e))

def notAllNumbers(ip):
    # given an ip address remove .s
    ip = ip.replace('.','').strip()
    numbers = ['0','1','2','3','4','5','6','7','8','9']
    for char in ip:
        if char not in numbers:
            print(char)
            return False
    return True

def updateIpTables():
    os.system('iptables -F INPUT; iptables -F FORWARD; iptables -F OUTPUT; iptables -P INPUT ACCEPT; iptables -P OUTPUT ACCEPT; iptables -P FORWARD ACCEPT')
    ip = nslookup(hostname)
    print('ip: %s' % ip)
    if not notAllNumbers(ip):
        os.system('iptables-restore < /etc/iptables/rules.v4')
        os.system('echo %s > /home/User1/out/%s_NSLOOKUPFAIL.log' % (datetime.datetime.now(), socket.gethostname()))
        return False
    #   print(ip)
    ruleOut = '\n-A OUTPUT -d %s -j ACCEPT\n' % ip
    ruleIn = '-A INPUT -s %s -j ACCEPT\n' % ip
    # copy rules.v4 file
    # stop ms and aws services
    os.system('systemctl stop msIot')
    os.system('systemctl stop awsScript')

    os.system('cp base.v4 rules.txt')
    with open('rules.txt', 'a') as rulesFile:
        rulesFile.write(ruleOut)
        rulesFile.write(ruleIn)
        otherRules = pullRemoteAws()
        for rule in otherRules:
            rulesFile.write(rule)
        rulesFile.write('COMMIT\n')
        rulesFile.close()

    # set iptables config to this file
    os.system('mv -f rules.txt /etc/iptables/rules.v4')

    # restart msService    
    os.system('iptables-restore < /etc/iptables/rules.v4')
    os.system('systemctl start msIot')
    os.system('systemctl start awsScript')
    os.system('iptables -L > /home/User1/ms_aws_monitor/src/logs/%s_%s_iptables.log' % (deviceName, datetime.datetime.now().isoformat()))
    return True

def downloadFile():
    url = 'https://ip-ranges.amazonaws.com/ip-ranges.json'
    response = urllib.request.urlopen(url)
    data = json.loads(response.read().decode())
    return data

def pullIps(data):
    realData = data['prefixes']
    ip = []
    for item in realData:
        if 'S3' in item['service']:
            try:
                ip.append(item['ip_prefix'])
            except:
                # just is an ipv6
                pass
    return ip

def printAllIps(data):
    for item in data:
        print(item)

def createRules(ips):
    rules = []
    for item in ips:
        ip = item.strip()
        ruleOut = '\n-A OUTPUT -d %s -j ACCEPT\n' % ip
        ruleIn = '-A INPUT -s %s -j ACCEPT\n' % ip
        rules.append(ruleIn)
        rules.append(ruleOut)
    return rules

def pullRemoteAws():
    list = 'proxy50.rt3.io p50.rt3.io proxy51.rt3.io p51.rt3.io proxy53.remot3.it proxy55.remot3.it p55.rt3.io proxy2.remot3.it proxy6.remot3.it proxy13.remot3.it proxy15.rt3.io p15.rt3.io proxy16.rt3.io p16.rt3.io proxy17.rt3.io p17.rt3.io proxy18.remot3.it p18.rt3.io proxy19.remot3.it p19.rt3.io proxy21.remot3.it p21.rt3.io'.split(' ')
    ips = []
    for hostname in list:
        ip = nslookup(hostname)
        if notAllNumbers(ip):
            # the ip is valid
            ips.append(ip)
    rules = createRules(ips)
    awsRules = pullIps(downloadFile())
    awsRules = createRules(awsRules)
    for item in awsRules:
        if item not in rules:
            rules.append(item)
    return rules
    
        
            


### Main Loop

# need to check if the device is connected to the internet
os.system('/home/User1/emsa/cleariptables')
internetActive = False
while not internetActive:
    try:
        urllib.request.urlopen('http://216.58.192.142')
        internetActive = True
    except urllib.URLError as err:
        internetActive = False

# pull and update iptables once a day
startTime = time.time()/60.0
interval = 10
time.sleep(120) # wait a minute after boot up
os.system('iptables -F INPUT; iptables -F FORWARD; iptables -F OUTPUT; iptables -P INPUT ACCEPT; iptables -P OUTPUT ACCEPT; iptables -P FORWARD ACCEPT')
os.system('iptables -L > /home/User1/iptablesTest.txt')
returnVal = updateIpTables()
#returnVal = True
print(returnVal)
if returnVal:
    removeOldFiles()
    while True:
        currTime = time.time()/60.0
        delta = abs(startTime-currTime)

    
        if delta >= interval:
            startTime = currTime
            
            state = getMsStatus()
            logging.info('Ms Status: '+str(state))
            if not state:
                logging.info('Restarting')
                timestamp = datetime.datetime.now()
                year = str(timestamp.year)
                month = str(timestamp.month)
                day = str(timestamp.day)
                hour = str(timestamp.hour)
                minute = str(timestamp.minute)
                ts = str(day+month+year+hour+minute)
                os.system('systemctl status msIot > /home/User1/out/%s_%s_msFail.log' % (deviceName, ts))
                os.system('systemctl restart msIot')
            
