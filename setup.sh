#!/usr/bin/env bash

echo
echo "###############################################"
echo "Thank you for using the Onbox Assistant Demo App"
echo "This script will set up the environment to run the app"
echo "###############################################"
echo

echo "Press Enter to continue..."
read confirm

echo "Please enter the NAMESERVER : "
read NAMESERVER

# configure nameserver
echo "nameserver " $NAMESERVER | sudo tee --append /etc/resolv.conf

# pip install required python libraries
sudo -E pip install --upgrade pip
sudo -E pip install urllib3[secure]
sudo -E pip install requests
sudo -E pip install ciscosparkapi
sudo -E pip install pyCli

# create a folder to store scripts in
#mkdir /bootflash/scripts

wget "https://raw.githubusercontent.com/clintmann/onbox_assistant/master/onbox_assistant_SparkAlerts.py" "/bootflash/scripts/"

echo "Please enter the IP ADDRESS used to test for connectivity : "
read GATEWAY_IP

echo "Please enter the SPARK AUTHENTICATION TOKEN : "
read TOKEN

echo "Please enter the EMAIL ADDRESS to Send to : "
read EMAIL_ADDR

sed -i "s/<GATEWAY_IP>/$GATEWAY_IP/"  /bootflash/scripts/onbox_assistant_SparkAlerts.py
sed -i "s/<TOKEN>/$TOKEN/"  /bootflash/scripts/onbox_assistant_SparkAlerts.py
sed -i "s/<EMAIL>/$EMAIL_ADDR/"  /bootflash/scripts/onbox_assistant_SparkAlerts.py