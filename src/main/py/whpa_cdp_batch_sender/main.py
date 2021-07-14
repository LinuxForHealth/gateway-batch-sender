import asyncio
import aiohttp
import os
import time
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrTimeout, ErrNoServers
from caf_logger import logger as caflogger
from functools import partial

nc = None
logger = caflogger.get_logger('whpa_cdp_batch_sender.config')

## HL7 is the stream and ENCRYPTED_BATCHES is the consumer.
subject = os.getenv('WHPA_CDP_CLIENT_GATEWAY_ENCRYPTED_BATCHES', default='HL7.ENCRYPTED_BATCHES')
connected_address = os.getenv('WHPA_CDP_CLIENT_GATEWAY_NATS_SERVER_URL', default='127.0.0.1:4222')
batch_receiver_url = os.getenv('WHPA_CDP_CLIENT_GATEWAY_BATCH_RECEIVER_URL', default='127.0.0.1:4222')

# How do I get these two?
timezone = os.getenv('WHPA_CDP_CLIENT_GATEWAY_BATCH_RECEIVER_URL', default='GMT')
tenant = 'cloud1'

headers = {'timezone': timezone, 'tenant': tenant}

# Connect to the NATS jetstream server
async def nc_connect():
    global nc
    nc = NATS()

    try:
        await nc.connect(connected_address, loop=loop)
    except ErrNoServers as e:
        print(e)

# Send message to the batch receiver in the cloud
async def send_to_cloud(msg):
    print('Send to the cloud batch receiver')
    logger.info('test')
    async with aiohttp.ClientSession() as session:
        async with session.put('batch_receiver_url', data=msg, headers=headers) as resp:
            print(resp.status)
            response = await resp.text()
            print(response)

# Callback for the message ack        
def ack_callback(msg, future):
    print('4. confirm that ack has been received by the jetstream server')
    print(f'Received ACK: {msg.data}')
    print('5. processing message finished')
    future.set_result(None)

#Callback for the message request
def message_handler(msg, future):
    print(f'Received response: {msg.data}')
    print('3. do something with the message')
    loop.create_task(send_to_cloud('test'))
    if len(msg.reply) != 0:
        # 3. send ack to jetstream after message has been processed
        loop.create_task(nc.request(msg.reply, b'+ACK', cb=partial(ack_callback, future=future)))

async def run(loop):
    global nc

    if nc is None:
        print("error nc not initialized")
        return

    while True:                   
            fut = loop.create_future()
            print('1. Requesting next message from jetstream')
            try:
                response = await nc.request('$JS.API.CONSUMER.MSG.NEXT.'+subject, payload=b'', cb=partial(message_handler, future=fut))
                print('Request response='+str(response))
            except ErrTimeout:
                print("Request timed out")
                    
            # sleep 1 sescond before requesting next message        
            # await asyncio.sleep(1, loop=loop)
            (print('2. waiting for processing to be complete'))
            await fut

        
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(nc_connect())
    loop.run_until_complete(run(loop))
    loop.close()