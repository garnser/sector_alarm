# sectoralarm/exceptions.py

class AuthenticationError(Exception):
    """Exception raised for authentication errors."""
    pass

class APIRequestError(Exception):
    """Exception raised for API request errors."""
    pass
