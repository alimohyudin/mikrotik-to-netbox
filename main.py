import paramiko
import pynetbox
import requests
import json
import re
from netbox_api import cu_netbox 



# MikroTik SSH connection function
def ssh_to_mikrotik(ip, port, username, password):
    try:
        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the MikroTik router
        ssh.connect(hostname=ip, port=port, username=username, password=password)

        print(f"Successfully connected to {ip}")
        return ssh
    except Exception as e:
        print(f"Failed to connect to {ip}: {e}")
        return None

# Retrieve configuration from the router
def get_router_config(ssh_client):
    if ssh_client is None:
        return None

    router_data = {}

    # Helper function to run commands and return output
    def run_command(command):
        stdin, stdout, stderr = ssh_client.exec_command(command)
        return stdout.read().decode()

    # Retrieve regular information
    router_data['ethernet_interfaces'] = run_command("/interface ethernet print detail without-paging")
    router_data['vlan_interfaces'] = run_command("/interface vlan print detail without-paging")
    router_data['bridge_interfaces'] = run_command("/interface bridge print detail without-paging")
    router_data['wireless_interfaces'] = run_command("/interface wireless print detail without-paging")
    router_data['hostname'] = parse_monitor(run_command("/system identity print without-paging"))
    router_data['system_resource'] = parse_monitor(run_command("/system resource print without-paging"))
    router_data['firmware_version'] = parse_monitor(run_command("/system routerboard print without-paging"))
    router_data['port'] = run_command("/port print detail without-paging")
    #router_data['full_config'] = run_command("/export")

    router_data['ethernet_interfaces'] = parse_details_without_paging(router_data['ethernet_interfaces'])
    router_data['vlan_interfaces'] = parse_details_without_paging(router_data['vlan_interfaces'])
    router_data['bridge_interfaces'] = parse_details_without_paging(router_data['bridge_interfaces'])
    router_data['wireless_interfaces'] = parse_details_without_paging(router_data['wireless_interfaces'])
    router_data['port'] = parse_details_without_paging(router_data['port'])

    # for each interface pick its name
    for index, interface_info in enumerate(router_data['ethernet_interfaces']):
        #print("interface_info: ", interface_info)
        if "name" in interface_info:
            #print("Found interface: ", interface_info["name"])
            # Extract the interface name
            interface_name = interface_info["name"]
            #print("Interface name: ", interface_name)

            # Check if this interface has an SFP or SFP+ module
            monitor_raw = run_command(f"/interface ethernet monitor {interface_name} once")
            #print(monitor)
            monitor_data = parse_monitor(monitor_raw)

            router_data['ethernet_interfaces'][index]['monitor'] = monitor_data


    for index, interface_info in enumerate(router_data['bridge_interfaces']):
        #print("interface_info: ", interface_info)
        if "name" in interface_info:
            #print("Found interface: ", interface_info["name"])
            # Extract the interface name
            interface_name = interface_info["name"]
            #print("Interface name: ", interface_name)

            # Check if this interface has an SFP or SFP+ module
            monitor_raw = run_command(f"/interface bridge monitor {interface_name} once")
            #print(monitor)
            monitor_data = parse_monitor(monitor_raw)

            router_data['bridge_interfaces'][index]['monitor'] = monitor_data


    for index, interface_info in enumerate(router_data['wireless_interfaces']):
        #print("interface_info: ", interface_info)
        if "name" in interface_info:
            #print("Found interface: ", interface_info["name"])
            # Extract the interface name
            interface_name = interface_info["name"]
            #print("Interface name: ", interface_name)

            # Check if this interface has an SFP or SFP+ module
            monitor_raw = run_command(f"/interface wireless monitor {interface_name} once")
            #print(monitor)
            monitor_data = parse_monitor(monitor_raw)

            router_data['wireless_interfaces'][index]['monitor'] = monitor_data

    return router_data

def parse_details_without_paging(data):
    output = []
    # Loop through all interfaces and check for SFP modules
    for line in data.split('\r\n\r\n'):
        #print("line: ", line)
        # Skip header lines and empty lines
        if line.startswith("Flags:"):
            mlines = line.split('\n')
            line = mlines[1:]
            line = '\n'.join(line)
            #print("new line: ", line)

        # Step 1: Normalize the line by removing newlines and excess spaces
        normalized_line = re.sub(r'\s+', ' ', line).strip()

        # Step 2: Split the line into parts
        parts = normalized_line.split(' ')
        #print("parts: ", parts)

        # Step 3: Initialize a dictionary to hold the information
        interface_info = {}

        # Step 4: Process each part of the line
        for part in parts:
            # Split the part into key and value
            # split only if there is an equal sign
            if '=' not in part:
                continue
            key, value = part.split('=', 1)
            # Add the key-value pair to the dictionary
            interface_info[key] = value.strip('"')
        if(interface_info != {}):
            output.append(interface_info)
        #break

    return output
def parse_print_without_paging(data):
    pass
def parse_monitor(data):
    output = {}
    #print("data: ", data)
    for line in data.split('\n'):
        #print("line: ", line)
        normalized_line = re.sub(r'\s+', ' ', line).strip()
        #print("normalized_line: ", normalized_line)
        parts = normalized_line.split(':')
        #print("parts: ", parts)

        # Step 3: Initialize a dictionary to hold the information
        value = {}

        if(len(parts) >= 2):
            value = parts[1].strip('"').strip()
            output[parts[0]] = value

    #print("output: ", output)
    return output


