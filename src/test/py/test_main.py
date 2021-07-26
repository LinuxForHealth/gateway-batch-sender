from logging import raiseExceptions
from aiohttp.helpers import set_result
import pytest
import asyncio
import os
import importlib
from unittest.mock import AsyncMock, Mock, MagicMock
from nats.aio.errors import ErrTimeout, ErrNoServers
from nats.aio.client import Client as NATS
from whpa_cdp_batch_sender import main
import aiohttp
from async_retrying import retry, RetryError


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    os.environ['WHPA_CDP_CLIENT_GATEWAY_NATS_SERVER_URL'] = 'nats-server'
    os.environ['WHPA_CDP_CLIENT_GATEWAY_BATCH_RECEIVER_URL'] = 'batch-receiver'
    os.environ['WHPA_CDP_CLIENT_GATEWAY_TIMEZONE'] = 'some-timezone'
    os.environ['WHPA_CDP_CLIENT_GATEWAY_TENANT'] = 'tenant1'
    os.environ['WHPA_CDP_CLIENT_GATEWAY_SLEEP_ON_ERROR'] = '0'
    
    importlib.reload(main)

@pytest.mark.asyncio
async def test_nc_connect(mocker):
    mocker.patch.object(NATS, 'connect')
    result = await main.nc_connect()
    assert result == True

    NATS.connect.side_effect = ErrNoServers()
    result = await main.nc_connect()
    assert result == False


@pytest.mark.asyncio
async def test_send_to_cloud(mocker):
    mocker.patch.object(aiohttp.ClientSession, 'post')
    message = Mock()
    message.data = 'msg1'
    resp = AsyncMock()
    resp.status = 200
    aiohttp.ClientSession.post().__aenter__.return_value = resp
    await main.send_to_cloud(message)

    resp.status = 500
    with pytest.raises(RetryError):
        await main.send_to_cloud(message)

    aiohttp.ClientSession.post().__aenter__.side_effect = aiohttp.ClientConnectionError()
    with pytest.raises(RetryError) as e:
        await main.send_to_cloud(message)
    

@pytest.mark.asyncio
async def test_ack_callback():
    future = asyncio.get_event_loop().create_future()
    await main.ack_callback(None, future)
    await future
    assert future.done() == True


@pytest.mark.asyncio
async def test_message_handler(mocker):
    mocker.patch.object(main, 'nc')
    mocker.patch.object(main, 'send_to_cloud')
    mocker.patch.object(main.nc, 'request', new=AsyncMock())

    # Case 1
    main.len = lambda o : 5
    message = Mock()

    future = asyncio.get_event_loop().create_future()

    main.nc.request.side_effect = lambda *args, **kwargs: future.set_result(None)

    await main.message_handler(message, future)
    await future
    assert future.done() == True
    main.nc.request.assert_called_once()

    main.nc.request.reset_mock()

    # Case 2
    main.len = lambda o : 0
    await main.message_handler(message, None)
    main.nc.request.assert_not_called()

    main.nc.request.reset_mock()

    # Case 3
    main.len = lambda o : 5
    future = asyncio.get_event_loop().create_future()

    main.nc.request.side_effect = Exception('forced')

    #with pytest.raises(Exception):
    await main.message_handler(message, future)

    with pytest.raises(Exception):    
        await future

    assert future.done() == True
    main.nc.request.assert_called_once()


@pytest.mark.asyncio
async def test_main(mocker):
    os.environ['WHPA_CDP_CLIENT_GATEWAY_NATS_SERVER_URL'] = 'nats-server'
    os.environ['WHPA_CDP_CLIENT_GATEWAY_BATCH_RECEIVER_URL'] = 'batch-receiver'
    os.environ['WHPA_CDP_CLIENT_GATEWAY_TIMEZONE'] = 'some-timezone'
    os.environ['WHPA_CDP_CLIENT_GATEWAY_TENANT'] = 'tenant1'
    os.environ['WHPA_CDP_CLIENT_GATEWAY_SLEEP_ON_ERROR'] = '0'
    
    importlib.reload(main)

    mocker.patch.object(asyncio, 'get_event_loop')
    loop = Mock()
    asyncio.get_event_loop.return_value = loop
    main.main()
    loop.run_until_complete.assert_called()
    loop.reset_mock()

    # Case 2:
    del os.environ['WHPA_CDP_CLIENT_GATEWAY_NATS_SERVER_URL']
    del os.environ['WHPA_CDP_CLIENT_GATEWAY_BATCH_RECEIVER_URL']
    del os.environ['WHPA_CDP_CLIENT_GATEWAY_TIMEZONE']
    del os.environ['WHPA_CDP_CLIENT_GATEWAY_TENANT']
    
    importlib.reload(main)
    main.main()
    loop.run_until_complete.assert_not_called()
    loop.reset_mock()
