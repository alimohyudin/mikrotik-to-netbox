How to run this?
1- create routers-list.json file
    This should look sometihng like this:
        [
            {"ip": "102.22.105.55", "port": 17, "username": "netbox", "password": "", "hostname": "coo.cajutel.sl"}
        ]
2- Make sure you have python 3.12 installed
    > pip install paramiko pynetbox ipaddress
    > py main.py


How it works:
1- create devices
2- each device has interfaces
    - if interface > monitor has sfp-module-present": "no"
        - then create interface
    - else create module bays
        - if this module bay has vendor
            - then create module
3- each device has ports create Console Ports
    - ['port']
4- where are power ports?