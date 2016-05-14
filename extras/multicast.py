#!/usr/bin/env python
#
# Send/receive UDP multicast packets.
# Requires that your OS kernel supports IP multicast.
#
# Usage:
#   mcast -s (sender, IPv4)
#   mcast -s -6 (sender, IPv6)
#   mcast    (receivers, IPv4)
#   mcast  -6  (receivers, IPv6)

MYPORT = 8123
MYGROUP_4 = '225.0.0.250'
MYGROUP_6 = 'ff15:7079:7468:6f6e:6465:6d6f:6d63:6173'
MYTTL = 1 # Increase to reach other networks

import time
import struct
import socket
import sys
import netifaces


def main():
    group = MYGROUP_6 if "-6" in sys.argv[1:] else MYGROUP_4

    if "-s" in sys.argv[1:]:
        sender(group)
    else:
        receiver(group)


def sender(group):
    addrinfo = socket.getaddrinfo(group, None)[0]

    s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

    # Set Time-to-live (optional)
    ttl_bin = struct.pack('@i', MYTTL)
    if addrinfo[0] == socket.AF_INET: # IPv4
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
    else:
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)

    while True:
        data = repr(time.time()) + '\0'
        s.sendto(data.encode('utf-8'), (addrinfo[4][0], MYPORT))
        time.sleep(1)


def sender2(group):
    import netifaces

    sockets = []
    ifs = netifaces.interfaces()
    for name in ifs:
        info = netifaces.ifaddresses(name)
        if netifaces.AF_INET in info:
            addr = info[netifaces.AF_INET][0]['addr']
            if addr != '127.0.0.1':
                print('ADDR', name, addr)
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                ttl_bin = struct.pack('@i', MYTTL) # optional
                s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
                s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(addr))
                sockets.append(s)

    addrinfo = socket.getaddrinfo(group, None)[0]
    while True:
        data = repr(time.time()) + '\0'
        print(addrinfo)
        for s in sockets:
            s.sendto(data.encode('utf-8'), (addrinfo[4][0], MYPORT))
        time.sleep(1)
    

def receiver(group):
    # Look up multicast group address in name server and find out IP version
    addrinfo = socket.getaddrinfo(group, None)[0]

    # Create a socket
    s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

    # Allow multiple copies of this program on one machine
    # (not strictly needed)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind it to the port
    s.bind(('', MYPORT))

    group_bin = socket.inet_pton(addrinfo[0], addrinfo[4][0])
    # Join group
    if addrinfo[0] == socket.AF_INET: # IPv4
        mreq = group_bin + struct.pack('=I', socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    else:
        mreq = group_bin + struct.pack('@I', 0)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)
    s.setblocking(False)
    s.settimeout(.5)
    # Loop, printing any data we receive
    while True:
        try:
            data, sender = s.recvfrom(1500)
        except socket.timeout:
            continue
        while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
        print (str(sender) + '  ' + repr(data))


if __name__ == '__main__':
    main()
