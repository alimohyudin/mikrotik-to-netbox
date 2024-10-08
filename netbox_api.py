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
        'interfaces': [],
        'sfp_modules': []
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
    
    
    device = nb.dcim.devices.get(serial=router_data['serial_number'])

    if device:
        print(f"Device {router_data['hostname']} already exists. Updating it.")
        nb.dcim.devices.update([{
            "id": device.id,
            "name": router_data['hostname'],
            "device_type": {'model': router_data['vendor'].capitalize()+' '+router_data['device_model']},
            "role": {'name': 'Router'},
            "serial": router_data['serial_number'],
            "site": {'name': "Paris TH2"},  # Add appropriate site
            "status": 'active',
            "manufacturer": {'name': router_data['vendor']},
            #"primary_ip4": {'address': router_data['primary_ipv4']},
            "custom_fields": {
                'device_softare_version': router_data['device_software_version'],
                'device_software': router_data['device_software'],
                'cpu_architecture': router_data['cpu_architecture'],
                'mac_address':router_data['primary_mac_address'],
            }
            
        }])
    else:
        # check if device type exists or create it
        print(f"Device {router_data['hostname']} doesn't exist. Creating it.")
        print(router_data['vendor'].capitalize()+' '+router_data['device_model'])
        device_type = list(nb.dcim.device_types.filter(model=router_data['vendor'].capitalize()+' '+router_data['device_model']))
        if len(device_type) == 0:
            device_type = nb.dcim.device_types.create(
                model=router_data['vendor'].capitalize()+' '+router_data['device_model'],
                slug=router_data['vendor'].lower()+'-'+router_data['device_model'].lower(),
                manufacturer={'name': router_data['vendor'].capitalize()},
                airflow="front-to-rear",
                is_full_depth=True,
                u_height=1
            )
        # Create the device if it doesn't exist
        device = nb.dcim.devices.create(
            name=router_data['hostname'],
            device_type={'model': router_data['vendor'].capitalize()+' '+router_data['device_model']},
            role={'name': 'Router'},
            serial=router_data['serial_number'],
            site={'name': "Paris TH2"},  # Add appropriate site
            status='active',
            manufacturer={'name': router_data['vendor']},
            custom_fields={
                'device_softare_version': router_data['device_software_version'],
                'device_software': router_data['device_software'],
                'cpu_architecture': router_data['cpu_architecture'],
                'mac_address':router_data['primary_mac_address'],
            }
        )
        print(f"Created device {router_data['hostname']}.")


    #########################################################
    # create or update interfaces
    #########################################################


    for interface in simple_interfaces:
        break
        # Check if interface exists on the device
        intf = nb.dcim.interfaces.get(device_id=device.id, name=interface['name'])
        if intf:
            print(f"Interface {interface['name']} exists. Updating it.")
            # Update interface properties if needed
            intf.update({
                'mac_address': interface['mac-address'],
                'type': '1000base-t',
            })
        else:
            # Create the interface if it doesn't exist
            nb.dcim.interfaces.create(
                device=device.id,
                name=interface['name'],
                type='1000base-t',
                mac_address=interface['mac-address'],
            )
            print(f"Created interface {interface['name']}.")

        # # Add IP addresses to the interface
        # for ip in interface['ip_addresses']:
        #     ip_obj = nb.ipam.ip_addresses.create(
        #         address=ip,
        #         assigned_object_type='dcim.interface',
        #         assigned_object_id=intf.id,
        #     )
        #     print(f"Assigned IP {ip} to interface {interface['name']}.")

    
    # Create or update SFP modules under Interfaces
    for interface in sfp_interfaces:
        break
        intf = nb.dcim.interfaces.get(device_id=device.id, name=interface['name'])
        
        if intf:
            print(f"Interface {interface['name']} exists. Updating it.")
            # Update interface properties if needed
            intf.update({
                'mac_address': interface['mac-address'],
                'type': get_valid_interface_types(interface['name']),
            })
        else:
            # Create the interface if it doesn't exist
            nb.dcim.interfaces.create(
                device=device.id,
                name=interface['name'],
                type=get_valid_interface_types(interface['name']),
                mac_address=interface['mac-address'],
            )
            print(f"Created interface {interface['name']}.")
    
    # Create or update SFP modules under Module Bays
    for sfp in sfp_interfaces:
        break
        # Check if a module bay exists for the SFP interface
        module_bay = list(nb.dcim.module_bays.filter(device_id=device.id, name=sfp['name']))

        if module_bay:
            print(f"SFP module bay on {sfp['name']} already exists. Updating it.")

            print(module_bay)
            # Retrieve the first module bay from the filter result
            module_bay = module_bay[0]

            # Check if a module exists in the module bay
            #create_or_update_module(nb, device, sfp, module_bay)
            if sfp['monitor']['sfp-module-present'] == 'yes':
                
                create_or_update_module(nb, device, sfp, module_bay)
                
                print(f"Updated SFP module on {sfp['name']}.")
            elif sfp['monitor']['sfp-module-present'] == "no":
                
                print(f"No SFP module present on {sfp['name']}. Update is  skipped.")
        else:
            print(f"SFP module bay on {sfp['name']} does not exist. Creating it.")
            try:
                if sfp['monitor']['sfp-module-present'] == 'yes':
                    # Create the module bay if SFP module is present
                    module_bay = nb.dcim.module_bays.create(
                        device=device.id,
                        name=sfp['name'],
                        type=sfp['monitor']['sfp-type'],  # Add appropriate type
                    )
                    
                    create_or_update_module(nb, device, sfp, module_bay)
                    
                    print(f"Created SFP module on {sfp['name']}.")
                elif sfp['monitor']['sfp-module-present'] == "no":
                    module_bay = nb.dcim.module_bays.create(
                        device=device.id,
                        name=sfp['name']
                    )
                    print(f"No SFP module present on {sfp['name']}. Created module bay but skipped module creation.")
            except Exception as e:
                print(f"Failed to create SFP module bay or module on {sfp['name']}. Error: {e}")
        #break


    # Bridge Interface
    bridge_intf = None
    for bridge in data['bridge_interfaces']:
        break
        # Check if the bridge interface already exists
        bridge_intf = list(nb.dcim.interfaces.filter(device_id=device.id, name=bridge['name'], type="virtual"))

        if len(bridge_intf) > 0:
            bridge_intf = bridge_intf[0]
            print(f"Bridge interface {'bridge'} already exists. Updating it.")
            # Update the bridge interface properties
            bridge_intf.update({
                'mtu': bridge['mtu'] if bridge['mtu'] != 'auto' else None,  # Set MTU if not 'auto'
                'mac_address': bridge['mac-address'],
                'description': "Bridge interface",
            })
        else:
            # Create the bridge interface if it doesn't exist
            bridge_intf = nb.dcim.interfaces.create(
                device=device.id,
                name=bridge['name'],
                type="virtual",  # Use the "bridge" type for bridge interfaces
                mtu=bridge['mtu'] if bridge['mtu'] != 'auto' else None,  # Set MTU if not 'auto'
                mac_address=bridge['mac-address'],
                description="Bridge interface"
            )
            print(f"Created bridge interface {'bridge'}.")
        #break

    #print("bridge: ", bridge_intf)
    for vlan in data['vlan_interfaces']:
        break
        # First, check if the parent interface (e.g., bond0) exists on the device
        #parent_interface = nb.dcim.interfaces.get(device_id=device.id, name=vlan['interface'])
        
        if not bridge_intf:
            print(f"Parent interface {vlan['interface']} not found for VLAN {vlan['name']}. Skipping creation.")
            continue

        # Check if the VLAN interface already exists
        vlan_intf = list(nb.dcim.interfaces.filter(device_id=device.id, name=vlan['name'], type="virtual"))

        if len(vlan_intf) > 0:
            print(f"VLAN interface {vlan['name']} already exists. Updating it.")
            # Update the VLAN interface properties
            vlan_intf.update({
                'mtu': vlan['mtu'],
                'mac_address': vlan['mac-address'],
                'description': f"VLAN {vlan['vlan-id']}",
            })
        else:
            # Create the VLAN interface if it doesn't exist
            nb.dcim.interfaces.create(
                device=device.id,
                name=vlan['name'],
                type="virtual",  # VLAN interfaces are typically virtual
                parent=bridge_intf.id,  # Associate with the parent interface (bond0, etc.)
                mtu=vlan['mtu'],
                mac_address=vlan['mac-address'],
                description=f"VLAN {vlan['vlan-id']}",
                #mode='tagged',  # You can set this as needed (tagged or access)
                #untagged_vlan=None,  # Set to None or define as needed
                #tagged_vlans=[vlan['vlan-id']],  # Tag the VLAN with the appropriate ID
            )
            print(f"Created VLAN interface {vlan['name']} on parent {vlan['interface']}.")



    # Add IP addresses to the interface
    # Loop through the IP addresses to create or update them in NetBox
    for ip_data in data['ip_addresses']:
        break
        print(ip_data)
        # Check if the interface exists on the device
        interface = list(nb.dcim.interfaces.filter(device_id=device.id, name=ip_data['interface']))

        if len(interface) == 0:
            print(f"Interface {ip_data['interface']} not found. Skipping IP {ip_data['address']}.")
            continue 
        interface = interface[0]
        # Check if the IP address already exists
        ip = list(nb.ipam.ip_addresses.filter(address=ip_data['address']))

        if len(ip) > 0:
            ip = ip[0]
            print(f"IP address {ip_data['address']} already exists. Updating it.")
            # Update the IP address properties
            ip.update({
                'assigned_object_type': 'dcim.interface',  # Ensure it's assigned to an interface
                'assigned_object_id': interface.id,        # Assign it to the correct interface
            })
        else:
            # Create the IP address if it doesn't exist
            nb.ipam.ip_addresses.create(
                address=ip_data['address'],
                status='active',                          # Set status to active (can be customized)
                assigned_object_type='dcim.interface',    # Assign to an interface
                assigned_object_id=interface.id,          # ID of the interface
                description=f"IP on {ip_data['interface']}",  # Optional description
            )
            print(f"Created and assigned IP address {ip_data['address']} to interface {ip_data['interface']}.")



    # Create or update Wireless Interfaces
    for wlan in data['wireless_interfaces']:
        # Check if the wireless interface already exists on the device
        wireless = list(nb.wireless.wireless_lans.filter(ssid=wlan['ssid'], description=f"Wireless interface {wlan['name']} - Device {device.name}"))
        print(wireless)

        if len(wireless) > 0:
            print(f"Wireless interface {wlan['name']} already exists. Updating it.")
            # Update the wireless interface properties
            wireless[0].update({
                'ssid': wlan['ssid'],
                'status': 'active' if wlan['monitor'].get('status', None) == 'running-ap' else 'disabled',
                'description': f"Wireless interface {wlan['name']} - Device {device.name}",
            })
        else:
            # Create the wireless interface if it doesn't exist
            nb.wireless.wireless_lans.create(
                ssid=wlan['ssid'],
                status= 'active' if wlan['monitor'].get('status', None) == 'running-ap' else 'disabled',
                description=f"Wireless interface {wlan['name']} - Device {device.name}",
            )
            print(f"Created wireless interface {wlan['name']} with SSID {wlan['ssid']}.")


    ######################################################
    # Create Update Serial Ports
    ######################################################
    
    # Loop through the serial ports to create them in NetBox
    for port in data['port']:
        break
        # Check if the serial port already exists on the device
        serial_port = list(nb.dcim.console_ports.filter(device_id=device.id, name=port['name']))

        if len(serial_port) > 0:
            serial_port = serial_port[0]
            print(f"Serial port {port['name']} already exists. Updating it.")
            # Update the serial port properties
            serial_port.update({
                'description': port['used-by'],  # Description or purpose of the serial port
                'speed': port['baud-rate'],      # Baud rate of the serial port
            })
        else:
            # Create the serial port if it doesn't exist
            nb.dcim.console_ports.create(
                device=device.id,
                name=port['name'],
                description=port['used-by'],  # Description or purpose of the serial port
                speed=port['baud-rate'],      # Baud rate of the serial port
            )
            print(f"Created serial port {port['name']} on device {device.name}.")




