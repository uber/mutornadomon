try:
    import ipaddress
    Network = ipaddress.ip_network
    IP = ipaddress.ip_address
except ImportError:
    import ipcalc
    Network = ipcalc.Network
    IP = ipcalc.IP


PRIVATE_NETS = [
    Network('10.0.0.0/8'),      # RFC 1918
    Network('172.16.0.0/12'),   # RFC 1918
    Network('192.168.0.0/16'),  # RFC 1918
    Network('127.0.0.0/8'),     # local ipv4
    Network('fc00::/7'),        # ula ipv6
    Network('fe80::/10'),       # link-local ipv6
    Network('2001:0002::/48'),  # bench ipv6
    Network('2001:db8::/32'),   # documentation-only
]


LOCAL_NETS = [
    Network('127.0.0.0/8'),     # local ipv4
    Network('::1'),             # local ipv6
    Network('fc00::/7'),        # ula ipv6
    Network('fe80::/10'),       # link-local ipv6
]


def is_local_address(ip):
    ip = IP(ip)
    return any(ip in net for net in LOCAL_NETS)


def is_private_address(ip):
    ip = IP(ip)
    return any(ip in net for net in PRIVATE_NETS)
