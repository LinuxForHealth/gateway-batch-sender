import asyncio
import aiohttp
import os
import time
from whpa_cdp_batch_sender import logger_util, logging_codes
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrTimeout, ErrNoServers
from async_retrying import retry
from functools import partial

logger = logger_util.get_logger(__name__)

## HL7 is the stream and ENCRYPTED_BATCHES is the consumer.
subject = os.getenv('WHPA_CDP_CLIENT_GATEWAY_ENCRYPTED_BATCHES', default='HL7.ENCRYPTED_BATCHES')
# NATS Jetstream connection info
connected_address = os.getenv('WHPA_CDP_CLIENT_GATEWAY_NATS_SERVER_URL', default='127.0.0.1:4222')
# Batch receiver cloud
batch_receiver_url = os.getenv('WHPA_CDP_CLIENT_GATEWAY_BATCH_RECEIVER_URL', default='http://192.1ss68.37.21:5000/upload_hl7_batchzip')
# Timezone
timezone = os.getenv('WHPA_CDP_CLIENT_GATEWAY_TIMEZONE', default='America/New_York')
# Tenant
tenant = os.getenv('WHPA_CDP_CLIENT_GATEWAY_TENANT', default='cloud1')

sleep_on_error_duration = int(os.getenv('WHPA_CDP_CLIENT_GATEWAY_SLEEP_ON_ERROR', default=5))

#headers used in the post to the batch receiver.
headers = {'timezone': timezone, 'tenant-id': tenant}

#uninitiated NATS Client
nc = None

# Connect to the NATS jetstream server
async def nc_connect():
    global nc
    
    nc = NATS()

    try:
        await nc.connect(connected_address, loop=loop)
    except ErrNoServers as e:
        logger.error(logging_codes.NATS_CONNECT_ERROR,e)
        return 1

# Send message to the batch receiver in the cloud
@retry(attempts=5)
async def send_to_cloud(msg):
    logger.info(logging_codes.SENDING_TO_CLOUD)
    async with aiohttp.ClientSession() as session:
        try:
            form = aiohttp.FormData()
            form.add_field('file', msg.data)
            async with session.post(batch_receiver_url, data=form, headers=headers) as resp:
                response_msg = await resp.text()
                logger.info(logging_codes.BATCH_RECEIVER_RESP_STATUS, str(resp.status))
                logger.info(logging_codes.BATCH_RECEIVER_RESP_MESSAGE, response_msg)
                if resp.status == 200 and resp.status < 300:        
                    logger.info(logging_codes.BATCH_SENT_SUCCESS)
                else:
                    logger.error(logging_codes.BATCH_FAILED_TO_SEND)
                    raise RuntimeError('Non-200 error code response')
                    
        except aiohttp.ClientConnectorError as e:
            logger.error(logging_codes.BATCH_SENDER_CONNECT_ERROR, exc_info=e)
            await asyncio.sleep(sleep_on_error_duration)
            raise
        except Exception as e:
            logger.error(logging_codes.BATCH_SENDER_OTHER_ERROR, exc_info=e)
            await asyncio.sleep(sleep_on_error_duration)
            raise

# Callback for the message ack        
async def ack_callback(msg, future):
    logger.info(logging_codes.ACK_RECEIVED_FROM_NATS)
    future.set_result(None)

#Callback for the message request
async def message_handler(msg, future):
    logger.info(logging_codes.NATS_RECEIVED_NEXT_BATCH)
    try:
        await send_to_cloud(msg)
        if len(msg.reply) != 0:
            # 3. send ack to jetstream after message has been processed
            await nc.request(msg.reply, b'+ACK', cb=partial(ack_callback, future=future))
    except Exception as e:
        future.set_exception(e)

async def run(loop):
    global nc

    if nc is None:
        logger.error(logging_codes.NATS_NOT_INITIALIZED)
        return 1

    while True:               
        try:    
            fut = loop.create_future()
            logger.info(logging_codes.NATS_REQUEST_TIMED_OUT)
            try:
                response = await nc.request('$JS.API.CONSUMER.MSG.NEXT.'+subject, payload=b'', cb=partial(message_handler, future=fut))
            except ErrTimeout:
                logger.warn(logging_codes.NATS_REQUEST_TIMED_OUT)
                    
            # sleep 1 sescond before requesting next message        
            # await asyncio.sleep(1, loop=loop)
            logger.info(logging_codes.WAITING_FOR_PROCESSING)
            await fut
            logger.info(logging_codes.PROCESSING_COMPLETE)
        except:
            logger.error(logging_codes.UNEXPECTED_ERROR, exc_info=True)
            await asyncio.sleep(sleep_on_error_duration)

        
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(nc_connect())
    loop.run_until_complete(run(loop))
    loop.close()