# Check if device exists in NetBox and create/update
def create_or_update_device_in_netbox(data):
    # Check NetBox for existing device
    # Create or update device, interfaces, and modules in NetBox
    pass

# Main function to loop over routers and process
def main(router_list):
    for router in router_list:
        print(f"Processing {router['hostname']}...")
        ssh_client = ssh_to_mikrotik(router['ip'], router['port'], router['username'], router['password'])
        data = get_router_config(ssh_client)

        # save data to file
        if data is not None:
            with open(f"{router['hostname']}-everything.json", "w") as f:
                json.dump(data, f, indent=4)
                print(f"Data saved to {router['hostname']}-everything.json")
            
            # process data
            cu_netbox(data)


        #create_or_update_device_in_netbox(data)

if __name__ == "__main__":
    print("Starting...")
    routers = [
        # Add more routers here...
    ]
    #main(routers)
    data = {
            "ethernet_interfaces": [
                {
                    "name": "ether1",
                    "default-name": "ether1",
                    "mtu": "1500",
                    "l2mtu": "1600",
                    "mac-address": "DC:2C:6E:E0:91:E8",
                    "orig-mac-address": "DC:2C:6E:E0:91:E8",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "monitor": {
                        "name": "ether1",
                        "status": "link-ok",
                        "auto-negotiation": "done",
                        "rate": "1Gbps",
                        "full-duplex": "yes",
                        "tx-flow-control": "no",
                        "rx-flow-control": "no",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "advertising": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "link-partner-advertising": "10M-baseT-half,10M-baseT-full,100M-baseT-half,"
                    }
                },
                {
                    "name": "qsfp28-1-1",
                    "default-name": "qsfp28-1-1",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "orig-mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "fec91",
                    "sfp-shutdown-temperature": "80C",
                    "monitor": {
                        "name": "qsfp28-1-1",
                        "status": "link-ok",
                        "auto-negotiation": "done",
                        "rate": "100Gbps",
                        "full-duplex": "yes",
                        "tx-flow-control": "no",
                        "rx-flow-control": "no",
                        "fec": "fec91",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "sfp-supported": "1G-baseX,10G-baseSR-LR,25G-baseSR-LR,",
                        "advertising": "1G-baseX,10G-baseSR-LR,25G-baseSR-LR,",
                        "link-partner-advertising": "",
                        "sfp-module-present": "yes",
                        "sfp-type": "QSFP28/QSFP56",
                        "sfp-connector-type": "LC",
                        "sfp-link-length-sm": "10km",
                        "sfp-vendor-name": "FS",
                        "sfp-vendor-part-number": "QSFP28-LR4-100G",
                        "sfp-vendor-revision": "01",
                        "sfp-vendor-serial": "G2140564425",
                        "sfp-manufacturing-date": "20220117",
                        "sfp-wavelength": "1310nm",
                        "sfp-temperature": "35C",
                        "sfp-supply-voltage": "3.299V",
                        "sfp-tx-bias-current": "54mA",
                        "sfp-tx-power": "1.73dBm",
                        "sfp-rx-power": "0.805dBm",
                        "eeprom-checksum": "good",
                        "eeprom": "0000",
                        "0010": "00 00 00 00 00 00 23 9a 00 00 80 e7 00 00 00 00 ......#. ........",
                        "0020": "00 00 2f 06 27 93 37 e0 39 0b 6a 1a 80 fa 71 f3 ../.'.7. 9.j...q.",
                        "0030": "71 fb 3a 2f 30 a3 3a 23 36 83 00 00 00 00 00 00 q.",
                        "0040": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0060": "00 00 ff 00 00 00 00 00 00 00 1f 00 00 00 00 00 ........ ........",
                        "0070": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0080": "11 ce 07 80 00 00 00 00 00 00 00 03 ff 02 0a 00 ........ ........",
                        "0090": "00 00 00 64 46 53 20 20 20 20 20 20 20 20 20 20 ...dFS",
                        "00a0": "20 20 20 20 00 00 00 00 51 53 46 50 32 38 2d 4c .... QSFP28-L",
                        "00b0": "52 34 2d 31 30 30 47 20 30 31 66 58 01 c1 46 20 R4-100G 01fX..F",
                        "00c0": "03 07 3f f2 47 32 31 34 30 35 36 34 34 32 35 20 ..?.G214 0564425",
                        "00d0": "20 20 20 20 32 30 32 32 30 31 31 37 0c 08 67 2d 2022 0117..g-",
                        "00e0": "00 00 08 26 4a 51 50 b2 21 45 6c 5c b7 c9 17 ea ...&JQP. !El\\....",
                        "00f0": "c6 5b 42 00 00 00 00 00 00 00 00 00 b7 d9 a9 b6 .[B..... ........"
                    }
                },
                {
                    "name": "qsfp28-1-2",
                    "default-name": "qsfp28-1-2",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:D5",
                    "orig-mac-address": "DC:2C:6E:E0:91:D5",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "monitor": {
                        "name": "qsfp28-1-2",
                        "status": "no-link",
                        "auto-negotiation": "done",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "sfp-supported": "1G-baseX,10G-baseSR-LR,25G-baseSR-LR,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "yes",
                        "sfp-type": "QSFP28/QSFP56",
                        "sfp-connector-type": "LC",
                        "sfp-link-length-sm": "10km",
                        "sfp-vendor-name": "FS",
                        "sfp-vendor-part-number": "QSFP28-LR4-100G",
                        "sfp-vendor-revision": "01",
                        "sfp-vendor-serial": "G2140564425",
                        "sfp-manufacturing-date": "20220117",
                        "sfp-wavelength": "1310nm",
                        "sfp-temperature": "35C",
                        "sfp-supply-voltage": "3.299V",
                        "sfp-tx-bias-current": "66mA",
                        "sfp-tx-power": "0.952dBm",
                        "sfp-rx-power": "0.056dBm",
                        "eeprom-checksum": "good",
                        "eeprom": "0000",
                        "0010": "00 00 00 00 00 00 23 9a 00 00 80 e7 00 00 00 00 ......#. ........",
                        "0020": "00 00 2f 06 27 93 37 e0 39 0b 6a 1a 80 fa 71 f3 ../.'.7. 9.j...q.",
                        "0030": "71 fb 3a 2f 30 a3 3a 23 36 83 00 00 00 00 00 00 q.",
                        "0040": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0060": "00 00 ff 00 00 00 00 00 00 00 1f 00 00 00 00 00 ........ ........",
                        "0070": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0080": "11 ce 07 80 00 00 00 00 00 00 00 03 ff 02 0a 00 ........ ........",
                        "0090": "00 00 00 64 46 53 20 20 20 20 20 20 20 20 20 20 ...dFS",
                        "00a0": "20 20 20 20 00 00 00 00 51 53 46 50 32 38 2d 4c .... QSFP28-L",
                        "00b0": "52 34 2d 31 30 30 47 20 30 31 66 58 01 c1 46 20 R4-100G 01fX..F",
                        "00c0": "03 07 3f f2 47 32 31 34 30 35 36 34 34 32 35 20 ..?.G214 0564425",
                        "00d0": "20 20 20 20 32 30 32 32 30 31 31 37 0c 08 67 2d 2022 0117..g-",
                        "00e0": "00 00 08 26 4a 51 50 b2 21 45 6c 5c b7 c9 17 ea ...&JQP. !El\\....",
                        "00f0": "c6 5b 42 00 00 00 00 00 00 00 00 00 b7 d9 a9 b6 .[B..... ........"
                    }
                },
                {
                    "name": "qsfp28-1-3",
                    "default-name": "qsfp28-1-3",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:D6",
                    "orig-mac-address": "DC:2C:6E:E0:91:D6",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "monitor": {
                        "name": "qsfp28-1-3",
                        "status": "no-link",
                        "auto-negotiation": "done",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "sfp-supported": "1G-baseX,10G-baseSR-LR,25G-baseSR-LR,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "yes",
                        "sfp-type": "QSFP28/QSFP56",
                        "sfp-connector-type": "LC",
                        "sfp-link-length-sm": "10km",
                        "sfp-vendor-name": "FS",
                        "sfp-vendor-part-number": "QSFP28-LR4-100G",
                        "sfp-vendor-revision": "01",
                        "sfp-vendor-serial": "G2140564425",
                        "sfp-manufacturing-date": "20220117",
                        "sfp-wavelength": "1310nm",
                        "sfp-temperature": "35C",
                        "sfp-supply-voltage": "3.298V",
                        "sfp-tx-bias-current": "58mA",
                        "sfp-tx-power": "1.724dBm",
                        "sfp-rx-power": "1.546dBm",
                        "eeprom-checksum": "good",
                        "eeprom": "0000",
                        "0010": "00 00 00 00 00 00 23 9a 00 00 80 d7 00 00 00 00 ......#. ........",
                        "0020": "00 00 2e fb 27 9e 37 c6 38 b1 6a 1a 80 fa 71 f3 ....'.7. 8.j...q.",
                        "0030": "71 fb 3a 39 30 a3 3a 1c 36 7b 00 00 00 00 00 00 q.",
                        "0040": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0060": "00 00 ff 00 00 00 00 00 00 00 1f 00 00 00 00 00 ........ ........",
                        "0070": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0080": "11 ce 07 80 00 00 00 00 00 00 00 03 ff 02 0a 00 ........ ........",
                        "0090": "00 00 00 64 46 53 20 20 20 20 20 20 20 20 20 20 ...dFS",
                        "00a0": "20 20 20 20 00 00 00 00 51 53 46 50 32 38 2d 4c .... QSFP28-L",
                        "00b0": "52 34 2d 31 30 30 47 20 30 31 66 58 01 c1 46 20 R4-100G 01fX..F",
                        "00c0": "03 07 3f f2 47 32 31 34 30 35 36 34 34 32 35 20 ..?.G214 0564425",
                        "00d0": "20 20 20 20 32 30 32 32 30 31 31 37 0c 08 67 2d 2022 0117..g-",
                        "00e0": "00 00 08 26 4a 51 50 b2 21 45 6c 5c b7 c9 17 ea ...&JQP. !El\\....",
                        "00f0": "c6 5b 42 00 00 00 00 00 00 00 00 00 b7 d9 a9 b6 .[B..... ........"
                    }
                },
                {
                    "name": "qsfp28-1-4",
                    "default-name": "qsfp28-1-4",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:D7",
                    "orig-mac-address": "DC:2C:6E:E0:91:D7",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "monitor": {
                        "name": "qsfp28-1-4",
                        "status": "no-link",
                        "auto-negotiation": "done",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "sfp-supported": "1G-baseX,10G-baseSR-LR,25G-baseSR-LR,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "yes",
                        "sfp-type": "QSFP28/QSFP56",
                        "sfp-connector-type": "LC",
                        "sfp-link-length-sm": "10km",
                        "sfp-vendor-name": "FS",
                        "sfp-vendor-part-number": "QSFP28-LR4-100G",
                        "sfp-vendor-revision": "01",
                        "sfp-vendor-serial": "G2140564425",
                        "sfp-manufacturing-date": "20220117",
                        "sfp-wavelength": "1310nm",
                        "sfp-temperature": "35C",
                        "sfp-supply-voltage": "3.298V",
                        "sfp-tx-bias-current": "58mA",
                        "sfp-tx-power": "1.444dBm",
                        "sfp-rx-power": "1.617dBm",
                        "eeprom-checksum": "good",
                        "eeprom": "0000",
                        "0010": "00 00 00 00 00 00 23 9a 00 00 80 d7 00 00 00 00 ......#. ........",
                        "0020": "00 00 2e fb 27 9e 37 c6 38 b1 6a 1a 80 fa 71 f3 ....'.7. 8.j...q.",
                        "0030": "71 fb 3a 39 30 a3 3a 1c 36 7b 00 00 00 00 00 00 q.",
                        "0040": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0060": "00 00 ff 00 00 00 00 00 00 00 1f 00 00 00 00 00 ........ ........",
                        "0070": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0080": "11 ce 07 80 00 00 00 00 00 00 00 03 ff 02 0a 00 ........ ........",
                        "0090": "00 00 00 64 46 53 20 20 20 20 20 20 20 20 20 20 ...dFS",
                        "00a0": "20 20 20 20 00 00 00 00 51 53 46 50 32 38 2d 4c .... QSFP28-L",
                        "00b0": "52 34 2d 31 30 30 47 20 30 31 66 58 01 c1 46 20 R4-100G 01fX..F",
                        "00c0": "03 07 3f f2 47 32 31 34 30 35 36 34 34 32 35 20 ..?.G214 0564425",
                        "00d0": "20 20 20 20 32 30 32 32 30 31 31 37 0c 08 67 2d 2022 0117..g-",
                        "00e0": "00 00 08 26 4a 51 50 b2 21 45 6c 5c b7 c9 17 ea ...&JQP. !El\\....",
                        "00f0": "c6 5b 42 00 00 00 00 00 00 00 00 00 b7 d9 a9 b6 .[B..... ........"
                    }
                },
                {
                    "name": "qsfp28-2-1",
                    "default-name": "qsfp28-2-1",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:D8",
                    "orig-mac-address": "DC:2C:6E:E0:91:D8",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "fec91",
                    "sfp-shutdown-temperature": "80C",
                    "monitor": {
                        "name": "qsfp28-2-1",
                        "status": "link-ok",
                        "auto-negotiation": "done",
                        "rate": "100Gbps",
                        "full-duplex": "yes",
                        "tx-flow-control": "no",
                        "rx-flow-control": "no",
                        "fec": "fec91",
                        "supported": "10M-baseT-half,10M-baseT-full,",
                        "sfp-supported": "1G-baseX,10G-baseSR-LR,40G-baseSR4-LR4,",
                        "advertising": "1G-baseX,10G-baseSR-LR,40G-baseSR4-LR4,",
                        "link-partner-advertising": "",
                        "sfp-module-present": "yes",
                        "sfp-type": "QSFP28/QSFP56",
                        "sfp-connector-type": "no-separable-connector",
                        "sfp-link-length-copper-active-om4": "3m",
                        "sfp-vendor-name": "FS",
                        "sfp-vendor-part-number": "Q28-AO03",
                        "sfp-vendor-revision": "00",
                        "sfp-vendor-serial": "S2106283764-1",
                        "sfp-manufacturing-date": "21-06-26",
                        "sfp-wavelength": "850nm",
                        "sfp-temperature": "31C",
                        "sfp-supply-voltage": "3.272V",
                        "sfp-tx-bias-current": "6mA",
                        "eeprom-checksum": "good",
                        "eeprom": "0000",
                        "0010": "00 00 00 00 00 00 1f 42 00 00 7f d0 00 00 00 00 .......B ........",
                        "0020": "00 00 0d 37 0c a2 0e 07 0c 1c 0d a5 0d a2 0d af ...7.... ........",
                        "0030": "0d ac 2a a1 2c 23 2d c9 2a 73 00 00 00 00 00 00 ..*.,#-. *s......",
                        "0040": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0050": "00 00 00 00 00 00 00 aa aa 00 00 00 00 00 00 00 ........ ........",
                        "0060": "00 00 ff 00 00 00 00 00 00 00 00 00 00 00 08 00 ........ ........",
                        "0070": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0080": "11 cc 23 80 00 00 00 40 00 02 00 00 ff 00 00 00 ..#....@ ........",
                        "0090": "00 00 03 00 46 53 20 20 20 20 20 20 20 20 20 20 ....FS",
                        "00a0": "20 20 20 20 1f 00 00 00 51 32 38 2d 41 4f 30 33 .... Q28-AO03",
                        "00b0": "20 20 20 20 20 20 20 20 30 30 42 68 03 52 46 bc 00Bh.RF.",
                        "00c0": "01 07 ff 9a 53 32 31 30 36 32 38 33 37 36 34 2d ....S210 6283764-",
                        "00d0": "31 20 20 20 32 31 30 36 32 36 20 20 00 10 67 a1 1 2106 26 ..g.",
                        "00e0": "00 00 08 df 70 9a 81 d1 29 78 9f d7 f8 cf b9 e7 ....p... )x......",
                        "00f0": "66 69 31 00 00 00 00 00 00 00 00 00 6a 7b 20 58 fi1..... ....j{ X"
                    }
                },
                {
                    "name": "qsfp28-2-2",
                    "default-name": "qsfp28-2-2",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:D9",
                    "orig-mac-address": "DC:2C:6E:E0:91:D9",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "monitor": {
                        "name": "qsfp28-2-2",
                        "status": "no-link",
                        "auto-negotiation": "done",
                        "supported": "10M-baseT-half,10M-baseT-full,",
                        "sfp-supported": "1G-baseX,10G-baseSR-LR,40G-baseSR4-LR4,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "yes",
                        "sfp-type": "QSFP28/QSFP56",
                        "sfp-connector-type": "no-separable-connector",
                        "sfp-link-length-copper-active-om4": "3m",
                        "sfp-vendor-name": "FS",
                        "sfp-vendor-part-number": "Q28-AO03",
                        "sfp-vendor-revision": "00",
                        "sfp-vendor-serial": "S2106283764-1",
                        "sfp-manufacturing-date": "21-06-26",
                        "sfp-wavelength": "850nm",
                        "sfp-temperature": "31C",
                        "sfp-supply-voltage": "3.272V",
                        "sfp-tx-bias-current": "6mA",
                        "eeprom-checksum": "good",
                        "eeprom": "0000",
                        "0010": "00 00 00 00 00 00 1f 42 00 00 7f d0 00 00 00 00 .......B ........",
                        "0020": "00 00 0d 37 0c a2 0e 07 0c 1c 0d a5 0d a2 0d af ...7.... ........",
                        "0030": "0d ac 2a a1 2c 23 2d c9 2a 73 00 00 00 00 00 00 ..*.,#-. *s......",
                        "0040": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0050": "00 00 00 00 00 00 00 aa aa 00 00 00 00 00 00 00 ........ ........",
                        "0060": "00 00 ff 00 00 00 00 00 00 00 00 00 00 00 08 00 ........ ........",
                        "0070": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0080": "11 cc 23 80 00 00 00 40 00 02 00 00 ff 00 00 00 ..#....@ ........",
                        "0090": "00 00 03 00 46 53 20 20 20 20 20 20 20 20 20 20 ....FS",
                        "00a0": "20 20 20 20 1f 00 00 00 51 32 38 2d 41 4f 30 33 .... Q28-AO03",
                        "00b0": "20 20 20 20 20 20 20 20 30 30 42 68 03 52 46 bc 00Bh.RF.",
                        "00c0": "01 07 ff 9a 53 32 31 30 36 32 38 33 37 36 34 2d ....S210 6283764-",
                        "00d0": "31 20 20 20 32 31 30 36 32 36 20 20 00 10 67 a1 1 2106 26 ..g.",
                        "00e0": "00 00 08 df 70 9a 81 d1 29 78 9f d7 f8 cf b9 e7 ....p... )x......",
                        "00f0": "66 69 31 00 00 00 00 00 00 00 00 00 6a 7b 20 58 fi1..... ....j{ X"
                    }
                },
                {
                    "name": "qsfp28-2-3",
                    "default-name": "qsfp28-2-3",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:DA",
                    "orig-mac-address": "DC:2C:6E:E0:91:DA",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "monitor": {
                        "name": "qsfp28-2-3",
                        "status": "no-link",
                        "auto-negotiation": "done",
                        "supported": "10M-baseT-half,10M-baseT-full,",
                        "sfp-supported": "1G-baseX,10G-baseSR-LR,40G-baseSR4-LR4,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "yes",
                        "sfp-type": "QSFP28/QSFP56",
                        "sfp-connector-type": "no-separable-connector",
                        "sfp-link-length-copper-active-om4": "3m",
                        "sfp-vendor-name": "FS",
                        "sfp-vendor-part-number": "Q28-AO03",
                        "sfp-vendor-revision": "00",
                        "sfp-vendor-serial": "S2106283764-1",
                        "sfp-manufacturing-date": "21-06-26",
                        "sfp-wavelength": "850nm",
                        "sfp-temperature": "31C",
                        "sfp-supply-voltage": "3.24V",
                        "sfp-tx-bias-current": "6mA",
                        "eeprom-checksum": "good",
                        "eeprom": "0000",
                        "0010": "00 00 00 00 00 00 1f 42 00 00 7e 90 00 00 00 00 .......B ..~.....",
                        "0020": "00 00 0d 37 0c a2 0e 07 0c 0e 0d a9 0d a5 0d a2 ...7.... ........",
                        "0030": "0d af 2a ae 2c 2d 2d a0 2a 7c 00 00 00 00 00 00 ..*.,--. *|......",
                        "0040": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0050": "00 00 00 00 00 00 00 aa aa 00 00 00 00 00 00 00 ........ ........",
                        "0060": "00 00 ff 00 00 00 00 00 00 00 00 00 00 00 08 00 ........ ........",
                        "0070": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0080": "11 cc 23 80 00 00 00 40 00 02 00 00 ff 00 00 00 ..#....@ ........",
                        "0090": "00 00 03 00 46 53 20 20 20 20 20 20 20 20 20 20 ....FS",
                        "00a0": "20 20 20 20 1f 00 00 00 51 32 38 2d 41 4f 30 33 .... Q28-AO03",
                        "00b0": "20 20 20 20 20 20 20 20 30 30 42 68 03 52 46 bc 00Bh.RF.",
                        "00c0": "01 07 ff 9a 53 32 31 30 36 32 38 33 37 36 34 2d ....S210 6283764-",
                        "00d0": "31 20 20 20 32 31 30 36 32 36 20 20 00 10 67 a1 1 2106 26 ..g.",
                        "00e0": "00 00 08 df 70 9a 81 d1 29 78 9f d7 f8 cf b9 e7 ....p... )x......",
                        "00f0": "66 69 31 00 00 00 00 00 00 00 00 00 6a 7b 20 58 fi1..... ....j{ X"
                    }
                },
                {
                    "name": "qsfp28-2-4",
                    "default-name": "qsfp28-2-4",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:DB",
                    "orig-mac-address": "DC:2C:6E:E0:91:DB",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "monitor": {
                        "name": "qsfp28-2-4",
                        "status": "no-link",
                        "auto-negotiation": "done",
                        "supported": "10M-baseT-half,10M-baseT-full,",
                        "sfp-supported": "1G-baseX,10G-baseSR-LR,40G-baseSR4-LR4,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "yes",
                        "sfp-type": "QSFP28/QSFP56",
                        "sfp-connector-type": "no-separable-connector",
                        "sfp-link-length-copper-active-om4": "3m",
                        "sfp-vendor-name": "FS",
                        "sfp-vendor-part-number": "Q28-AO03",
                        "sfp-vendor-revision": "00",
                        "sfp-vendor-serial": "S2106283764-1",
                        "sfp-manufacturing-date": "21-06-26",
                        "sfp-wavelength": "850nm",
                        "sfp-temperature": "31C",
                        "sfp-supply-voltage": "3.24V",
                        "sfp-tx-bias-current": "7mA",
                        "eeprom-checksum": "good",
                        "eeprom": "0000",
                        "0010": "00 00 00 00 00 00 1f 42 00 00 7e 90 00 00 00 00 .......B ..~.....",
                        "0020": "00 00 0d 37 0c a2 0e 07 0c 0e 0d a9 0d a5 0d a2 ...7.... ........",
                        "0030": "0d af 2a ae 2c 2d 2d a0 2a 7c 00 00 00 00 00 00 ..*.,--. *|......",
                        "0040": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0050": "00 00 00 00 00 00 00 aa aa 00 00 00 00 00 00 00 ........ ........",
                        "0060": "00 00 ff 00 00 00 00 00 00 00 00 00 00 00 08 00 ........ ........",
                        "0070": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........",
                        "0080": "11 cc 23 80 00 00 00 40 00 02 00 00 ff 00 00 00 ..#....@ ........",
                        "0090": "00 00 03 00 46 53 20 20 20 20 20 20 20 20 20 20 ....FS",
                        "00a0": "20 20 20 20 1f 00 00 00 51 32 38 2d 41 4f 30 33 .... Q28-AO03",
                        "00b0": "20 20 20 20 20 20 20 20 30 30 42 68 03 52 46 bc 00Bh.RF.",
                        "00c0": "01 07 ff 9a 53 32 31 30 36 32 38 33 37 36 34 2d ....S210 6283764-",
                        "00d0": "31 20 20 20 32 31 30 36 32 36 20 20 00 10 67 a1 1 2106 26 ..g.",
                        "00e0": "00 00 08 df 70 9a 81 d1 29 78 9f d7 f8 cf b9 e7 ....p... )x......",
                        "00f0": "66 69 31 00 00 00 00 00 00 00 00 00 6a 7b 20 58 fi1..... ....j{ X"
                    }
                },
                {
                    "name": "sfp28-1",
                    "default-name": "sfp28-1",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:DC",
                    "orig-mac-address": "DC:2C:6E:E0:91:DC",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "sfp-shutdown-temperature": "95C",
                    "monitor": {
                        "name": "sfp28-1",
                        "status": "no-link",
                        "auto-negotiation": "failed",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "no"
                    }
                },
                {
                    "name": "sfp28-2",
                    "default-name": "sfp28-2",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:DD",
                    "orig-mac-address": "DC:2C:6E:E0:91:DD",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "sfp-shutdown-temperature": "95C",
                    "monitor": {
                        "name": "sfp28-2",
                        "status": "no-link",
                        "auto-negotiation": "done",
                        "supported": "10M-baseT-half,10M-baseT-full,",
                        "sfp-supported": "1G-baseT-full,1G-baseX,2.5G-baseT,",
                        "advertising": "1G-baseT-full,1G-baseX,2.5G-baseT,",
                        "link-partner-advertising": "",
                        "sfp-module-present": "yes",
                        "sfp-rx-loss": "no",
                        "sfp-tx-fault": "no",
                        "sfp-type": "SFP/SFP+/SFP28/SFP56",
                        "sfp-connector-type": "no-separable-connector",
                        "sfp-link-length-copper-active-om4": "2m",
                        "sfp-vendor-name": "FS",
                        "sfp-vendor-part-number": "S28-AO02",
                        "sfp-vendor-revision": "01",
                        "sfp-vendor-serial": "S2106264627-2",
                        "sfp-manufacturing-date": "21-06-24",
                        "sfp-dwdm-channel-spacing": "1Ghz",
                        "eeprom-checksum": "good",
                        "eeprom": "0000",
                        "0010": "00 00 02 00 46 53 20 20 20 20 20 20 20 20 20 20 ....FS",
                        "0020": "20 20 20 20 01 ec 01 e2 53 32 38 2d 41 4f 30 32 .... S28-AO02",
                        "0030": "20 20 20 20 20 20 20 20 30 31 20 20 00 00 00 d9 01 ....",
                        "0040": "08 12 67 00 53 32 31 30 36 32 36 34 36 32 37 2d ..g.S210 6264627-",
                        "0050": "32 20 20 20 32 31 30 36 32 34 20 20 00 70 00 76 2 2106 24 .p.v",
                        "0060": "00 00 06 c8 82 bf 23 11 24 fe 72 4e a7 4f 5d de ......#. $.rN.O].",
                        "0070": "9e 64 98 00 00 00 00 00 00 00 00 00 79 40 bb a3 .d...... ....y@..",
                        "0080": "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ........ ........"
                    }
                },
                {
                    "name": "sfp28-3",
                    "default-name": "sfp28-3",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:DE",
                    "orig-mac-address": "DC:2C:6E:E0:91:DE",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "sfp-shutdown-temperature": "95C",
                    "monitor": {
                        "name": "sfp28-3",
                        "status": "no-link",
                        "auto-negotiation": "failed",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "no"
                    }
                },
                {
                    "name": "sfp28-4",
                    "default-name": "sfp28-4",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:DF",
                    "orig-mac-address": "DC:2C:6E:E0:91:DF",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "sfp-shutdown-temperature": "95C",
                    "monitor": {
                        "name": "sfp28-4",
                        "status": "no-link",
                        "auto-negotiation": "failed",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "no"
                    }
                },
                {
                    "name": "sfp28-5",
                    "default-name": "sfp28-5",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:E0",
                    "orig-mac-address": "DC:2C:6E:E0:91:E0",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "sfp-shutdown-temperature": "95C",
                    "monitor": {
                        "name": "sfp28-5",
                        "status": "no-link",
                        "auto-negotiation": "failed",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "no"
                    }
                },
                {
                    "name": "sfp28-6",
                    "default-name": "sfp28-6",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:E1",
                    "orig-mac-address": "DC:2C:6E:E0:91:E1",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "sfp-shutdown-temperature": "95C",
                    "monitor": {
                        "name": "sfp28-6",
                        "status": "no-link",
                        "auto-negotiation": "failed",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "no"
                    }
                },
                {
                    "name": "sfp28-7",
                    "default-name": "sfp28-7",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:E2",
                    "orig-mac-address": "DC:2C:6E:E0:91:E2",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "sfp-shutdown-temperature": "95C",
                    "monitor": {
                        "name": "sfp28-7",
                        "status": "no-link",
                        "auto-negotiation": "failed",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "no"
                    }
                },
                {
                    "name": "sfp28-8",
                    "default-name": "sfp28-8",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:E3",
                    "orig-mac-address": "DC:2C:6E:E0:91:E3",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "sfp-shutdown-temperature": "95C",
                    "monitor": {
                        "name": "sfp28-8",
                        "status": "no-link",
                        "auto-negotiation": "failed",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "no"
                    }
                },
                {
                    "name": "sfp28-9",
                    "default-name": "sfp28-9",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:E4",
                    "orig-mac-address": "DC:2C:6E:E0:91:E4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "sfp-shutdown-temperature": "95C",
                    "monitor": {
                        "name": "sfp28-9",
                        "status": "no-link",
                        "auto-negotiation": "failed",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "no"
                    }
                },
                {
                    "name": "sfp28-10",
                    "default-name": "sfp28-10",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:E5",
                    "orig-mac-address": "DC:2C:6E:E0:91:E5",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "sfp-shutdown-temperature": "95C",
                    "monitor": {
                        "name": "sfp28-10",
                        "status": "no-link",
                        "auto-negotiation": "failed",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "no"
                    }
                },
                {
                    "name": "sfp28-11",
                    "default-name": "sfp28-11",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:E6",
                    "orig-mac-address": "DC:2C:6E:E0:91:E6",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "sfp-shutdown-temperature": "95C",
                    "monitor": {
                        "name": "sfp28-11",
                        "status": "no-link",
                        "auto-negotiation": "failed",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "no"
                    }
                },
                {
                    "name": "sfp28-12",
                    "default-name": "sfp28-12",
                    "mtu": "9200",
                    "l2mtu": "9300",
                    "mac-address": "DC:2C:6E:E0:91:E7",
                    "orig-mac-address": "DC:2C:6E:E0:91:E7",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "auto-negotiation": "yes",
                    "advertise": "10M-baseT-half,10M-baseT-full,100M-baseT-half,100M-baseT-full,",
                    "tx-flow-control": "off",
                    "rx-flow-control": "off",
                    "bandwidth": "unlimited/unlimited",
                    "switch": "switch1",
                    "sfp-rate-select": "high",
                    "sfp-ignore-rx-los": "no",
                    "fec-mode": "auto",
                    "sfp-shutdown-temperature": "95C",
                    "monitor": {
                        "name": "sfp28-12",
                        "status": "no-link",
                        "auto-negotiation": "failed",
                        "supported": "10M-baseT-half,10M-baseT-full,100M-baseT-half,",
                        "advertising": "",
                        "link-partner-advertising": "",
                        "sfp-module-present": "no"
                    }
                }
            ],
            "vlan_interfaces": [
                {
                    "name": "vlan106-init7",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "106",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan800",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "800",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan801",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "801",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan802",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "802",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan803",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "803",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan804-ss7a-int",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "804",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan805-ss7b-int",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "805",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan806",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "806",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan807-ss7a",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "807",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan808-ss7b",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "808",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan809",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "809",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan810",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "810",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan811",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "811",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan812",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "812",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan813",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "813",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan814",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "814",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan815",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "815",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan816",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "816",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan817",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "817",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan818-cogent-uplink",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "818",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan819",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "819",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan820-storage",
                    "mtu": "1500",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "820",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan1250-par-pcb",
                    "mtu": "9100",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "1250",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan1252-paris-r2-pcb-r2",
                    "mtu": "9100",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "1252",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan1450-zrh-pcb",
                    "mtu": "9100",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "1450",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan1452-zurich-r2-pcb-r2",
                    "mtu": "9100",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "1452",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan2250-par-pcb-mgmt",
                    "mtu": "9100",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "2250",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan2450-zrh-pcb-mgmt",
                    "mtu": "9100",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "2450",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan2560-pcb-aar-mgmt",
                    "mtu": "9100",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "2560",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan3248-pcb-zrh-gas-com",
                    "mtu": "9100",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "3248",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                },
                {
                    "name": "vlan3249-pcb-zrh-gas-com-mgmt",
                    "mtu": "9100",
                    "l2mtu": "9296",
                    "mac-address": "DC:2C:6E:E0:91:D4",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "loop-protect": "default",
                    "loop-protect-status": "off",
                    "loop-protect-send-interval": "5s",
                    "loop-protect-disable-time": "5m",
                    "vlan-id": "3249",
                    "interface": "bond0",
                    "use-service-tag": "no",
                    "mvrp": "no"
                }
            ],
            "bridge_interfaces": [
                {
                    "name": "mpls-loopback0",
                    "mtu": "auto",
                    "actual-mtu": "1500",
                    "l2mtu": "65535",
                    "arp": "enabled",
                    "arp-timeout": "auto",
                    "mac-address": "82:B2:24:7B:31:E6",
                    "protocol-mode": "none",
                    "fast-forward": "yes",
                    "igmp-snooping": "no",
                    "auto-mac": "yes",
                    "ageing-time": "5m",
                    "vlan-filtering": "no",
                    "dhcp-snooping": "no",
                    "port-cost-mode": "long",
                    "mvrp": "no",
                    "forward-reserved-addresses": "no",
                    "max-learned-entries": "auto",
                    "monitor": {
                        "state": "enabled",
                        "current-mac-address": "82",
                        "root-bridge": "yes",
                        "root-bridge-id": "0x8000.00",
                        "root-path-cost": "0",
                        "root-port": "none",
                        "port-count": "0",
                        "designated-port-count": "0",
                        "fast-forward": "no"
                    }
                }
            ],
            "wireless_interfaces": [],
            "hostname": {
                "name": "pcbr-r2-CCR2216-1G-12XS-2XQ"
            },
            "system_resource": {
                "uptime": "1w5d23m19s",
                "version": "7.16 (stable)",
                "build-time": "2024-09-20 13",
                "factory-software": "7.1.3",
                "free-memory": "14.9GiB",
                "total-memory": "16.0GiB",
                "cpu": "ARM64",
                "cpu-count": "16",
                "cpu-frequency": "2000MHz",
                "cpu-load": "1%",
                "free-hdd-space": "101.9MiB",
                "total-hdd-space": "128.0MiB",
                "write-sect-since-reboot": "4109560",
                "write-sect-total": "143817947",
                "bad-blocks": "0%",
                "architecture-name": "arm64",
                "board-name": "CCR2216-1G-12XS-2XQ",
                "platform": "MikroTik"
            },
            "firmware_version": {
                "routerboard": "yes",
                "model": "CCR2216-1G-12XS-2XQ",
                "serial-number": "HCA07RCRGGW",
                "firmware-type": "al64v3",
                "factory-firmware": "7.1.3",
                "current-firmware": "7.15.3",
                "upgrade-firmware": "7.16"
            }
        }
    data["hostname"] = routers[0]['hostname']
    data["primary_ipv4"] = routers[0]['ip']
    cu_netbox(data)
