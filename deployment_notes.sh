#!/bin/bash

# Note: with poetry, deployment is even simpler...

####################################################################################################
# STEPS EXECUTED TO DEPLOY THE BACKEND PROJECT (SIMPLIFIED)
####################################################################################################

# Configure Python Poetry dependencies
poetry shell
poetry install

# Configure deployment environment
export AWS_DEFAULT_REGION=us-east-1
export DEPLOYMENT_ENVIRONMENT=dev

# Initialize CDK (Cloud Development Kit)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
cdk bootstrap aws://${ACCOUNT_ID}/us-east-1

# Deploy the backend
cdk deploy "recipe-book-backend-${DEPLOYMENT_ENVIRONMENT}" --require-approval never



####################################################################################################
# STEPS EXECUTED TO DEPLOY THE FRONTEND PROJECT (SIMPLIFIED)
####################################################################################################

# IMPORTANT: MANUAL STEPS ONLY ONCE!!!
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# Manually set the global variables inside the frontend project "frontend/src/GLOBAL_VARS.jsx"
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# Configure Python Poetry dependencies
poetry shell
poetry install

# Move to frontend folder
cd frontend

# Build the frontend distribution
npm install .
npm run build

# Return to root directoy
cd ..

# Install Python dependencies with PIP (other tools like Poetry can be used)
pip install -r requirements.txt

# Configure deployment environment
export AWS_DEFAULT_REGION=us-east-1
export DEPLOYMENT_ENVIRONMENT=dev

# Initialize CDK (Cloud Development Kit)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
cdk bootstrap aws://${ACCOUNT_ID}/us-east-1

# Deploy the frontend
cdk deploy "recipe-book-frontend-${DEPLOYMENT_ENVIRONMENT}" --require-approval never


####################################################################################################
# STEPS EXECUTED TO DEPLOY THE CHATBOT PROJECT (SIMPLIFIED WITHOUT POETRY TOOL)
####################################################################################################

# IMPORTANT: MANUAL STEPS ONLY ONCE!!!
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# Manually configure the META TOKEN secret in AWS Secrets Manager with name /{env}/aws-whatsapp-chatbot
# --> AWS_API_KEY_TOKEN (added in META and AWS side)
# --> META_TOKEN (taken from META side)
# --> META_FROM_PHONE_NUMBER_ID (taken from META side)
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# Configure deployment environment
export AWS_DEFAULT_REGION=us-east-1
export DEPLOYMENT_ENVIRONMENT=dev

# Initialize CDK (Cloud Development Kit)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
cdk bootstrap aws://${ACCOUNT_ID}/us-east-1

# Deploy the chatbot
cdk deploy "recipe-book-chatbot-${DEPLOYMENT_ENVIRONMENT}" --require-approval never
