# sectoralarm/__init__.py

from .client import SectorAlarmAPI
from .exceptions import AuthenticationError, APIRequestError

__all__ = ['SectorAlarmAPI', 'AuthenticationError', 'APIRequestError']
