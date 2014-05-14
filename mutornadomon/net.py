import ipcalc


PRIVATE_NETS = [
    ipcalc.Network('10.0.0.0/8'),      # RFC 1918
    ipcalc.Network('172.16.0.0/12'),   # RFC 1918
    ipcalc.Network('192.168.0.0/16'),  # RFC 1918
    ipcalc.Network('127.0.0.0/8'),     # local ipv4
    ipcalc.Network('fc00::/7'),        # ula ipv6
    ipcalc.Network('fe80::/10'),       # link-local ipv6
    ipcalc.Network('2001:0002::/48'),  # bench ipv6
    ipcalc.Network('2001:db8::/32'),   # documentation-only
]


LOCAL_NETS = [
    ipcalc.Network('127.0.0.0/8'),     # local ipv4
    ipcalc.Network('fc00::/7'),        # ula ipv6
    ipcalc.Network('fe80::/10'),       # link-local ipv6
]


def is_local_address(ip):
    ip = ipcalc.IP(ip)
    return any(ip in net for net in LOCAL_NETS)


def is_private_address(ip):
    ip = ipcalc.IP(ip)
    return any(ip in net for net in PRIVATE_NETS)
