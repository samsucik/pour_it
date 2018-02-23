Use https://askubuntu.com/a/785442/440104 to fix name of network interface (otherwise it may keep changing):
```sudo nano /etc/udev/rules.d/70-persistent-net.rules```

Add:
```SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="xx:xx:xx:xx:xx:xx", NAME="usb0"```
42:cf:a2:b3:48:86


sudo ip addr add 192.168.1.1/24 dev usb0

sudo iptables -A FORWARD -o wlp4s0 -i usb0 -s 192.168.1.0/24 -m conntrack --ctstate NEW -j ACCEPT
sudo iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A POSTROUTING -t nat -j MASQUERADE

echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

sudo ifconfig usb0 up



sudo ip addr add 192.168.1.2/24 dev usb0
sudo ip route add default via 192.168.1.1