import uuid
import re
import socket
import ipaddress

from typing import Dict, Any
from urllib.parse import urlparse

# --------------------------------------------------------------------------------
def camel_to_snake(input_string: str) -> str:
    output_string = ""
    for i in range(len(input_string)):
        if input_string[i].isupper() and i != 0:
            output_string += "_" + input_string[i].lower()
        else:
            output_string += input_string[i].lower()
    return output_string

# --------------------------------------------------------------------------------
def string_to_uuid(value: str) -> uuid.UUID | bool:
    try:
        return uuid.UUID(value)
    except ValueError:
        return False

# --------------------------------------------------------------------------------
def is_valid_ipv4_address(ip_address: str) -> bool:
    try:
        ipaddress.IPv4Address(ip_address)
        return True
    except ipaddress.AddressValueError:
        return False

# Checks hostname against Internet Engineering Task Force (IETF) standard
# --------------------------------------------------------------------------------
def is_possible_valid_ietf_hostname(hostname: str) -> bool:
    if len(hostname) > 255: # It may not be longer than 255 characters
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1]  # strip exactly one dot from the right, if present
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))

# --------------------------------------------------------------------------------
def is_valid_hostname(hostname: str) -> bool:
    if not is_valid_ipv4_address(hostname):
        return is_possible_valid_ietf_hostname(hostname)
    return True

# --------------------------------------------------------------------------------
def is_valid_port_number(port_number: str) -> bool:
    return port_number.isdigit()

# --------------------------------------------------------------------------------
def flatten_dictionary(dictionary: Dict[str, Any], current_key: str = '') -> Dict[str, Any]:
    retval: Dict[str, Any] = {}
    for key, value in dictionary.items():
        new_key = f"{current_key}.{key}" if current_key else key
        if isinstance(dictionary[key], dict):
            retval.update(flatten_dictionary(value, new_key))
        else:
            retval[new_key] = value
    return retval

# --------------------------------------------------------------------------------
# This gets used to get the host name of a machine running an Ecosystem application
# --------------------------------------------------------------------------------
def get_machine_hostname(hostname: str) -> str:
    if hostname == "127.0.0.1" or hostname == "localhost":
        return socket.gethostname()
    elif is_valid_ipv4_address(hostname):
        return socket.gethostbyname(hostname)
    elif is_possible_valid_ietf_hostname(hostname):
        return hostname

# --------------------------------------------------------------------------------
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
