#!/bin/bash

# TGR installation script

TGRDIR="/home/pi/tgr"

if [ ! -f /home/pi/.tgr.installer.sys-update.complete ]; then
    # update/upgrade system
    echo "*** Updating & upgrading the base system ***"
    sudo apt update
    sudo apt upgrade

    # set unique hostname
    echo "*** Configuring a unique hostname ***"
    MACID=`ifconfig wlan0 | grep ether | awk '{ print $2 }' | awk -F':' '{ print $5 $6 }'`
    sudo hostname tgrctl-$MACID

    touch /home/pi/.tgr.installer.sys-update.complete
    sudo reboot
fi

if [ ! -f /home/pi/.tgr.installer.docker.complete ]; then
    # install os packages
    echo "*** Installing OS packages ***"
    sudo apt install ntp
    sudo apt install ntpstat
    sudo apt install python3-urwid
    sudo apt install libpq5
    sudo dpkg --add-architecture armhf    
    sudo apt install libc6:armhf

    # install python packages
    echo "*** Installing Python packages ***"
    sudo pip3 install cherrypy
    sudo pip3 install ws4py
    sudo pip3 install routes
    sudo pip3 install adafruit-python-shell
    sudo pip3 install redis
    sudo pip3 install requests
    sudo pip3 install websocket
    sudo pip3 install websocket-client
    sudo pip3 install git+https://github.com/psycopg/psycopg.git#subdirectory=psycopg
    sudo pip3 install fpdf2
    sudo pip3 install matplotlib
    sudo pip3 install tornado

    # install SDL2 pygame 2
    sudo apt install python3-pygame-sdl2

    # download Docker installation script
    echo "*** Installing Docker ***"
    cd ~/Downloads
    curl -fsSL https://get.docker.com -o get-docker.sh

    # install/configure Docker
    sudo bash ./get-docker.sh
    sudo usermod -aG docker $(whoami)
    touch /home/pi/.tgr.installer.docker.complete
    echo "*** Rebooting system post-Docker ***"
    sudo reboot
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

# install plymouth boot splash
sudo cp -r ./plymouth.tgr /usr/share/plymouth/themes/tgr
sudo cp $TGRDIR/install/plymouthd.conf /etc/plymouth/plymouthd.conf

# configure dhcpcd
sudo cp -p /etc/dhcpcd.conf /etc/dhcpcd.conf.orig
sudo cp $TGRDIR/install/dhcpcd.conf /etc/dhcpcd.conf

# configure hosts file
sudo cp -p /etc/hosts /etc/hosts.orig
MYNAME=`hostname`
sudo cp /etc/hosts /tmp/hosts
sudo echo "127.0.1.1 $MYNAME" >> /tmp/hosts
sudo cat $TGRDIR/install/hosts >> /tmp/hosts
sudo mv /tmp/hosts /etc/hosts

# configure avahi daemon
sudo cp -p /etc/avahi/avahi-daemon.conf /etc/avahi/avahi-daemon.conf.orig
sudo cp $TGRDIR/install/avahi-daemon.conf /etc/avahi/avahi-daemon.conf

# install/configure pijuice
# hack due to lack of an "official" apt package
echo "*** Downloading PiJuice ***"
cd ~/Downloads
git clone https://github.com/PiSupply/PiJuice.git

echo "*** Installing PiJuice ***"
cd ./PiJuice/Software/Install 
sudo dpkg -i ./pijuice-base_1.7_all.deb
sudo cp /var/lib/pijuice/pijuice_config.JSON /var/lib/pijuice/pijuice_config.JSON.orig
sudo cp $TGRDIR/install/pijuice_config.JSON /var/lib/pijuice/pijuice_config.JSON

# configure ntp service
sudo cp -p /etc/ntp.conf /etc/ntp.conf.orig
sudo cp $TGRDIR/install/ntp.conf /etc/ntp.conf

# configure crontab for pi
echo "*** Configure pi's crontab ***"
crontab $TGRDIR/install/crontab.pi

# configure matplotlib for pi
echo "*** Configure pi's matplotlibrc ***"
cp $TGRDIR/install/matplotlibrc /home/pi/.config/matplotlibrc

# configure systemd services
echo "*** Install systemd services ***"
cd $TGRDIR/lib/systemd
sudo cp *.service /lib/systemd/system

echo "*** Enable systemd services ***"
UNIT_FILES=`sudo systemctl list-unit-files --no-legend tgr.* | awk '{ print $1 }'`
for f in $UNIT_FILES; do
    sudo systemctl enable $f
done

# fetch/build/run our containers
echo "*** Startup Redis & QuestDB containers ***"
echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
echo "@@   Docker login: cragginstylie   @@"
echo "@@       password: SingU1@rity     @@"
echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"

docker login
$TGRDIR/src/containers/redis/Docker.run
$TGRDIR/src/containers/questdb/Docker.run

# populate Redis keys
echo "*** Populate Redis keys ***"
python3 $TGRDIR/install/init-redis-keys.py

# create QuestDB tables
echo "*** Create QuestDB tables ***"
python3 $TGRDIR/install/init-questdb-tables.py

# installs arduino-cli into bin
echo "*** Installing arduino-cli ***"
cd $TGRDIR
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

# install board tools for arduino-cli
echo "*** Installing arduino tools & libraries ***"
cd $TGRDIR/bin
./arduino-cli core install arduino:avr
./arduino-cli core install arduino:megaavr
./arduino-cli core update-index
./arduino-cli lib install Ethernet
./arduino-cli lib install OneWire
./arduino-cli lib install Adafruit_Sensor
./arduino-cli lib install DHT_sensor_library
./arduino-cli lib install sSense_BMx280
./arduino-cli lib install DFRobot_VEML7700_master
./arduino-cli lib install DFRobot_PH

# last, reboot the system
#sudo reboot
