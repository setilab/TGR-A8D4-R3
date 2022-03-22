#!/bin/bash

# TGR installation script

TGRDIR="/home/pi/tgr"

if [ ! -f /home/pi/.tgr.installer.sys-update.complete ]; then
    # update/upgrade system
    echo "*** Updating & upgrading the base system ***"
    sudo apt update
    sudo apt upgrade

    touch /home/pi/.tgr.installer.sys-update.complete
    sudo reboot
fi

if [ ! -f /home/pi/.tgr.installer.docker.complete ]; then
    # install os packages
    echo "*** Installing OS packages ***"
    #sudo apt install ntp
    #sudo apt install ntpstat
    #sudo apt install python3-urwid
    #sudo apt install libpq5

    # install python packages
    echo "*** Installing Python packages ***"
    sudo pip3 install cherrypy
    sudo pip3 install ws4py
    sudo pip3 install routes
    sudo pip3 install redis
    sudo pip3 install requests
    sudo pip3 install websocket
    sudo pip3 install websocket-client

    # download Docker installation script
    #echo "*** Installing Docker ***"
    #cd ~/Downloads
    #curl -fsSL https://get.docker.com -o get-docker.sh

    # install/configure Docker
    #sudo bash ./get-docker.sh
    #sudo usermod -aG docker $(whoami)
    #touch /home/pi/.tgr.installer.docker.complete
    #echo "*** Rebooting system post-Docker ***"
    #sudo reboot
fi

echo "*** Configuring system ***"
sudo mkdir /usr/share/fonts/truetype/la-solid-900
sudo cp $TGRDIR/install/la-solid-900.ttf /usr/share/fonts/truetype/la-solid-900

# replace config.txt
#sudo cp -p /boot/config.txt /boot/config.txt.orig
#sudo cp $TGRDIR/install/config.txt /boot/config.txt

# replace cmdline.txt
#sudo cp -p /boot/cmdline.txt /boot/cmdline.txt.orig
#sudo cat $TGRDIR/install/cmdline.txt /boot/cmdline.txt

# configure dhcpcd
sudo cp -p /etc/dhcpcd.conf /etc/dhcpcd.conf.orig
sudo cp $TGRDIR/install/dhcpcd.conf /etc/dhcpcd.conf

# configure crontab for pi
echo "*** Configure pi's crontab ***"
crontab $TGRDIR/install/crontab.pi

#docker login
$TGRDIR/containers/redis/Docker.build
$TGRDIR/containers/redis/Docker.run
$TGRDIR/containers/ocmodule/Docker.build
$TGRDIR/containers/ocmodule/Docker.run
$TGRDIR/containers/api/Docker.build
$TGRDIR/containers/api/Docker.run

# configure systemd services
echo "*** Install systemd services ***"
cd $TGRDIR/lib/systemd
sudo cp *.service /lib/systemd/system

echo "*** Enable systemd services ***"
UNIT_FILES=`sudo systemctl list-unit-files --no-legend tgr.* | awk '{ print $1 }'`
for f in $UNIT_FILES; do
    sudo systemctl enable $f
done

# populate Redis keys
echo "*** Populate Redis keys ***"
python3 $TGRDIR/install/init-redis-keys.py

# last, reboot the system
#sudo reboot
