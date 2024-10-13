# Built-in imports
import os

# External imports
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_certificatemanager,
    aws_cloudfront,
    aws_cloudfront_origins,
    aws_route53,
    aws_route53_targets,
    aws_s3,
    aws_s3_deployment,
    RemovalPolicy,
    Duration,
)
from constructs import Construct

# TODO: Migrate to constants or CDK.json
DNS_SUBDOMAIN = "recipes"


class FrontendStack(Stack):
    """
    Class to create the Frontend resources, which includes an S3 bucket and
    some deployments (future: include CloudFront, Route53, etc.).
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

        # Main methods for the deployment
        self.create_s3_buckets()
        self.upload_objects_to_s3()
        self.import_route_53_hosted_zone()
        self.configure_acm_certificate()
        self.configure_cloudfront_distribution()
        self.configure_route_53_records()

        # Create CloudFormation outputs
        self.generate_cloudformation_outputs()

    def create_s3_buckets(self):
        """
        Method to create S3 buckets.
        """
        self.bucket = aws_s3.Bucket(
            self,
            "Bucket",
            website_index_document="index.html",
            website_error_document="index.html",
            public_read_access=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=aws_s3.BlockPublicAccess(
                block_public_policy=False,
                restrict_public_buckets=False,
                ignore_public_acls=False,
                block_public_acls=False,
            ),
        )

    def upload_objects_to_s3(self):
        """
        Method to upload object/files to S3 bucket at deployment.
        """
        PATH_TO_S3_FOLDER = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "frontend",
            "build",
        )

        aws_s3_deployment.BucketDeployment(
            self,
            "S3Deployment1",
            sources=[aws_s3_deployment.Source.asset(PATH_TO_S3_FOLDER)],
            destination_bucket=self.bucket,
        )

    def import_route_53_hosted_zone(self):
        """
        Method to import the Route 53 hosted zone for the application.
        """
        # IMPORTANT: The hosted zone must be already created in Route 53!
        self.hosted_zone_name = self.app_config["hosted_zone_name"]
        self.domain_name = f"{DNS_SUBDOMAIN}.{self.hosted_zone_name}"
        self.hosted_zone = aws_route53.HostedZone.from_lookup(
            self,
            "HostedZone",
            domain_name=self.hosted_zone_name,
        )

    def configure_acm_certificate(self):
        """
        Method to configure the SSL certificate for the frontend.
        """
        self.certificate = aws_certificatemanager.Certificate(
            self,
            "Certificate",
            domain_name=self.domain_name,
            validation=aws_certificatemanager.CertificateValidation.from_dns(
                hosted_zone=self.hosted_zone,
            ),
            subject_alternative_names=[f"*.{self.domain_name}"],
        )

    def configure_cloudfront_distribution(self):
        """
        Method to configure the CloudFront distribution for the frontend.
        """
        cloudfront_origin_access_identity = aws_cloudfront.OriginAccessIdentity(
            self,
            "CloudFrontOriginAccessIdentity",
            comment=f"Origin Access Identity for the s3 frontend for {self.main_resources_name}",
        )
        self.bucket.grant_read(cloudfront_origin_access_identity)

        # TODO: enhance with better security headers (such as strictTransport, xss, etc)
        response_response_header_policy = aws_cloudfront.ResponseHeadersPolicy(
            self,
            "SecurityResponseHeadersPolicy",
            comment=f"Response Headers Policy for the s3 frontend for {self.main_resources_name}",
            response_headers_policy_name=f"ResponseHeadersPolicy-{self.main_resources_name}",
            security_headers_behavior=aws_cloudfront.ResponseSecurityHeadersBehavior(
                content_security_policy=aws_cloudfront.ResponseHeadersContentSecurityPolicy(
                    content_security_policy="default-src https:;", override=True
                ),
                content_type_options=aws_cloudfront.ResponseHeadersContentTypeOptions(
                    override=True
                ),
                frame_options=aws_cloudfront.ResponseHeadersFrameOptions(
                    frame_option=aws_cloudfront.HeadersFrameOption.DENY, override=True
                ),
                referrer_policy=aws_cloudfront.ResponseHeadersReferrerPolicy(
                    referrer_policy=aws_cloudfront.HeadersReferrerPolicy.NO_REFERRER,
                    override=True,
                ),
                strict_transport_security=aws_cloudfront.ResponseHeadersStrictTransportSecurity(
                    access_control_max_age=Duration.seconds(600),
                    include_subdomains=True,
                    override=True,
                ),
                xss_protection=aws_cloudfront.ResponseHeadersXSSProtection(
                    protection=True,
                    mode_block=False,
                    report_uri="https://example.com/csp-report",
                    override=True,
                ),
            ),
            cors_behavior=aws_cloudfront.ResponseHeadersCorsBehavior(
                # # TODO: Update to a more restrictive control
                access_control_allow_origins=["*"],
                access_control_allow_methods=[
                    "GET",
                    "HEAD",
                    "OPTIONS",
                    "PATCH",
                    "POST",
                    "DELETE",
                ],
                access_control_allow_headers=["*"],  # TODO: Restrict more if needed
                access_control_allow_credentials=True,
                origin_override=True,  # If CloudFront overrides origin CORS headers
            ),
        )

        self.cloudfront_distribution = aws_cloudfront.Distribution(
            self,
            "CloudFrontDistribution",
            comment=f"CloudFront Distribution for the s3 frontend for {self.main_resources_name}",
            domain_names=[self.domain_name, f"www.{self.domain_name}"],
            certificate=self.certificate,
            default_behavior=aws_cloudfront.BehaviorOptions(
                origin=aws_cloudfront_origins.S3Origin(
                    self.bucket,
                    origin_access_identity=cloudfront_origin_access_identity,
                ),
                viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                response_headers_policy=response_response_header_policy,
            ),
            default_root_object="index.html",
            error_responses=[
                aws_cloudfront.ErrorResponse(
                    http_status=404,
                    ttl=Duration.seconds(1),
                    response_page_path="/index.html",
                )
            ],
            enabled=True,
        )

    def configure_route_53_records(self):
        """
        Method to configure the Route 53 records for the frontend.
        """
        # Create the main route 53 record
        aws_route53.ARecord(
            self,
            "Route53ARecord",
            comment=f"Route 53 A Record for the s3 frontend for {self.main_resources_name}",
            zone=self.hosted_zone,
            target=aws_route53.RecordTarget.from_alias(
                aws_route53_targets.CloudFrontTarget(self.cloudfront_distribution)
            ),
            record_name=self.domain_name,
        )

        # Create the WWW route 53 record
        aws_route53.ARecord(
            self,
            "Route53WWWRecord",
            comment=f"Route 53 WWW Record for the s3 frontend for {self.main_resources_name}",
            zone=self.hosted_zone,
            target=aws_route53.RecordTarget.from_alias(
                aws_route53_targets.CloudFrontTarget(self.cloudfront_distribution)
            ),
            record_name=f"www.{self.domain_name}",
        )

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
            "S3BucketEndpointHTTP",
            value=self.bucket.bucket_website_url,
            description="Deployment environment",
        )
