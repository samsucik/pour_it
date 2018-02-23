# How to SSH into Raspberry PI over USB from Linux (Ubuntu 16.04)

This has worked on Sam's laptop and may not be replicable on a different machine. But better than nothing. Note that root access was necessary.

1. Create this config
sudo subl /etc/udev/rules.d/70-persistent-net.rules

2. Put this into the file:
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="cdc_ether", NAME="usb0"
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="cdc_eem", NAME="usb0"
SUBSYSTEM=="net", ACTION=="add", DRIVERS=="cdc_subset", NAME="usb0"

3. Open your interfaces config
sudo subl /etc/network/interfaces

4. Add this:
auto usb0
iface usb0 inet static
    address 10.9.8.1
    netmask 255.255.255.0
    up iptables -A FORWARD -i usb0 -j ACCEPT
    up iptables -A FORWARD -o usb0 -j ACCEPT
    up iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

5. Connect PI over USB.

6. Open your Networks manager

7. Wait until you see the USB connection there

8. Edit the setting for the connection
	- disable IPv6
	- in IPv4 set Addresses to Link-Local Only
	- disable Automatic DNS
	- disable automatic Routes

9. Check in your terminal that you can ssh using 'ssh pi@raspberrypi.local' or 'ssh pi@IPADDRESS' (you'll see the IP address in the details of the connection in the Networks manager)