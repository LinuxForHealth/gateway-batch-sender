import asyncio
import aiohttp
import os
import time
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrTimeout, ErrNoServers
import logging
from functools import partial

logging.info = print  # uncomment to print instead of log.

## HL7 is the stream and ENCRYPTED_BATCHES is the consumer.
subject = os.getenv('WHPA_CDP_CLIENT_GATEWAY_ENCRYPTED_BATCHES', default='HL7.ENCRYPTED_BATCHES')
# NATS Jetstream connection info
connected_address = os.getenv('WHPA_CDP_CLIENT_GATEWAY_NATS_SERVER_URL', default='127.0.0.1:4222')
# Batch receiver cloud
batch_receiver_url = os.getenv('WHPA_CDP_CLIENT_GATEWAY_BATCH_RECEIVER_URL', default='127.0.0.1:4222')
# Timezone
timezone = os.getenv('WHPA_CDP_CLIENT_GATEWAY_TIMEZONE', default='GMT')
# Tenant
tenant = os.getenv('WHPA_CDP_CLIENT_GATEWAY_TENANT', default='America/New_York')

logging.info("Batch sender started with the follow value from the env:")
logging.info("HL7 subject="+subject);
logging.info("NATs Jetstream Connected Address="+connected_address);
logging.info("Batch Receiver URL="+batch_receiver_url);
logging.info("Timezone="+timezone);
logging.info("Tenant="+tenant);

headers = {'timezone': timezone, 'tenant': tenant}
nc = None

# Connect to the NATS jetstream server
async def nc_connect():
    global nc
    
    nc = NATS()

    try:
        await nc.connect(connected_address, loop=loop)
    except ErrNoServers as e:
        logging.error(e)
        return 1

# Send message to the batch receiver in the cloud
async def send_to_cloud(msg):
    logging.info('Send to the cloud batch receiver')
    async with aiohttp.ClientSession() as session:
        async with session.put('batch_receiver_url', data=msg, headers=headers) as resp:
            logging.info(resp.status)
            response = await resp.text()
            logging.info(response)

# Callback for the message ack        
def ack_callback(msg, future):
    logging.info('Confirmed that ack has been received by the jetstream server')
    logging.info(msg)
    logging.info('Received ACK:'+str(msg.data))
    future.set_result(None)

#Callback for the message request
def message_handler(msg, future):
    logging.info('Received response:'+str(msg))
    logging.info('Received response: {msg.data}')
    logging.info('Calling the batch receiver')
    loop.create_task(send_to_cloud(msg))
    if len(msg.reply) != 0:
        # 3. send ack to jetstream after message has been processed
        loop.create_task(nc.request(msg.reply, b'+ACK', cb=partial(ack_callback, future=future)))

async def run(loop):
    global nc

    if nc is None:
        logging.error("Error NC is not initialized")
        return 1

    while True:                   
            fut = loop.create_future()
            logging.info('Requesting next message from jetstream')
            try:
                response = await nc.request('$JS.API.CONSUMER.MSG.NEXT.'+subject, payload=b'', cb=partial(message_handler, future=fut))
                logging.info('Request call response='+str(response))
            except ErrTimeout:
                logging.error("Request timed out")
                    
            # sleep 1 sescond before requesting next message        
            # await asyncio.sleep(1, loop=loop)
            logging.info('Waiting for processing to be complete')
            await fut
            logging.info('Processing completed')
            print('Processing complete!')

        
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(nc_connect())
    loop.run_until_complete(run(loop))
    loop.close()