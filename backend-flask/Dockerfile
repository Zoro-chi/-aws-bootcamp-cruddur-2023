FROM 902749539657.dkr.ecr.ca-central-1.amazonaws.com/cruddur-python:3.10-slim-buster

#* INSIDE CONTAINER
WORKDIR /backend-flask

#* OUTSIDE CONTAINER
#* CONTAINS LIBRARIES WE WANT TO INSTALL TO RUN THE APP
COPY requirements.txt requirements.txt

#* INSIDE THE CONTAINER
#* INSTALLS PYTHON LIBRARIES USED FOR THE APP
RUN pip3 install -r requirements.txt

#* OUTSIDE CONTAINER ---> INSIDE CONTAINER
#* . MEANS EVERYTHING IN THE CURRENT DIRECTORY
COPY . .

EXPOSE ${PORT}
CMD [ "python3", "-m" , "-u", "flask", "run", "--host=0.0.0.0", "--port=4567", "--debug"]