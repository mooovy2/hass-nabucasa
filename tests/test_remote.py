"""Test remote sni handler."""
import asyncio
from unittest.mock import patch, MagicMock, Mock
from datetime import timedelta

import pytest

from hass_nabucasa.remote import RemoteUI
from hass_nabucasa.utils import utcnow

from .common import mock_coro, MockAcme, MockSnitun


@pytest.fixture(autouse=True)
def ignore_context():
    """Ignore ssl context."""
    with patch(
        "hass_nabucasa.remote.RemoteUI._create_context", return_value=mock_coro()
    ) as context:
        yield context


@pytest.fixture
async def acme_mock():
    """Mock ACME client."""
    with patch("hass_nabucasa.remote.AcmeHandler", new_callable=MockAcme) as acme:
        yield acme


@pytest.fixture
async def snitun_mock():
    """Mock ACME client."""
    with patch("hass_nabucasa.remote.SniTunClientAioHttp", MockSnitun()) as snitun:
        yield snitun


def test_init_remote(cloud_mock):
    """Init remote object."""
    remote = RemoteUI(cloud_mock)

    assert len(cloud_mock.iot.mock_calls) == 2


async def test_load_backend_exists_cert(
    cloud_mock, acme_mock, mock_cognito, aioclient_mock, snitun_mock
):
    """Initialize backend."""
    valid = utcnow() + timedelta(days=1)
    cloud_mock.remote_api_url = "https://test.local/api"
    remote = RemoteUI(cloud_mock)

    aioclient_mock.post(
        "https://test.local/api/register_instance",
        json={
            "domain": "test.dui.nabu.casa",
            "email": "test@nabucasa.inc",
            "server": "rest-remote.nabu.casa",
        },
    )
    aioclient_mock.post(
        "https://test.local/api/snitun_token",
        json={
            "token": "test-token",
            "server": "rest-remote.nabu.casa",
            "valid": valid.timestamp(),
        },
    )

    await remote.load_backend()
    await asyncio.sleep(0.1)

    assert remote.snitun_server == "rest-remote.nabu.casa"
    assert not acme_mock.call_issue
    assert acme_mock.init_args == (
        cloud_mock,
        "test.dui.nabu.casa",
        "test@nabucasa.inc",
    )
    assert snitun_mock.call_start
    assert snitun_mock.init_args == (None, None)
    assert snitun_mock.init_kwarg == {
        "snitun_server": "rest-remote.nabu.casa",
        "snitun_port": 443,
    }

    assert snitun_mock.call_connect
    assert snitun_mock.connect_args[0] == b"test-token"


async def test_load_backend_not_exists_cert(
    cloud_mock, acme_mock, mock_cognito, aioclient_mock, snitun_mock
):
    """Initialize backend."""
    valid = utcnow() + timedelta(days=1)
    cloud_mock.remote_api_url = "https://test.local/api"
    remote = RemoteUI(cloud_mock)

    aioclient_mock.post(
        "https://test.local/api/register_instance",
        json={
            "domain": "test.dui.nabu.casa",
            "email": "test@nabucasa.inc",
            "server": "rest-remote.nabu.casa",
        },
    )
    aioclient_mock.post(
        "https://test.local/api/snitun_token",
        json={
            "token": "test-token",
            "server": "rest-remote.nabu.casa",
            "valid": valid.timestamp(),
        },
    )

    acme_mock.set_false()
    await remote.load_backend()
    await asyncio.sleep(0.1)

    assert remote.snitun_server == "rest-remote.nabu.casa"
    assert acme_mock.call_issue
    assert acme_mock.init_args == (
        cloud_mock,
        "test.dui.nabu.casa",
        "test@nabucasa.inc",
    )
    assert snitun_mock.call_start
    assert snitun_mock.init_args == (None, None)
    assert snitun_mock.init_kwarg == {
        "snitun_server": "rest-remote.nabu.casa",
        "snitun_port": 443,
    }

    assert snitun_mock.call_connect
    assert snitun_mock.connect_args[0] == b"test-token"


