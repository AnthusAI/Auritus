"""Auritus backend CDK stack: API, DynamoDB mutex, Cognito, Batch fallback, budgets."""

from __future__ import annotations

from pathlib import Path

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    SecretValue,
    Stack,
)
from aws_cdk import (
    aws_apigatewayv2 as apigwv2,
)
from aws_cdk import (
    aws_apigatewayv2_authorizers as apigwv2_auth,
)
from aws_cdk import (
    aws_apigatewayv2_integrations as apigwv2_integrations,
)
from aws_cdk import (
    aws_batch as batch,
)
from aws_cdk import (
    aws_budgets as budgets,
)
from aws_cdk import (
    aws_cloudfront as cloudfront,
)
from aws_cdk import (
    aws_cloudfront_origins as origins,
)
from aws_cdk import (
    aws_cognito as cognito,
)
from aws_cdk import (
    aws_dynamodb as dynamodb,
)
from aws_cdk import (
    aws_ec2 as ec2,
)
from aws_cdk import (
    aws_ecr as ecr,
)
from aws_cdk import (
    aws_events as events,
)
from aws_cdk import (
    aws_events_targets as targets,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_lambda as lambda_,
)
from aws_cdk import (
    aws_logs as logs,
)
from aws_cdk import (
    aws_s3 as s3,
)
from aws_cdk import (
    aws_secretsmanager as secretsmanager,
)
from aws_cdk import (
    aws_sns as sns,
)
from aws_cdk import (
    aws_sns_subscriptions as sns_subscriptions,
)
from aws_cdk import (
    aws_stepfunctions as sfn,
)
from aws_cdk import (
    aws_stepfunctions_tasks as sfn_tasks,
)
from constructs import Construct

LAMBDA_ROOT = Path(__file__).resolve().parents[1] / "lambdas"
DEFAULT_CLAIM_TIMEOUT_SECONDS = 900


