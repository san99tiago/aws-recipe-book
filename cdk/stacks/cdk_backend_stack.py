# Built-in imports
import os
from typing import Optional

# External imports
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Tags,
    Duration,
    aws_cognito,
    aws_dynamodb,
    aws_lambda,
    aws_apigateway as aws_apigw,
    CfnOutput,
)
from constructs import Construct

# TODO: Migrate to constants or CDK.json
DNS_SUBDOMAIN = "recipes"


class BackendStack(Stack):
    """
    Class to create the backend resources, which includes the DynamoDB database,
    Lambda Functions, APIs, Roles and additional resources for the RECIPE app solution on AWS.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        main_resources_name: str,
        app_config: dict[str],
        **kwargs,
    ) -> None:
        """
        :param scope (Construct): Parent of this stack, usually an 'App' or a 'Stage', but could be any construct.
        :param construct_id (str): The construct ID of this stack (same as aws-cdk Stack 'construct_id').
        :param main_resources_name (str): The main unique identified of this stack.
        :param app_config (dict[str]): Dictionary with relevant configuration values for the stack.
        """
        super().__init__(scope, construct_id, **kwargs)

        # Input parameters
        self.construct_id = construct_id
        self.main_resources_name = main_resources_name
        self.app_config = app_config
        self.deployment_environment = self.app_config["deployment_environment"]

        # Main methods for the deployment
        self.create_dynamodb_table()
        self.create_cognito_user_pool()
        self.create_lambda_layers()
        self.create_lambda_functions()
        self.create_rest_api()
        self.configure_cognito_app_client()
        self.configure_rest_api_advanced()

        # Create CloudFormation outputs
        self.generate_cloudformation_outputs()

    def create_dynamodb_table(self):
        """
        Create DynamoDB table for the NoSQL data.
        """

        # Generic "PK" and "SK", to leverage Single-Table-Design
        self.dynamodb_table = aws_dynamodb.Table(
            self,
            "DynamoDB-Table",
            table_name=self.app_config["table_name"],
            partition_key=aws_dynamodb.Attribute(
                name="PK", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="SK", type=aws_dynamodb.AttributeType.STRING
            ),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        Tags.of(self.dynamodb_table).add("Name", self.app_config["table_name"])

    def create_cognito_user_pool(self):
        """
        Create Cognito User Pool for the RECIPE app.
        """
        self.cognito_user_pool = aws_cognito.UserPool(
            self,
            "Cognito-UserPool",
            user_pool_name=f"{self.main_resources_name}-user-pool-{self.deployment_environment}",
            sign_in_aliases=aws_cognito.SignInAliases(email=True, username=False),
            sign_in_case_sensitive=False,
            self_sign_up_enabled=True,
            auto_verify={
                "email": True,
            },
            user_verification=aws_cognito.UserVerificationConfig(
                email_subject=f"Verify your email for our {self.main_resources_name}!",
                email_body="Thanks for signing up! Your verification code is {####}",
                sms_message="Thanks for signing up! Your verification code is {####}",
                email_style=aws_cognito.VerificationEmailStyle.CODE,
            ),
            standard_attributes=aws_cognito.StandardAttributes(
                email=aws_cognito.StandardAttribute(required=True, mutable=False),
                fullname=aws_cognito.StandardAttribute(required=True, mutable=False),
                birthdate=aws_cognito.StandardAttribute(required=False, mutable=False),
                nickname=aws_cognito.StandardAttribute(required=False, mutable=True),
            ),
            custom_attributes={
                "isAdmin": aws_cognito.BooleanAttribute(mutable=False),
                "createdAt": aws_cognito.DateTimeAttribute(),
            },
            password_policy=aws_cognito.PasswordPolicy(
                min_length=6,
                require_lowercase=False,
                require_uppercase=False,
                require_digits=False,
                require_symbols=False,
            ),
            account_recovery=aws_cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Allows us to enable the Custom-UI for auth/validation purposes
        self.user_pool_domain = self.cognito_user_pool.add_domain(
            "Cognito-Domain",
            cognito_domain=aws_cognito.CognitoDomainOptions(
                domain_prefix=f"{self.main_resources_name}-{self.deployment_environment}"
            ),
        )

    def create_lambda_layers(self) -> None:
        """
        Create the Lambda layers that are necessary for the additional runtime
        dependencies of the Lambda Functions.
        """

        # Layer for "LambdaPowerTools" (for logging, traces, observability, etc)
        self.lambda_layer_powertools = aws_lambda.LayerVersion.from_layer_version_arn(
            self,
            "Layer-powertools",
            layer_version_arn=f"arn:aws:lambda:{self.region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:59",
        )

        # Layer for "common" Python requirements (fastapi, pydantic, ...)
        self.lambda_layer_common = aws_lambda.LayerVersion(
            self,
            "Layer-common",
            code=aws_lambda.Code.from_asset("lambda-layers/common/modules"),
            compatible_runtimes=[
                aws_lambda.Runtime.PYTHON_3_11,
            ],
            description="Lambda Layer for Python with <common> library",
            removal_policy=RemovalPolicy.DESTROY,
            compatible_architectures=[aws_lambda.Architecture.X86_64],
        )

    def create_lambda_functions(self) -> None:
        """
        Create the Lambda Functions for the solution.
        """
        # Get relative path for folder that contains Lambda function source
        # ! Note--> we must obtain parent dirs to create path (that"s why there is "os.path.dirname()")
        PATH_TO_LAMBDA_FUNCTION_FOLDER = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "backend",
        )

        # Lambda Function for managing CRUD operations on "Recipes"
        self.lambda_recipes_app: aws_lambda.Function = aws_lambda.Function(
            self,
            "Lambda-Recipes",
            runtime=aws_lambda.Runtime.PYTHON_3_11,
            function_name=f"{self.main_resources_name}-{self.deployment_environment}",
            handler="api/v1/main.handler",
            code=aws_lambda.Code.from_asset(PATH_TO_LAMBDA_FUNCTION_FOLDER),
            timeout=Duration.seconds(20),
            memory_size=512,
            environment={
                "ENVIRONMENT": self.app_config["deployment_environment"],
                "LOG_LEVEL": self.app_config["log_level"],
                "DYNAMODB_TABLE": self.dynamodb_table.table_name,
            },
            layers=[
                self.lambda_layer_powertools,
                self.lambda_layer_common,
            ],
        )

        self.dynamodb_table.grant_read_write_data(self.lambda_recipes_app)

    def create_rest_api(self):
        """
        Method to create the REST-API Gateway for exposing the "Recipes"
        functionalities.
        """
        rest_api_name = self.app_config["api_gw_name"]

        # TODO: enhance with dedicated construct helper/methods
        cognito_authorizer = aws_apigw.CognitoUserPoolsAuthorizer(
            self,
            "RESTAPI-CognitoAuthorizer",
            authorizer_name=f"{rest_api_name}-authorizer",
            cognito_user_pools=[self.cognito_user_pool],
            identity_source=aws_apigw.IdentitySource.header("Authorization"),
            results_cache_ttl=Duration.minutes(0),
        )

        self.api_method_options_public = aws_apigw.MethodOptions(
            api_key_required=False,
            authorization_type=aws_apigw.AuthorizationType.NONE,
            authorizer=None,
        )
        self.api_method_options_private = aws_apigw.MethodOptions(
            api_key_required=False,  # Disabled, as it will use cognito always
            authorization_type=aws_apigw.AuthorizationType.COGNITO,
            authorizer=cognito_authorizer,  # Only if Cognito is enabled
        )

        self.api = aws_apigw.LambdaRestApi(
            self,
            "RESTAPI",
            rest_api_name=rest_api_name,
            description=f"REST API Gateway for {self.main_resources_name}",
            handler=self.lambda_recipes_app,
            deploy_options=aws_apigw.StageOptions(
                stage_name=self.deployment_environment,
                description=f"REST API for {self.main_resources_name} in {self.deployment_environment} environment",
                metrics_enabled=True,
            ),
            default_cors_preflight_options=aws_apigw.CorsOptions(
                allow_origins=aws_apigw.Cors.ALL_ORIGINS,
                allow_methods=aws_apigw.Cors.ALL_METHODS,
                allow_headers=["*"],
                allow_credentials=True,
            ),
            endpoint_types=[aws_apigw.EndpointType.REGIONAL],
            cloud_watch_role=False,
            proxy=False,  # Proxy disabled to have more control
        )

    def configure_cognito_app_client(self):
        """
        Method to configure the Cognito App Client for the User Pool.
        """
        hosted_zone_name = self.app_config["hosted_zone_name"]
        domain_name = f"{DNS_SUBDOMAIN}.{hosted_zone_name}"
        self.redirect_uri = f"https://{domain_name}"
        self.app_client = self.cognito_user_pool.add_client(
            "Cognito-AppClient",
            user_pool_client_name=f"{self.main_resources_name}-app-client-{self.deployment_environment}",
            auth_flows=aws_cognito.AuthFlow(user_password=True, user_srp=True),
            o_auth=aws_cognito.OAuthSettings(
                flows=aws_cognito.OAuthFlows(
                    implicit_code_grant=True,  # Return tokens directly
                ),
                scopes=[
                    aws_cognito.OAuthScope.EMAIL,
                    aws_cognito.OAuthScope.COGNITO_ADMIN,
                ],
                callback_urls=[
                    # Note: when using frontend, replace to frontend home page
                    self.redirect_uri,
                ],
            ),
            id_token_validity=Duration.hours(8),
            access_token_validity=Duration.hours(8),
        )

    def configure_rest_api_advanced(self):
        """
        Method to configure the REST-API Gateway with resources and methods (advanced way).
        """

        # Define REST-API resources
        root_resource_api = self.api.root.add_resource("api")
        root_resource_v1 = root_resource_api.add_resource("v1")

        # Endpoints for automatic Swagger docs (no auth required)
        root_resource_docs: aws_apigw.Resource = root_resource_v1.add_resource(
            "docs",
            default_method_options=self.api_method_options_public,
        )
        root_resource_docs_proxy = root_resource_docs.add_resource("{path}")

        # Endpoints for "recipes"resources
        root_resource_recipes = root_resource_v1.add_resource(
            "recipes",
            default_method_options=self.api_method_options_private,
        )
        recipes_resource = root_resource_recipes.add_resource("{recipe_id}")

        # Define all API-Lambda integrations for the API methods
        api_lambda_integration_recipes = aws_apigw.LambdaIntegration(
            self.lambda_recipes_app
        )

        # API-Path: "/api/v1/recipes"
        root_resource_recipes.add_method("GET", api_lambda_integration_recipes)
        root_resource_recipes.add_method("POST", api_lambda_integration_recipes)

        # API-Path: "/api/v1/recipes/{recipe_id}"
        recipes_resource.add_method("GET", api_lambda_integration_recipes)
        recipes_resource.add_method("PATCH", api_lambda_integration_recipes)
        recipes_resource.add_method("DELETE", api_lambda_integration_recipes)

        # API-Path: "/api/v1/docs"
        root_resource_docs.add_method("GET", api_lambda_integration_recipes)

        # API-Path: "/api/v1/docs/openapi.json
        root_resource_docs_proxy.add_method("GET", api_lambda_integration_recipes)

    def generate_cloudformation_outputs(self) -> None:
        """
        Method to add the relevant CloudFormation outputs.
        """

        CfnOutput(
            self,
            "DeploymentEnvironment",
            value=self.app_config["deployment_environment"],
            description="Deployment environment",
        )

        CfnOutput(
            self,
            "BackendAPIUrl",
            value=f"https://{self.api.rest_api_id}.execute-api.{self.region}.amazonaws.com/{self.deployment_environment}/api/v1",
            description="BackendAPIUrl",
        )

        CfnOutput(
            self,
            "FrontendAPIUrl",
            value=f"https://{DNS_SUBDOMAIN}{self.app_config['hosted_zone_name']}",
            description="FrontendAPIUrl",
        )

        CfnOutput(
            self,
            "UserPoolId",
            value=self.cognito_user_pool.user_pool_id,
            description="UserPoolId",
        )

        CfnOutput(
            self,
            "ClientId",
            value=self.app_client.user_pool_client_id,
            description="ClientId",
        )

        CfnOutput(
            self,
            "CognitoHostedUIEndpoint",
            value=self.user_pool_domain.sign_in_url(
                self.app_client,
                redirect_uri=self.redirect_uri,
                sign_in_path="/oauth2/authorize",
            ),
            description="CognitoHostedUIEndpoint",
        )