async def test_load_and_unload_backend(
    cloud_mock, acme_mock, mock_cognito, aioclient_mock, snitun_mock
):
    """Initialize backend."""
    valid = utcnow() + timedelta(days=1)
    cloud_mock.remote_api_url = "https://test.local/api"
    remote = RemoteUI(cloud_mock)

    aioclient_mock.post(
        "https://test.local/api/register_instance",
        json={
            "domain": "test.dui.nabu.casa",
            "email": "test@nabucasa.inc",
            "server": "rest-remote.nabu.casa",
        },
    )
    aioclient_mock.post(
        "https://test.local/api/snitun_token",
        json={
            "token": "test-token",
            "server": "rest-remote.nabu.casa",
            "valid": valid.timestamp(),
        },
    )

    await remote.load_backend()
    await asyncio.sleep(0.1)

    assert remote.snitun_server == "rest-remote.nabu.casa"
    assert not acme_mock.call_issue
    assert acme_mock.init_args == (
        cloud_mock,
        "test.dui.nabu.casa",
        "test@nabucasa.inc",
    )
    assert snitun_mock.call_start
    assert not snitun_mock.call_stop
    assert snitun_mock.init_args == (None, None)
    assert snitun_mock.init_kwarg == {
        "snitun_server": "rest-remote.nabu.casa",
        "snitun_port": 443,
    }

    await remote.close_backend()
    await asyncio.sleep(0.1)

    assert snitun_mock.call_stop


async def test_load_backend_exists_wrong_cert(
    cloud_mock, acme_mock, mock_cognito, aioclient_mock, snitun_mock
):
    """Initialize backend."""
    valid = utcnow() + timedelta(days=1)
    cloud_mock.remote_api_url = "https://test.local/api"
    remote = RemoteUI(cloud_mock)

    aioclient_mock.post(
        "https://test.local/api/register_instance",
        json={
            "domain": "test.dui.nabu.casa",
            "email": "test@nabucasa.inc",
            "server": "rest-remote.nabu.casa",
        },
    )
    aioclient_mock.post(
        "https://test.local/api/snitun_token",
        json={
            "token": "test-token",
            "server": "rest-remote.nabu.casa",
            "valid": valid.timestamp(),
        },
    )

    acme_mock.common_name = "wrong.dui.nabu.casa"
    await remote.load_backend()
    await asyncio.sleep(0.1)

    assert remote.snitun_server == "rest-remote.nabu.casa"
    assert acme_mock.call_reset
    assert acme_mock.init_args == (
        cloud_mock,
        "test.dui.nabu.casa",
        "test@nabucasa.inc",
    )
    assert snitun_mock.call_start
    assert snitun_mock.init_args == (None, None)
    assert snitun_mock.init_kwarg == {
        "snitun_server": "rest-remote.nabu.casa",
        "snitun_port": 443,
    }

    assert snitun_mock.call_connect
    assert snitun_mock.connect_args[0] == b"test-token"


async def test_call_disconnect(
    cloud_mock, acme_mock, mock_cognito, aioclient_mock, snitun_mock
):
    """Initialize backend."""
    valid = utcnow() + timedelta(days=1)
    cloud_mock.remote_api_url = "https://test.local/api"
    remote = RemoteUI(cloud_mock)

    aioclient_mock.post(
        "https://test.local/api/register_instance",
        json={
            "domain": "test.dui.nabu.casa",
            "email": "test@nabucasa.inc",
            "server": "rest-remote.nabu.casa",
        },
    )
    aioclient_mock.post(
        "https://test.local/api/snitun_token",
        json={
            "token": "test-token",
            "server": "rest-remote.nabu.casa",
            "valid": valid.timestamp(),
        },
    )

    await remote.load_backend()
    await asyncio.sleep(0.1)

    await remote.disconnect()
    assert snitun_mock.call_disconnect
