import os, sys, subprocess, datetime, shutil, time

def stopMs():
    command = ['systemctl', 'stop', 'msIot', '-l']
    output = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True).communicate()[0]
    
def startMs():
    command = ['systemctl', 'start', 'msIot', '-l']
    output = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True).communicate()[0]
    
def getMsStatus():
    command = ['systemctl', 'status', 'msIot']
    output = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True).communicate()[0]
    print(output)
    return output

def createFailLog(output):
    date = str(datetime.datetime.today().isoformat())
    fileName = 'msIot_stop_'+date+'.log'
    with open(fileName,'w') as logFile:
        for line in output:
            logFile.write(line.strip()+'\n')
        logFile.close()
    try:
        shutil.move(os.path.join('/home','User1','ms_aws_monitor','out',fileName), os.path.join('/home','User1','out'))
    except Exception as e:
        print('exception %s when moving %s' % (str(e), fileName))

def increaseTotalFailed():
    if not os.path.isfile('totalFails.txt'):
        with open('totalFails.txt', 'w') as file:
            today = str(datetime.datetime.today().isoformat())
            file.write(today+',1')
            file.close()
        return
    with open('totalFails.txt', 'r') as file:
        today = str(datetime.datetime.today().isoformat())
        lines = file.readlines()
        lines = lines.strip().split(',')
        todayThen = lines[0]
        amountFailed = lines[1]
        if todayThen != today:
            amountFailed = '1'
        else:
            if int(amountFailed) >= 5:
                fileName = 'ms_service_failed_max_'+today+'.log'
                with open(fileName, 'w') as file:
                    file.write('the ms iot serivce failed more than 5 times please see the log')
                    file.close()
                shutil.move(os.path.join('/home','User1','ms_aws_monitor','out',fileName), os.path.join('/home','User1','out'))
            else:
                with open('totalFails.txt','w') as file:
                    file.write(today+','+str(int(amountFailed)+1))
                    file.close()
                
def updateTextFile(hour):
    with open('timeInterval.txt', 'w') as file:
        file.write(str(hour))
        file.close()

def updateGit():
    os.system('cd /home/User1/connected-treatment-units/;git stash; git pull; cd /home/User1/ms_aws_monitor')

def removeLogsAnalytics():
    os.system('rm -rf /home/User1/aws-script/Analytics; rm -rf /home/User1/aws-script/Logs')

def checkTimeUpdate():
    hour = str(datetime.datetime.today().hour)
    fileName = 'timeInterval.txt'
    if not os.path.isfile(fileName):
        updateTextFile(hour)
        return hour
    else:
        hourThen = '0'
        with open(fileName, 'r') as file:
            lines = file.readlines()
            hourThen = lines[0].strip()
            file.close()
        if int(hourThen) != int(hour):
            # check the status and update the git
            stopMs()
            output = str(getMsStatus())
            print(output)
            failed = False
            for line in output.split('\n'):                
                if 'failed' in line.lower():    
                    failed = True
            if failed:
                createFailLog(output)
                increaseTotalFailed()
            updateGit()
            startMs()        
            removeLogsAnalytics()    
            updateTextFile(hour)

while True:
    checkTimeUpdate()
    time.sleep(5)
