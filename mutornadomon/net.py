from __future__ import unicode_literals

import six

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
    ip = _convert_to_unicode(ip)
    ip = IP(ip)
    return any(ip in net for net in LOCAL_NETS)


def is_private_address(ip):
    ip = _convert_to_unicode(ip)
    ip = IP(ip)
    return any(ip in net for net in PRIVATE_NETS)


def _convert_to_unicode(ip):
    """Converts given ip to unicode if its str type for python2."""
    if six.PY2 and type(ip) == str:
        return six.u(ip)
    return ip
