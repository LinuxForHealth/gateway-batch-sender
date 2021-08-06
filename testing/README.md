For this testing you will need to open 2 new terminal windows.

On the root of the project then you should run the gradle build command:

`gradle build`

If the build fails it will most like be due to missing TAAS Artifactory credentials in the gradle.properties file.  Add the following parameters to this file:

taasArtifactoryUsername=<your_ibm_email>
taasArtifactoryPassword=<your_artifactory_key>

Also make sure that you have logged into docker with the following command:

`docker login wh-imaging-cdp-docker-local.artifactory.swg-devops.com`


Terminal 1:
-----------
Firstly cd into the testing folder and then run the following commands:

`export USERNAME=<ibm email>`

`export PASSWORD=<artifactory api key>`

`docker-compose up --build` and thereafter use

`docker-compose up`

If you get 401 errors (authenication errors) the issue might be due to change password.  To get this to run properly run the following command:

`docker logout wh-imaging-cdp-docker-local.artifactory.swg-devops.com`

Then run the docker login command above and you will be asked to re-authenicate.  Then rerun the docker-compose up command and it should work now.

Terminal 2 (after terminal 1 commands are done):
-----------
`docker exec -it testing_nats-tools_1 sh`

`nats req HL7.ENCRYPTED_BATCHES <message content>`