######################################################
# Helper Functions
######################################################
def get_valid_interface_types(name):
    valid_types = [ '1000base-kx','1000base-t','1000base-tx','1000base-x-gbic','1000base-x-sfp','100base-fx','100base-lfx','100base-t1','100base-tx','100base-x-sfp','100gbase-kp4','100gbase-kr2','100gbase-kr4','100gbase-x-cfp','100gbase-x-cfp2','100gbase-x-cfp4','100gbase-x-cpak','100gbase-x-cxp','100gbase-x-dsfp','100gbase-x-qsfp28','100gbase-x-qsfpdd','100gbase-x-sfpdd','10g-epon','10gbase-cx4','10gbase-kr','10gbase-kx4','10gbase-t','10gbase-x-sfpp','10gbase-x-x2','10gbase-x-xenpak','10gbase-x-xfp','128gfc-qsfp28','16gfc-sfpp','1gfc-sfp','2.5gbase-kx','2.5gbase-t','200gbase-x-cfp2','200gbase-x-qsfp56','200gbase-x-qsfpdd','25g-pon','25gbase-kr','25gbase-x-sfp28','2gfc-sfp','32gfc-sfp28','32gfc-sfpp','400gbase-x-cdfp','400gbase-x-cfp2','400gbase-x-cfp8','400gbase-x-osfp','400gbase-x-osfp-rhs','400gbase-x-qsfp112','400gbase-x-qsfpdd','40gbase-kr4','40gbase-x-qsfpp','4g','4gfc-sfp','50g-pon','50gbase-kr','50gbase-x-sfp28','50gbase-x-sfp56','5g','5gbase-kr','5gbase-t','64gfc-qsfpp','64gfc-sfpdd','64gfc-sfpp','800gbase-x-osfp','800gbase-x-qsfpdd','8gfc-sfpp','bpon','bridge','cdma','cisco-flexstack','cisco-flexstack-plus','cisco-stackwise','cisco-stackwise-160','cisco-stackwise-1t','cisco-stackwise-320','cisco-stackwise-480','cisco-stackwise-80','cisco-stackwise-plus','docsis','e1','e3','epon','extreme-summitstack','extreme-summitstack-128','extreme-summitstack-256','extreme-summitstack-512','gpon','gsm','ieee802.11a','ieee802.11ac','ieee802.11ad','ieee802.11ax','ieee802.11ay','ieee802.11be','ieee802.11g','ieee802.11n','ieee802.15.1','ieee802.15.4','infiniband-ddr','infiniband-edr','infiniband-fdr','infiniband-fdr10','infiniband-hdr','infiniband-ndr','infiniband-qdr','infiniband-sdr','infiniband-xdr','juniper-vcp','lag','lte','ng-pon2','other','other-wireless','sonet-oc12','sonet-oc192','sonet-oc1920','sonet-oc3','sonet-oc3840','sonet-oc48','sonet-oc768','t1','t3','virtual','xdsl','xg-pon','xgs-pon']
    
    try:
        if name is None:
            return valid_types[0]
        # find if valid_types contains part name
        name = name.lower()
        name = name.split('-')[0]
        
        matched_strings = [s for s in valid_types if name in s]
        
        return matched_strings[0]
    except Exception as e:
        print(e)
        return valid_types[0]

