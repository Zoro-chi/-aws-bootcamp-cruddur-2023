# Week 6 — Deploying Containers

- [Preparation](#preparation)
- [ECS Cluster and ECR Repo](#ecs-cluster-and-ecr-repo)
- [Images of Backend and Frontend](#images-of-backend-and-frontend)
- [AWS Roles and Security Groups](#aws-roles-and-security-groups)
- [Application Load Balancer](#application-load-balancer)
- [Domain Configuration](#domain-configuration)
- [Fargate Services and Tasks](#fargate-services-and-tasks)

## Preparation

- `bin`: directory restructured from previous `backend-flask/bin`, more scripts were created here so we can easily run tasks;
- `erb`: directory to save ERB files which are used by Ruby to generate our environment variables;
- `docker-compose.yml`: update networks;
- update `.gitignore` and `.gitpod.yml`.

In the launched gitpod workspace, we firstly generate environment variable saved in `backend-flask.env` and `frontend-react-js.env`, which will be used for docker run locally:

```sh
./bin/backend/generate-env
./bin/frontend/generate-env
```

Passing sensitive data to AWS for running backend-flask later:

```sh
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/AWS_ACCESS_KEY_ID" --value $AWS_ACCESS_KEY_ID
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/AWS_SECRET_ACCESS_KEY" --value $AWS_SECRET_ACCESS_KEY
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/CONNECTION_URL" --value $PROD_CONNECTION_URL
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/ROLLBAR_ACCESS_TOKEN" --value $ROLLBAR_ACCESS_TOKEN
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/OTEL_EXPORTER_OTLP_HEADERS" --value "x-honeycomb-team=$HONEYCOMB_API_KEY"
```

## ECS Cluster and ECR Repo

Using AWS CLI, create a CloudWatch log group named `cruddur`, a ECS cluster named `cruddur`, and three ECR repos on AWS:

```sh
aws logs create-log-group --log-group-name cruddur
aws logs put-retention-policy --log-group-name cruddur --retention-in-days 1

aws ecs create-cluster \
 --cluster-name cruddur \
 --service-connect-defaults namespace=cruddur

aws ecr create-repository \
 --repository-name cruddur-python \
 --image-tag-mutability MUTABLE

aws ecr create-repository \
 --repository-name backend-flask \
 --image-tag-mutability MUTABLE

aws ecr create-repository \
 --repository-name frontend-react-js \
 --image-tag-mutability MUTABLE
```

Export and remember some AWS env vars in the gitpod workspace:

```sh
export AWS_ACCOUNT_ID=902749539657
gp env AWS_ACCOUNT_ID=902749539657

export ECR_PYTHON_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/cruddur-python"
gp env ECR_PYTHON_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/cruddur-python"

export ECR_FRONTEND_REACT_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/frontend-react-js"
gp env ECR_FRONTEND_REACT_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/frontend-react-js"

export ECR_BACKEND_FLASK_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/backend-flask"
gp env ECR_BACKEND_FLASK_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/backend-flask"
```

## Images of Backend and Frontend

Pull a base image of python, then tag and push it to the ECR repo:

```sh
./bin/ecr/login

docker pull python:3.10-slim-buster
docker tag python:3.10-slim-buster $ECR_PYTHON_URL:3.10-slim-buster
docker push $ECR_PYTHON_URL:3.10-slim-buster
```

For the backend image, create `backend-flask/bin/health-check`, and update `backend-flask/app.py` to add route for health check. Update backend dockerfile for development and production. Flask is secured by not running in debug mode. Now we can build backend image and push it to ECR:

```sh
./bin/backend/build
./bin/ecr/login
./bin/backend/push
```

For the frontend image fix cognito errors and token refresh. Create `frontend-react-js/Dockerfile.prod` and `frontend-react-js/nginx.conf`. Now we can build frontend image and push it to ECR:

```sh
cd frontend-react-js
npm run build
cd ../
./bin/frontend/build
./bin/ecr/login
./bin/frontend/push
```

Before pushing images to ECR, we can docker compose up to see if they work locally with data from/to local postgres and local dynamo db:

```sh
docker create cruddur-net
docker compose up
./bin/db/setup
./bin/ddb/schema-load
./bin/ddb/seed
```

Or only check the backend locally by:

```sh
docker create cruddur-net
docker compose up dynamodb-local db xray-daemon
./bin/db/setup
./bin/backend/run
```

## AWS Roles and Security Groups

Add AWS policies for `CruddurServiceExecutionRole` and `CruddurServiceExecutionPolicy`.

Based on the above files, create the ExecutionRole and attach policies:

```sh
aws iam create-role \
  --role-name CruddurServiceExecutionRole \
  --assume-role-policy-document file://aws/policies/service-assume-role-execution-policy.json

aws iam put-role-policy \
  --policy-name CruddurServiceExecutionPolicy \
  --role-name CruddurServiceExecutionRole \
  --policy-document file://aws/policies/service-execution-policy.json

aws iam attach-role-policy \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess \
  --role-name CruddurServiceExecutionRole

aws iam attach-role-policy \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
  --role-name CruddurServiceExecutionRole
```

Then create the TaskRole `CruddurTaskRole` and attach policies:

```sh
aws iam create-role \
    --role-name CruddurTaskRole \
    --assume-role-policy-document "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{
    \"Action\":[\"sts:AssumeRole\"],
    \"Effect\":\"Allow\",
    \"Principal\":{
      \"Service\":[\"ecs-tasks.amazonaws.com\"]
    }
  }]
}"

aws iam put-role-policy \
  --policy-name SSMAccessPolicy \
  --role-name CruddurTaskRole \
  --policy-document "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{
    \"Action\":[
      \"ssmmessages:CreateControlChannel\",
      \"ssmmessages:CreateDataChannel\",
      \"ssmmessages:OpenControlChannel\",
      \"ssmmessages:OpenDataChannel\"
    ],
    \"Effect\":\"Allow\",
    \"Resource\":\"*\"
  }]
}"

aws iam attach-role-policy \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess \
  --role-name CruddurTaskRole

aws iam attach-role-policy \
  --policy-arn arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess \
  --role-name CruddurTaskRole
```

Get `DEFAULT_VPC_ID` and `DEFAULT_SUBNET_IDS` in order to create a security group named `crud-srv-sg` that has inbound rules for port 4567 and 3000, and then authorize the security group to gain access of RDS (port 5432 in the default security group):

```sh
export DEFAULT_VPC_ID=$(aws ec2 describe-vpcs \
--filters "Name=isDefault, Values=true" \
--query "Vpcs[0].VpcId" \
--output text)
echo $DEFAULT_VPC_ID

export DEFAULT_SUBNET_IDS=$(aws ec2 describe-subnets  \
 --filters Name=vpc-id,Values=$DEFAULT_VPC_ID \
 --query 'Subnets[*].SubnetId' \
 --output json | jq -r 'join(",")')
echo $DEFAULT_SUBNET_IDS

export CRUD_SERVICE_SG=$(aws ec2 create-security-group \
  --group-name "crud-srv-sg" \
  --description "Security group for Cruddur services on ECS" \
  --vpc-id $DEFAULT_VPC_ID \
  --query "GroupId" --output text)
echo $CRUD_SERVICE_SG

aws ec2 authorize-security-group-ingress \
  --group-id $CRUD_SERVICE_SG \
  --protocol tcp \
  --port 4567 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id $CRUD_SERVICE_SG \
  --protocol tcp \
  --port 3000 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG_ID \
  --protocol tcp \
  --port 5432 \
  --source-group $CRUD_SERVICE_SG
```

## Application Load Balancer

Provision and configure Application Load Balancer along with target groups via AWS console:

- Basic configurations: name `cruddur-alb`, Internet-facing, IPv4 address type;
- Network mapping: default VPC, select first three availability zones;
- Security groups: create a new security group named `cruddur-alb-sg`, set inbound rules of HTTP and HTTPS from anywhere, and Custom TCP of 4567 and 3000 from anywhere (set description as TMP1 and TMP2); In addition, edit inbound rules of security group `crud-srv-sg`, instead of anywhere, set port source from `cruddur-alb-sg`, set description of port 4567 as ALBbackend, and port 3000 as ALBfrontend;
- Listeners and routing: HTTP:4567 with a new target group named `cruddur-backend-flask-tg`, select type as IP addresses, set HTTP:4567, set health check as `/api/health-check` with 3 healthy threshold, get its arn to put in `aws/json/service-backend-flask.json`; Add another listener HTTP:3000 with another target group created named `cruddur-frontend-react-js`, don't care about health check, set 3 healthy threshold, get its arn to put in `aws/json/service-frontend-react-js.json`.

## Domain Configuration

I've registered a domain name `zoro-chi.com.ng` for this bootcamp via [whogohost](https://www.whogohost.ng/). We can manage the domain using Route53 via hosted zone, create an SSL certificate via ACM, setup a record set for naked domain to point to frontend-react-js, and setup a record set for api subdomain to point to the backend-flask:

- At Route 53 > Hosted zones, create a new one with the registered domain name and the public type; Copy the values presented in the NS record type, and paste them into the porkbun nameservers (changes to your authoritative nameservers may take up to a couple of hours to propagate worldwide).
- At Certificate Manger, request a public certificate, add domain names of `zoro-chi.com.ng` and `*.zoro-chi.com.ng`, then enter the created certificate and click "Create records in Route 53", finally Route 53 will show two CNAME records.
- At Load Balancers, add a listener to make HTTP:80 redirect to HTTPS:443, and another one to make HTTPS:443 forward to frontend with certificate we created; edit rules for HTTPS:443 to add a new IF which sets Host Header as `api.zoro-chi.com.ng` and sets THEN forward to `cruddur-backend-flask-tg`.
- At Route 53 > Hosted zones > beici-demo.xyz, create a record without a record name, set type as "A - Route Traffic to an IPv4 address and some AWS resources", set route traffic as "Alias to Application and Classic Load Balancer" with the right region and load balancer, set routing policy as simple routing; do it again with record name `api.zoro-chi.com.ng`.

## Fargate Services and Tasks

Add AWS task definitions for backend and frontend. Now we have everything required for tasks, and then register the tasks by:

```sh
./bin/backend/register
./bin/frontend/register
```

Add basic json for creating AWS services. After creating the application load balancer, corresponding security group, subnet and target group, update the json and create the service by:

```sh
aws ecs create-service --cli-input-json file://aws/json/service-backend-flask.json
aws ecs create-service --cli-input-json file://aws/json/service-frontend-react-js.json
```

Before checking the domain https://zoro-chi.com.ng to see if the application works, we can check the backend https://api.zoro-chi.com.ng/api/health-check that should return a success, and https://api.zoro-chi.com.ng/api/activities/home that should be able to retrieve data from RDS.

Since I am the only user signed up in the app, it's impossible to send messages to others. To do this, I can insert a mock user to RDS using the commands below, then I can send messages using https://zoro-chi.com.ng/messages/new/londo:

```sh
./bin/db/connect prod
\x on
select * from users;
INSERT INTO public.users (display_name, email, handle, cognito_user_id)
VALUES
  ('Londo Mollari','lmollari@centari.com' ,'londo' ,'MOCK');
select * from users;
\q
```

Now we can check our domain https://zoro-chi.com.ng to see if everything works. If it is, we can safely remove TMP1 and TMP2 inbound rules in the security group `cruddur-alb-sg`, and delete HTTP:4567 and HTTP:3000 listeners in load balancer `cruddur-alb` (they were there for debugging more easily). Now we can only access the application through the domain.

If changes are made for backend/frontend, use the scripts in `./bin/backend/` and `./bin/frontend/` to build, tag, push the image to ECR, and update the service with a force deployment.
