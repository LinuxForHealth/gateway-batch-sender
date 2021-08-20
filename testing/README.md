For this testing you will need to open 2 new terminal windows.

On the root of the project then you should run the gradle build command:

`gradle build`

Terminal 1:
-----------
Firstly cd into the testing folder and then run the following commands:

`docker-compose up`

(`docker-compose up --build` if you want to rebuild the images)

Terminal 2 (after terminal 1 commands are done):
-----------
`docker exec -it testing_nats-tools_1 sh`

`nats req HL7.ENCRYPTED_BATCHES <message content>`
