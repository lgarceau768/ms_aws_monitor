import os, sys, subprocess, logging, socket, datetime, time, psutil
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
        for file in os.listdir('/home/User1/msV2/logs/'):
            if file.endswith('.log'):
                #print(file)
                if 'msLog' in file:
                    with open(os.path.join('/home/User1/msV2/logs', file), 'r') as readFile:
                        lines = readFile.readlines()
                        for line in lines:
                            line = line.strip()
                            logging.info(line.lower())
                            error = False
                            if 'error' in line.lower():
                                split = line.lower().split(' ')
                                if len(split) >= 3:
                                    if 'error' in split[2]:
                                        error = True
                            elif 'disconnected' in line.lower():
                                error = True
                            if error:
                                logging.info('Error in ms log: '+line.lower())
                                return False
                            return True
        return True
    return getStatus('msIot')


def removeOldFiles():
    path = '/home/User1/aws-script/'
    try:
        os.system('rm -rf %s' % os.path.join(path, 'Logs'))
        os.system('rm -rf %s' % os.path.join(path, 'Analytics'))
    except Exception as e:
        logging.error('Exception %s in removeOldFiles' % str(e))

def gitPull():
    cwd = os.getcwd()
    cd = 'cd /home/User1/msV2; git stash;'
    end = 'cd %s ' % cwd
    pull = 'git pull https://lgarceau768:Spook524*@github.com/lgarceau768/msV2.git > /home/User1/ms_aws_monitor//src/logs/%s_%s_pullLog.log;' % (deviceName, datetime.datetime.now().isoformat())    
    os.system(cd+pull+end)

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
    os.system('/home/User1/emsa/cleariptables')
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

def recordDay():
    # will just output datetime.datetime.today() to the text file
    with open('/home/User1/ms_aws_monitor/data/update.txt', 'w') as file:
        date = str(datetime.datetime.today()).split(' ')[0]
        #print(date)
        file.write(date+'\n')
        file.close()

def checkForUpdate():
    line = ''
    with open('/home/User1/ms_aws_monitor/data/update.txt', 'r') as file:
        if len(file.readlines()) > 1:
            line = file.readlines()[0].replace('\n', '').split(' ')[0]
    today = str(datetime.datetime.today()).split(' ')[0]
    #print(line+ '   vs: '+today)
    if line in today:
        return False
    else:
        return True

### Main Loop
# pull and update iptabl es once a day
startTime = time.time()/60.0
interval = 10
returnVal = updateIpTables()
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
                os.system('systemctl status msIot > /home/User1/out/%s_%s_msFail.log' % (deviceName, str(datetime.datetime.today())))
                os.system('systemctl restart msIot')
            
