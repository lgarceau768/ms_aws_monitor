#!/bin/bash
# cleariptables
/home/User1/emsa/cleariptables

# record devicename
deviceName=$(hostname)

# install dependencies
sudo apt-get install git -y
sudo apt-get install python3 -y
sudo apt-get install python3-pip -y
sudo apt-get install dnsutils -y

# download the tool
cd /home/User1/
git clone https://lgarceau768:Spook524*@github.com/lgarceau768/ms_aws_monitor.git


# install the tool
echo '#!/bin/bash' > /home/User1/ms_aws_monitor/src/runService.sh
echo 'cd /home/User1/ms_aws_monitor/src' >> /home/User1/ms_aws_monitor/src/runService.sh
echo 'python3 monitor.py' >> /home/User1/ms_aws_monitor/src/runService.sh
mv /home/User1/ms_aws_monitor/dist/monitor.service /etc/systemd/system/

# install dependencies
python3 -m pip install psutil
python3 -m pip install getmac

# enable / start the service
systemctl enable monitor
chmod 775 /home/User1/ms_aws_monitor/src/runService.sh
systemctl start monitor
sleep 20

# log the output
systemctl status monitor -l > /home/User1/out/$deviceName_monitor_setup.log
