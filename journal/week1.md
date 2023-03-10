# Week 1 — App Containerization

1) I installed Docker in my local development machine
2) I wrote a Dockerfile for both the backend-flask and frontend-react apps. The Dockerfile contains how the container would be set up by downloading
   the requirements to run the app and also copying files needed by the app into the container. The Dockerfile ends in a command 'CMD' with the parameters needed
   to start the app.
3) A docker-compose.yml file was also created which allowed me to set up the environment for each container such as the environment variables, ports, volumes and builds. 
   The docker-compose file also enabled me to orchestrate multiple containers side by side and manage them.
4) I had issues implementing the health check for the docker-compose file but hope to complete this soon.