class BackendStack(Stack):
    """Cloud backend for Auritus just-in-time TTS generation."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        claim_timeout_seconds = int(
            self.node.try_get_context("claim_timeout_seconds")
            or DEFAULT_CLAIM_TIMEOUT_SECONDS
        )

        google_secret_arn = self.node.try_get_context("google_oauth_secret_arn")
        if google_secret_arn:
            google_secret = secretsmanager.Secret.from_secret_complete_arn(
                self,
                "GoogleOAuthSecret",
                google_secret_arn,
            )
        else:
            google_secret = secretsmanager.Secret(
                self,
                "GoogleOAuthSecret",
                description="Google OAuth client id/secret for Cognito IdP (placeholder)",
                secret_object_value={
                    "client_id": SecretValue.unsafe_plain_text("REPLACE_ME"),
                    "client_secret": SecretValue.unsafe_plain_text("REPLACE_ME"),
                },
            )

        jobs = dynamodb.Table(
            self,
            "AuritusJobs",
            partition_key=dynamodb.Attribute(
                name="content_hash",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            time_to_live_attribute="ttl",
        )
        jobs.add_global_secondary_index(
            index_name="status-created_at-index",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING,
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        sites = dynamodb.Table(
            self,
            "AuritusSites",
            partition_key=dynamodb.Attribute(
                name="site_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )
        sites.add_global_secondary_index(
            index_name="site_key-index",
            partition_key=dynamodb.Attribute(
                name="site_key",
                type=dynamodb.AttributeType.STRING,
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        audio_bucket = s3.Bucket(
            self,
            "AuritusAudio",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
        )

        distribution = cloudfront.Distribution(
            self,
            "AuritusAudioCdn",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin(audio_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            comment="Auritus audio CDN (signed URLs issued by API)",
        )

        user_pool = cognito.UserPool(
            self,
            "AuritusUsers",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=False)
            ),
            removal_policy=RemovalPolicy.RETAIN,
        )

        google_idp = cognito.UserPoolIdentityProviderGoogle(
            self,
            "GoogleIdP",
            user_pool=user_pool,
            client_id=google_secret.secret_value_from_json("client_id").unsafe_unwrap(),
            client_secret_value=google_secret.secret_value_from_json("client_secret"),
            scopes=["openid", "email", "profile"],
            attribute_mapping=cognito.AttributeMapping(
                email=cognito.ProviderAttribute.GOOGLE_EMAIL,
                fullname=cognito.ProviderAttribute.GOOGLE_NAME,
            ),
        )

        user_pool_client = cognito.UserPoolClient(
            self,
            "AuritusCliClient",
            user_pool=user_pool,
            generate_secret=False,
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.PROFILE,
                ],
                callback_urls=[
                    "http://127.0.0.1/callback",
                    "http://localhost/callback",
                ],
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.GOOGLE,
            ],
            auth_flows=cognito.AuthFlow(user_srp=True),
        )
        user_pool_client.node.add_dependency(google_idp)

        router_fn = lambda_.Function(
            self,
            "RouterFn",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=lambda_.Code.from_asset(str(LAMBDA_ROOT / "router")),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "JOBS_TABLE": jobs.table_name,
                "SITES_TABLE": sites.table_name,
                "AUDIO_BUCKET": audio_bucket.bucket_name,
                "CLOUDFRONT_DOMAIN": distribution.distribution_domain_name,
                "FALLBACK_SECONDS": str(claim_timeout_seconds),
                "DAILY_SITE_QUOTA": str(
                    self.node.try_get_context("daily_site_quota") or 100
                ),
            },
        )
        jobs.grant_read_write_data(router_fn)
        sites.grant_read_write_data(router_fn)
        audio_bucket.grant_read_write(router_fn)

        authorizer_fn = lambda_.Function(
            self,
            "AuthorizerFn",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=lambda_.Code.from_asset(str(LAMBDA_ROOT / "authorizer")),
            timeout=Duration.seconds(10),
            environment={
                "USER_POOL_ID": user_pool.user_pool_id,
                "CLIENT_ID": user_pool_client.user_pool_client_id,
            },
        )

        http_api = apigwv2.HttpApi(
            self,
            "AuritusApi",
            api_name="auritus-api",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_headers=[
                    "Authorization",
                    "Content-Type",
                    "X-Auritus-Site-Key",
                    "Origin",
                ],
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.POST,
                    apigwv2.CorsHttpMethod.PUT,
                    apigwv2.CorsHttpMethod.DELETE,
                    apigwv2.CorsHttpMethod.OPTIONS,
                ],
                allow_origins=["*"],
                max_age=Duration.days(1),
            ),
        )

        router_integration = apigwv2_integrations.HttpLambdaIntegration(
            "RouterIntegration",
            router_fn,
        )

        lambda_authorizer = apigwv2_auth.HttpLambdaAuthorizer(
            "OperatorAuthorizer",
            authorizer_fn,
            authorizer_name="AuritusOperatorAuthorizer",
            identity_source=["$request.header.Authorization"],
            response_types=[apigwv2_auth.HttpLambdaResponseType.SIMPLE],
        )

        for method, path in [
            (apigwv2.HttpMethod.POST, "/jobs"),
            (apigwv2.HttpMethod.GET, "/jobs/{hash}"),
            (apigwv2.HttpMethod.POST, "/jobs/{hash}/redeem"),
            (apigwv2.HttpMethod.PUT, "/jobs/{hash}/claim"),
            (apigwv2.HttpMethod.PUT, "/jobs/{hash}/done"),
            (apigwv2.HttpMethod.POST, "/jobs/{hash}/presign-upload"),
        ]:
            http_api.add_routes(
                path=path,
                methods=[method],
                integration=router_integration,
            )

        for method, path in [
            (apigwv2.HttpMethod.GET, "/jobs/claimable"),
        ]:
            http_api.add_routes(
                path=path,
                methods=[method],
                integration=router_integration,
                authorizer=lambda_authorizer,
            )

        for method, path in [
            (apigwv2.HttpMethod.POST, "/sites"),
            (apigwv2.HttpMethod.GET, "/sites"),
            (apigwv2.HttpMethod.DELETE, "/sites/{id}"),
        ]:
            http_api.add_routes(
                path=path,
                methods=[method],
                integration=router_integration,
                authorizer=lambda_authorizer,
            )

        worker_repo = ecr.Repository(
            self,
            "WorkerImageRepo",
            repository_name="auritus-worker",
            removal_policy=RemovalPolicy.RETAIN,
        )
        worker_image_tag = self.node.try_get_context("worker_image_tag") or "latest"
        worker_image_uri = f"{worker_repo.repository_uri}:{worker_image_tag}"

        vpc = ec2.Vpc(self, "AuritusVpc", max_azs=2, nat_gateways=1)
        batch_sg = ec2.SecurityGroup(self, "BatchSg", vpc=vpc, allow_all_outbound=True)
        instance_profile = self._batch_instance_profile()

        compute_env = batch.CfnComputeEnvironment(
            self,
            "GpuComputeEnv",
            type="MANAGED",
            compute_resources=batch.CfnComputeEnvironment.ComputeResourcesProperty(
                type="EC2",
                maxv_cpus=8,
                minv_cpus=0,
                desiredv_cpus=0,
                instance_types=["g4dn.xlarge"],
                allocation_strategy="BEST_FIT_PROGRESSIVE",
                subnets=[subnet.subnet_id for subnet in vpc.private_subnets],
                security_group_ids=[batch_sg.security_group_id],
                instance_role=instance_profile.attr_arn,
            ),
        )

        job_queue_name = "auritus-gpu"
        batch.CfnJobQueue(
            self,
            "AuritusJobQueueV2",
            job_queue_name=job_queue_name,
            priority=2,
            compute_environment_order=[
                batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    order=1,
                    compute_environment=compute_env.ref,
                )
            ],
            state="ENABLED",
        )
        job_queue_arn = Stack.of(self).format_arn(
            service="batch",
            resource="job-queue",
            resource_name=job_queue_name,
        )

        job_role = iam.Role(
            self,
            "BatchJobRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        jobs.grant_read_write_data(job_role)
        audio_bucket.grant_read_write(job_role)

        job_def = batch.CfnJobDefinition(
            self,
            "AuritusGpuJobDef",
            type="container",
            platform_capabilities=["EC2"],
            container_properties=batch.CfnJobDefinition.ContainerPropertiesProperty(
                image=worker_image_uri,
                vcpus=2,
                memory=8192,
                resource_requirements=[
                    batch.CfnJobDefinition.ResourceRequirementProperty(
                        type="GPU",
                        value="1",
                    )
                ],
                job_role_arn=job_role.role_arn,
                environment=[
                    batch.CfnJobDefinition.EnvironmentProperty(
                        name="AURITUS_API_ENDPOINT",
                        value=http_api.api_endpoint or "",
                    ),
                    batch.CfnJobDefinition.EnvironmentProperty(
                        name="AURITUS_JOBS_TABLE",
                        value=jobs.table_name,
                    ),
                    batch.CfnJobDefinition.EnvironmentProperty(
                        name="AURITUS_TTS_BACKEND",
                        value="kokoro",
                    ),
                ],
                log_configuration=batch.CfnJobDefinition.LogConfigurationProperty(
                    log_driver="awslogs"
                ),
            ),
        )

        wait = sfn.Wait(
            self,
            "WaitForLocalWorker",
            time=sfn.WaitTime.duration(Duration.seconds(claim_timeout_seconds)),
        )

        get_job = sfn_tasks.DynamoGetItem(
            self,
            "GetJobStatus",
            table=jobs,
            key={
                "content_hash": sfn_tasks.DynamoAttributeValue.from_string(
                    sfn.JsonPath.string_at("$.content_hash")
                )
            },
            result_path="$.job",
        )

        estimate_now = sfn.Pass(
            self,
            "EstimateNowEpoch",
            parameters={
                "content_hash.$": "$.content_hash",
                "job_token.$": "$.job_token",
                "tts_backend.$": "$.tts_backend",
                "job.$": "$.job",
                "now_epoch.$": "States.Format('{}', States.MathAdd($.baseline_epoch, $.fallback_seconds))",
            },
        )

        submit_batch = sfn_tasks.BatchSubmitJob(
            self,
            "SubmitGpuJob",
            job_name=sfn.JsonPath.format(
                "auritus-{}",
                sfn.JsonPath.string_at("$.content_hash"),
            ),
            job_definition_arn=job_def.ref,
            job_queue_arn=job_queue_arn,
            container_overrides=sfn_tasks.BatchContainerOverrides(
                environment={
                    "AURITUS_CONTENT_HASH": sfn.JsonPath.string_at("$.content_hash"),
                    "AURITUS_JOB_TOKEN": sfn.JsonPath.string_at("$.job_token"),
                    "AURITUS_TTS_BACKEND": sfn.JsonPath.string_at("$.tts_backend"),
                }
            ),
            result_path="$.batch",
        )

        still_open = sfn.Choice(self, "PendingOrStale")
        succeed = sfn.Succeed(self, "LocalWorkerOwnsJob")

        definition = (
            wait.next(get_job)
            .next(estimate_now)
            .next(
                still_open.when(
                    sfn.Condition.string_equals("$.job.Item.status.S", "pending"),
                    submit_batch,
                )
                .when(
                    sfn.Condition.and_(
                        sfn.Condition.string_equals("$.job.Item.status.S", "claimed"),
                        sfn.Condition.string_less_than(
                            "$.job.Item.claim_deadline.N",
                            sfn.JsonPath.string_at("$.now_epoch"),
                        ),
                    ),
                    submit_batch,
                )
                .otherwise(succeed)
            )
        )

        fallback = sfn.StateMachine(
            self,
            "AuritusFallback",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            timeout=Duration.hours(2),
            logs=sfn.LogOptions(
                destination=logs.LogGroup(
                    self,
                    "FallbackLogs",
                    retention=logs.RetentionDays.ONE_MONTH,
                    removal_policy=RemovalPolicy.DESTROY,
                ),
                level=sfn.LogLevel.ERROR,
            ),
        )
        router_fn.add_environment(
            "FALLBACK_STATE_MACHINE_ARN",
            fallback.state_machine_arn,
        )
        router_fn.add_environment("BATCH_JOB_QUEUE_NAME", job_queue_name)
        fallback.grant_start_execution(router_fn)

        budget_topic = sns.Topic(self, "AuritusBudgetTopic")
        budget_guard_fn = lambda_.Function(
            self,
            "BudgetGuardFn",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=lambda_.Code.from_asset(str(LAMBDA_ROOT / "budget_guard")),
            timeout=Duration.seconds(30),
            environment={
                "BATCH_JOB_QUEUE_ARN": job_queue_arn,
                "BATCH_JOB_QUEUE_NAME": job_queue_name,
            },
        )
        budget_guard_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["batch:UpdateJobQueue", "batch:DescribeJobQueues"],
                resources=["*"],
            )
        )

        budget_topic.grant_publish(iam.ServicePrincipal("budgets.amazonaws.com"))
        budget_topic.add_subscription(
            sns_subscriptions.LambdaSubscription(budget_guard_fn)
        )

        events.Rule(
            self,
            "BudgetAlarmRule",
            event_pattern=events.EventPattern(source=["aws.budgets"]),
            targets=[targets.LambdaFunction(budget_guard_fn)],
        )

        daily_budget_limit = float(
            self.node.try_get_context("daily_budget_usd") or 50.0
        )
        budgets.CfnBudget(
            self,
            "DailyGpuBudget",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_type="COST",
                time_unit="DAILY",
                budget_limit=budgets.CfnBudget.SpendProperty(
                    amount=daily_budget_limit,
                    unit="USD",
                ),
                budget_name="AuritusDailyGpuBudget",
            ),
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="ACTUAL",
                        threshold=100,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=budget_topic.topic_arn,
                            subscription_type="SNS",
                        )
                    ],
                )
            ],
        )

        CfnOutput(self, "ApiUrl", value=http_api.api_endpoint or "")
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)
        CfnOutput(self, "JobsTableName", value=jobs.table_name)
        CfnOutput(self, "SitesTableName", value=sites.table_name)
        CfnOutput(self, "AudioBucketName", value=audio_bucket.bucket_name)
        CfnOutput(self, "CloudFrontDomain", value=distribution.distribution_domain_name)
        CfnOutput(self, "BatchQueueArn", value=job_queue_arn)
        CfnOutput(self, "ClaimTimeoutSeconds", value=str(claim_timeout_seconds))
        CfnOutput(self, "WorkerEcrRepositoryUri", value=worker_repo.repository_uri)
        CfnOutput(self, "GoogleOAuthSecretArn", value=google_secret.secret_arn)

    def _batch_instance_profile(self) -> iam.CfnInstanceProfile:
        """Create an EC2 instance profile for AWS Batch GPU workers.

        :returns: Instance profile for the Batch compute environment.
        """
        role = iam.Role(
            self,
            "BatchInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2ContainerServiceforEC2Role"
                )
            ],
        )
        return iam.CfnInstanceProfile(
            self,
            "BatchInstanceProfile",
            roles=[role.role_name],
        )
