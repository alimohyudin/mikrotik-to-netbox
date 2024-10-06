import paramiko
import pynetbox
import requests
import json
import re



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
    #router_data['full_config'] = run_command("/export")

    router_data['ethernet_interfaces'] = parse_details_without_paging(router_data['ethernet_interfaces'])
    router_data['vlan_interfaces'] = parse_details_without_paging(router_data['vlan_interfaces'])
    router_data['bridge_interfaces'] = parse_details_without_paging(router_data['bridge_interfaces'])
    router_data['wireless_interfaces'] = parse_details_without_paging(router_data['wireless_interfaces'])

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


        #create_or_update_device_in_netbox(data)

if __name__ == "__main__":
    print("Starting...")
    routers = [
        # Add more routers here...
    ]
    main(routers)
