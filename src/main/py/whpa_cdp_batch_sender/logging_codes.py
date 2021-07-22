""" Common place to document project logging codes."""

# ERROR
NATS_CONNECT_ERROR = 'CGBSSERR001: Error connecting to the NATS server: "%s".'
NATS_NOT_INITIALIZED = 'CGBSSERR002: NATS not initialized.'
BATCH_FAILED_TO_SEND = 'CGBSSERR003: Erroring sending batch to the cloud.'
BATCH_SENDER_CONNECT_ERROR = 'CGBSSERR004: Connection error'
BATCH_SENDER_OTHER_ERROR = 'CGBSSERR005: Other error'
UNEXPECTED_ERROR = 'CGBSSERR006: Unexpected exception occured'

# WARN
NATS_REQUEST_TIMED_OUT = 'CGBSSWARN001: NATS Request timed out'


#INFO
STARTUP_ENV_VARS = 'CGBSSLOG001: Batch sender started with the follow value from the env:\nHL7 subject="%s"\nNATs Jetstream Connected Address="%s"\nBatch Receiver URL="%s"\nTimezone="%s"\nTenant="+"%s"'
SENDING_TO_CLOUD = 'CGBSSLOG002: Sending message to the cloud batch receiver'
ACK_RECEIVED_FROM_NATS = 'CGBSSLOG003: Confirmed that ack has been received by the jetstream server'
BATCH_RECEIVER_RESP_STATUS = 'CGBSSLOG004: Response status: %s'
BATCH_RECEIVER_RESP_MESSAGE = 'CGBSSLOG005: Response message: %s'
BATCH_SENT_SUCCESS = 'CGBSSLOG006: Batch sent successfully'
NATS_RECEIVED_NEXT_BATCH = 'CGBSSLOG007: Received next batch from NATS, calling the batch receiver'
NATS_REQUESTING_NEXT_BATCH = 'CGBSSLOG008: Requesting next message from jetstream'
WAITING_FOR_PROCESSING = 'CGBSSLOG009: Waiting for processing to be complete'
PROCESSING_COMPLETE = 'CGBSSLOG010: Processing completed'
