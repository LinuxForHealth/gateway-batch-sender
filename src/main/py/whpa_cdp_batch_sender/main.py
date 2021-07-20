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
batch_receiver_url = os.getenv('WHPA_CDP_CLIENT_GATEWAY_BATCH_RECEIVER_URL', default='http://192.168.37.21:5000/upload_hl7_batchzip')
# Timezone
timezone = os.getenv('WHPA_CDP_CLIENT_GATEWAY_TIMEZONE', default='America/New_York')
# Tenant
tenant = os.getenv('WHPA_CDP_CLIENT_GATEWAY_TENANT', default='cloud1')

# logger.info(logging_codes.STARTUP_ENV_VARS,subject,connected_address,batch_receiver_url,timezone,tenant)

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
@retry(attempts=3)
async def send_to_cloud(msg):
    # logger.info(logging_codes.SENDING_TO_CLOUD,'test')
    async with aiohttp.ClientSession() as session:
        try:
            form = aiohttp.FormData()
            form.add_field('file', msg.data)
            async with session.post(batch_receiver_url, data=form, headers=headers) as resp:
                    response_msg = await resp.text()
                    logger.info('Response status:'+str(resp.status))
                    logger.info('Response:'+response_msg)
                    if resp.status == 200 and resp.status < 300:        
                        logger.info('Batch sent successfully')
                    else:
                        logger.info('Erroring sending batch to the cloud')
                        raise RuntimeError('Non-200 error code response')
                    
        except aiohttp.ClientConnectorError as e:
            logger.error('Connection Error',exc_info=e)
            raise

# Callback for the message ack        
def ack_callback(msg, future):
    logger.info('Confirmed that ack has been received by the jetstream server')
    logger.info(msg)
    logger.info('Received ACK:'+str(msg.data))
    future.set_result(None)

#Callback for the message request
def message_handler(msg, future):
    logger.info('Received response from NATS:'+str(msg))
    logger.info('Calling the batch receiver')
    loop.create_task(send_to_cloud(msg))
    if len(msg.reply) != 0:
        # 3. send ack to jetstream after message has been processed
        loop.create_task(nc.request(msg.reply, b'+ACK', cb=partial(ack_callback, future=future)))

async def run(loop):
    global nc

    if nc is None:
        logger.error(logging_codes.NATS_NOT_INITIALIZED)
        return 1

    while True:                   
            fut = loop.create_future()
            logger.info('Requesting next message from jetstream')
            try:
                response = await nc.request('$JS.API.CONSUMER.MSG.NEXT.'+subject, payload=b'', cb=partial(message_handler, future=fut))
                logger.info('Request call response='+str(response))
            except ErrTimeout:
                logger.error("Request timed out")
                    
            # sleep 1 sescond before requesting next message        
            # await asyncio.sleep(1, loop=loop)
            logger.info('Waiting for processing to be complete')
            await fut
            logger.info('Processing completed')

        
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(nc_connect())
    loop.run_until_complete(run(loop))
    loop.close()