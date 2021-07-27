terminal 1:
-----------
`export USERNAME=<ibm email>`

`export PASSWORD=<artifactory api key>`

`docker compose up`

terminal 2 (after terminal 1 commands are done):
-----------
`docker exec -it testing_nats-tools_1 sh`

`nats req HL7.ENCRYPTED_BATCHES <message content>`
