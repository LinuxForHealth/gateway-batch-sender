# whpa-cdp-batch-sender

This service will...
- Read batches from NATS Jetstream Server Consumer "ENCRYPTED_BATCHES and send the appropriate ACK to the Jetstream Server
- Send HL7 batches to the HL7 Batch Receiver in the Cloud via Rest API call including tenantId and timezone of where the gateway is deployed (in configuration) in the header.

## Deployment

Since version 1.0.0, the build has been integrated with the Jenkins CI and images are now pushed automatically. See the Jenkinsfile for image path and version configurations.

This image can be used to test the service/ run it locally without building etc.

---

## Development

### Setup

```bash
gradle tasks # will list all the available tasks
gradle build # will setup virtualenv, run all tests, and create reports and distribution
```

Note: you will need the `taasArtifactoryUsername` and `taasArtifactoryPassword` variables in `gradle.properties`

> [Refer](https://pages.github.ibm.com/WH-Provider-Analytics/CDP-Development/docs/Dev_setup/Python.html) and see `local.build.gradle` for more information.

Update gradle.properties as needed.

### Install NATS Jetstream server and NATS CLI

You can find the instructions for the NATS Jetstream server (via docker) here:
https://hub.docker.com/_/nats/

You can find the instructions for the NATS Cli here:
https://github.com/nats-io/natscli

### Create the HL7 stream and ENCRYPTED_BATCHES consumer

Create the HL7 stream:

```bash
nats str add HL7 --subjects "HL7.*" --ack --max-msgs=-1 --max-bytes=-1 --max-age=1y --storage file --retention limits --max-msg-size=-1 --discard=old --max-msgs-per-subject=-1 --dupe-window=2m --replicas=1
```

Create the ENCRYPTED_BATCHES consumer for the HL7 stream:

```bash
nats con add HL7 ENCRYPTED_BATCHES --filter HL7.ENCRYPTED_BATCHES --ack explicit --pull --deliver all --max-deliver=-1 --sample 100
```

### Building

Use gradle to do a clean build.

```bash
nats con add HL7 ENCRYPTED_BATCHES --filter HL7.ENCRYPTED_BATCHES --ack explicit --pull --deliver all --max-deliver=-1 --sample 100 --replay=instant --max-pending=1
```

### Testing

To run unittest, execute:

```bash
gradle clean test -b local.build.gradle
```

### Running by command line

To run the program, execute:

```bash
python3 -m whpa_cdp_batch_sender.main
```

To send a message:

```bash
nats req HL7.ENCRYPTED_BATCHES <subject> [<body>]
```

To send a message from a file:

```bash
echo <filename> | nats req HL7.ENCRYPTED_BATCHES <subject>
```

### Environment variables

You will need to override these if you are not running locally.

WHPA_CDP_CLIENT_GATEWAY_ENCRYPTED_BATCHES = NATS subject to use

WHPA_CDP_CLIENT_GATEWAY_NATS_SERVER_URL = NATS Jetstream connection info

WHPA_CDP_CLIENT_GATEWAY_BATCH_RECEIVER_URL = Batch receiver cloud URL

WHPA_CDP_CLIENT_GATEWAY_TIMEZONE = Timezone

WHPA_CDP_CLIENT_GATEWAY_TENANT = Tenant

### Creating the docker image

Create the container using the docker build command below. Add your artifactory id (this is likely your w3 email) and key where specified.

```bash
docker build --build-arg USERNAME=<taasArtifactoryUsername> --build-arg PASSWORD=<taasArtifactoryPassword> -t whpa-cdp-batch-sender:1.0.0 .
```

If the steps completed successfully, the image specified by the -t option should now exist.

### Running the docker image
Note that the versions may need updated in the examples below.

```bash
docker run --name whpa-cdp-batch-sender -p 5000:5000 whpa-cdp-batch-sender:1.0.0
```