def create_or_update_module(nb, device, sfp, module_bay):
    
    try:
        print(1)
        # find module_type
        module_type = list(nb.dcim.module_types.filter(part_number=sfp['monitor']['sfp-vendor-part-number']))
        if len(module_type) > 0:
            print(2, module_type)
            module_type = module_type[0]
        else:
            print(3)
            # Create the module type
            module_type = nb.dcim.module_types.create(
                model=sfp['monitor']['sfp-vendor-part-number'],
                manufacturer={'name': sfp['monitor']['sfp-vendor-name']},
                part_number=sfp['monitor']['sfp-vendor-part-number'],
            )
        
        # check if module already exists
        module = list(nb.dcim.modules.filter(module_bay=module_bay.id, module_type_id=module_type.id))
        if module:
            print(4)        
            # update the module
            # module = module[0]
            # module.device = device.id
            # module.module_bay = module_bay.id
            # module.module_type = module_type.id
            # module.part_number = sfp['monitor']['sfp-vendor-part-number']
            # module.serial = sfp['monitor']['sfp-vendor-serial']
            # module.manufacturer = {'name': sfp['monitor']['sfp-vendor-name']}
            # module.custom_fields = {
            #     'sfp_connector_type': sfp['monitor'].get('sfp-connector-type', None),
            #     'sfp_link_length_sm': sfp['monitor'].get('sfp-link-length-sm', None),
            #     'sfp_manufacturing_date': sfp['monitor'].get('sfp-manufacturing-date', None),
            #     'sfp_rx_power': sfp['monitor'].get('sfp-rx-power', None),
            #     'sfp_tx_power': sfp['monitor'].get('sfp-tx-power', None),
            #     'sfp_vendor_revision': sfp['monitor'].get('sfp-vendor-revision', None),
            #     'sfp_wavelength': sfp['monitor'].get('sfp-wavelength', None),
            # }
            # module.save()
        else:
            print(5)
            # Create the module
            if sfp['advertise'] != '':
                module = nb.dcim.modules.create(
                    device=device.id,
                    module_bay=module_bay.id,
                    module_type=module_type.id,
                    part_number=sfp['monitor']['sfp-vendor-part-number'],
                    serial=sfp['monitor']['sfp-vendor-serial'],
                    manufacturer={'name': sfp['monitor']['sfp-vendor-name']},
                    custom_fields={
                        'sfp_connector_type': sfp['monitor'].get('sfp-connector-type', None),
                        'sfp_link_length_sm': sfp['monitor'].get('sfp-link-length-sm', None),
                        'sfp_manufacturing_date': sfp['monitor'].get('sfp-manufacturing-date', None),
                        'sfp_rx_power': sfp['monitor'].get('sfp-rx-power', None),
                        'sfp_tx_power': sfp['monitor'].get('sfp-tx-power', None),
                        'sfp_vendor_revision': sfp['monitor'].get('sfp-vendor-revision', None),
                        'sfp_wavelength': sfp['monitor'].get('sfp-wavelength', None),
                    }
                )
    except Exception as e:
        print(device.id, module_bay.id)
        print(5, e)
    print(6)
    return