import pynetbox

# Your NetBox instance URL and API token
NETBOX_URL = 'https://lab-netbox.fink-telecom.com/'
API_TOKEN = '584ef5ef9a910ab9697ca194c0a44acb7c83c8b4'

# Initialize the pynetbox API connection
nb = pynetbox.api(NETBOX_URL, token=API_TOKEN)


def cu_netbox(data):
    #print(data['hostname'])
    #return
    # Example data from MikroTik parsed results
    router_data = {
        'hostname': data['hostname'],
        'vendor': '',
        'model': '',
        'serial_number': '',
        'device_model': '',
        'role': 'Router',
        'interfaces': [
            {
                'name': 'ether1',
                'mac_address': 'AA:BB:CC:DD:EE:FF',
                'type': '1000base-t',  # Interface type from NetBox
                'ip_addresses': ['192.168.1.1/24']
            },
            {
                'name': 'sfp1',
                'mac_address': 'FF:EE:DD:CC:BB:AA',
                'type': '10gbase-x-sfpp',
                'ip_addresses': ['10.0.0.1/24']
            }
        ],
        'sfp_modules': [
            {
                'interface': 'sfp1',
                'vendor': 'FINISAR',
                'part_number': 'FTLF8524P2BNV-EM',
                'serial_number': 'P123456789AB'
            }
        ]
    }

    router_data['vendor'] = data['system_resource']['platform'] if data['system_resource']['platform'] else 'MikroTik'
    router_data['device_model'] = data['firmware_version']['model'] if data['firmware_version']['model'] else 'MikroTik'
    router_data['serial_number'] = data['firmware_version']['serial-number'] if data['firmware_version']['serial-number'] else ''
    router_data['cpu_architecture'] = data['system_resource']['architecture-name'] if data['system_resource']['architecture-name'] else ''
    router_data['device_software_version'] = data['firmware_version']['current-firmware'] if data['firmware_version']['current-firmware'] else ''
    router_data['device_software'] = 'RouterOS'
    router_data['primary_mac_address'] = data['ethernet_interfaces'][0]['mac-address']
    router_data['primary_ipv4'] = data['primary_ipv4']
    
    
    # Separate simple interfaces from sfp interfaces
    simple_interfaces = [intf for intf in data['ethernet_interfaces'] if 'sfp-module-present' not in intf['monitor']]
    sfp_interfaces = [intf for intf in data['ethernet_interfaces'] if 'sfp-module-present' in intf['monitor']]
    
    # simple_interfaces.extend(data['vlan_interfaces'])
    # simple_interfaces.extend(data['bridge_interfaces'])
    # simple_interfaces.extend(data['wireless_interfaces'])
    
    
    # print(simple_interfaces)
    
    #return
    
        

    # Check if the device already exists
    # get device types
    device_types = list(nb.dcim.sites.all())
    print(device_types)
    # return
    
    device = nb.dcim.devices.get(serial=router_data['serial_number'])

    if device:
        print(f"Device {router_data['hostname']} already exists. Updating it.")
    else:
        # Create the device if it doesn't exist
        device = nb.dcim.devices.create(
            name=router_data['hostname'],
            device_type={'model': router_data['vendor'].capitalize()+' '+router_data['device_model']},
            role={'name': 'Router'},
            serial=router_data['serial_number'],
            site={'name': "Paris TH2"},  # Add appropriate site
            status='active',
            manufacturer={'name': router_data['vendor']},
        )
        print(f"Created device {router_data['hostname']}.")

    # Create or update interfaces
    # for interface in router_data['interfaces']:
    #     # Check if interface exists on the device
    #     intf = nb.dcim.interfaces.get(device_id=device.id, name=interface['name'])
    #     if intf:
    #         print(f"Interface {interface['name']} exists. Updating it.")
    #         # Update interface properties if needed
    #         intf.update({
    #             'mac_address': interface['mac_address'],
    #             'type': interface['type'],
    #         })
    #     else:
    #         # Create the interface if it doesn't exist
    #         nb.dcim.interfaces.create(
    #             device=device.id,
    #             name=interface['name'],
    #             type=interface['type'],
    #             mac_address=interface['mac_address'],
    #         )
    #         print(f"Created interface {interface['name']}.")

    #     # Add IP addresses to the interface
    #     for ip in interface['ip_addresses']:
    #         ip_obj = nb.ipam.ip_addresses.create(
    #             address=ip,
    #             assigned_object_type='dcim.interface',
    #             assigned_object_id=intf.id,
    #         )
    #         print(f"Assigned IP {ip} to interface {interface['name']}.")

    # # Create or update SFP modules
    # for sfp in router_data['sfp_modules']:
    #     # Check if a module already exists on the interface
    #     intf = nb.dcim.interfaces.get(device_id=device.id, name=sfp['interface'])
    #     if intf:
    #         # Module bay and module can be created here
    #         module_bay = nb.dcim.module_bays.create(
    #             device=device.id,
    #             name=f"{sfp['interface']}-bay",
    #         )
    #         nb.dcim.modules.create(
    #             device=device.id,
    #             module_bay=module_bay.id,
    #             part_number=sfp['part_number'],
    #             serial=sfp['serial_number'],
    #             manufacturer={'name': sfp['vendor']}
    #         )
    #         print(f"Created SFP module on {sfp['interface']}.")
