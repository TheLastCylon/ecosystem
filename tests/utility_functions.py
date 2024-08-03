import pytest
import uuid

from ekosis.util.utility_functions import (
    camel_to_snake,
    string_to_uuid,
    is_valid_ipv4_address,
    is_possible_valid_ietf_hostname,
    is_valid_hostname,
    is_valid_port_number,
    flatten_dictionary,
    get_machine_hostname,
    is_valid_url
)

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_camel_to_snake():
    result = camel_to_snake('ThisIsATest')
    assert result == 'this_is_a_test'

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_string_to_uuid():
    test_uuid = uuid.uuid4()
    assert test_uuid == string_to_uuid(str(test_uuid))
    assert string_to_uuid('asdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdf') is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_is_valid_ipv4_address():
    assert is_valid_ipv4_address('127.0.0.1') is True
    assert is_valid_ipv4_address('xyz.0.0.1') is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_is_possible_valid_ietf_hostname():
    fail_host_name = ''
    for i in range(300):
        fail_host_name += 'a'
    assert is_possible_valid_ietf_hostname('google.com') is True
    assert is_possible_valid_ietf_hostname('google.com.') is True
    assert is_possible_valid_ietf_hostname('not-valid-') is False
    assert is_possible_valid_ietf_hostname(fail_host_name) is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_is_valid_hostname():
    assert is_valid_hostname('127.0.0.1') is True
    assert is_valid_hostname('test-host-name') is True
    assert is_valid_hostname('??#@') is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_is_valid_port_number():
    assert is_valid_port_number('12345') is True
    assert is_valid_port_number('xyz') is False

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_flatten_dictionary():
    dict_to_flatten = {
        "test": {
            "this": {
                "dict": 1
            }
        }
    }
    flattened_dict = flatten_dictionary(dict_to_flatten)
    assert flattened_dict["test.this.dict"] == 1

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_machine_hostname():
    assert get_machine_hostname('127.0.0.1') is not None
    assert get_machine_hostname('192.168.0.225') is not None
    assert get_machine_hostname('google.com') is not None

# --------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_is_valid_url():
    assert is_valid_url('https://google.com') is True
    assert is_valid_url('------------------') is False
