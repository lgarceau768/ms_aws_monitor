#!/bin/bash
/home/User1/emsa/cleariptables
deviceName=$(hostname)
cd /home/User1/
git clone https://lgarceau768:Spook524*@github.com/lgarceau768/ms_aws_monitor.git
tr -d '\15\32' < /home/User1/ms_aws_monitor/src/runService.sh > /home/User1/ms_aws_monitor/src/runService.sh
mv /home/User1/ms_aws_monitor/src/monitor.service /etc/systemd/system/
systemctl enable monitor
systemctl start monitor
chmod 775 /home/User1/ms_aws_monitor/src/runService.sh
sleep 20
systemctl status monitor -l > /home/User1/out/$deviceName_monitor_setup.log
