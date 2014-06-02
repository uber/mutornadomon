from __future__ import absolute_import

from .monitor import MuTornadoMon  # noqa
from .config import initialize_mutornadomon  # noqa

version_info = (0, 1, 6)
__name__ = 'MuTornadoMon'
__author__ = 'jbrown@uber.com'
__version__ = '.'.join(map(str, version_info))
__license__ = 'MIT'

__all__ = ['MuTornadoMon', initialize_mutornadomon, 'version_info']
