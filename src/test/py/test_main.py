from whpa_cdp_batch_sender import main
import asyncio
import pytest
from nats.aio.errors import ErrTimeout, ErrNoServers
from unittest.mock import AsyncMock, Mock

def test_run_loop():
    loop = asyncio.get_event_loop()
    main.run = AsyncMock()
    main.run(loop)
    main.run.assert_called_with(loop)

