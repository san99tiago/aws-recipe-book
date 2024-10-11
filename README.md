# :poultry_leg: AWS-RECIPE-BOOK :poultry_leg:

Advanced Serverless DEMO to illustrate a "recipe book" solution deployed on AWS with the following microservices/components:

## General Architecture

<img src="assets/aws-santi-architecture-main.png" width=90%> <br>

- Frontend: React App deployed on S3 + CloudFront + Route 53.
- Backend: API-Gateway + Lambda + S3 + DynamoDB.
- Chatbot: Built on top of Meta with Webhook + API connected to AWS. Generative-AI capabilities with Bedrock Agents and Bedrock KB.
- Infrastructure as Code: Managed with CDK-Python and deployed as independent stacks.
- CI/CD: GitHub Actions with IAM OIDC connector (Password-less)

## CI/CD Architecture

<img src="assets/aws-santi-architecture-cicd.png" width=90%> <br>

## Important Notes

> This is NOT intended to be used in production grade workflows. It's an advanced DEMO that showcase an interesting workflow driven by 3 microservices deployed on AWS Cloud.

## Author 🎹

### Santiago Garcia Arango

<table border="1">
    <tr>
        <td>
            <p align="center">Curious DevSecOps Engineer passionate about advanced cloud-based solutions and deployments in AWS. I am convinced that today's greatest challenges must be solved by people that love what they do.</p>
        </td>
        <td>
            <p align="center"><img src="assets/SantiagoGarciaArango_AWS.png" width=80%></p>
        </td>
    </tr>
</table>

## LICENSE

Copyright 2024 Santiago Garcia Arango.
