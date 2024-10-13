# AWS CONFIGURATION

In order to correctly configure the AWS account and manual steps (only once), follow these steps.

## Configure Secrets Manager Secret

Create an AWS Secret that will contain the required tokens/credentials for connecting AWS and Meta APIs.
Manually configure the META TOKEN secret in AWS Secrets Manager with name `/{env}/aws-whatsapp-chatbot`, with these values:

- AWS_API_KEY_TOKEN (added in META and AWS side)
- META_TOKEN (taken from META side)
- META_FROM_PHONE_NUMBER_ID (taken from META side)

This can be done with the following AWS CLI command:

TODO: Add AWS CLI command with the example secret creation (with necessary keys/values template)
