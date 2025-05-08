#!/usr/bin/env python3
import os
import json
from datetime import datetime
from aws_cdk import custom_resources as cr

from aws_cdk import (
    App,
    Stack,
    Duration,
    RemovalPolicy,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_budgets as budgets,
    CfnOutput,
    CfnParameter,
)
from constructs import Construct


class FreeTierAlertsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 파라미터 정의
        account_creation_date = CfnParameter(
            self,
            "AccountCreationDate",
            type="String",
            description="AWS 계정 생성 일자 (YYYY-MM-DD 형식)",
            default="2024-04-25",  # 실제 계정 생성 일자로 변경하세요
        )

        email_address = CfnParameter(
            self,
            "EmailAddress",
            type="String",
            description="알림을 받을 이메일 주소",
            default="your-email@example.com",  # ***알림을 받을 이메일 주소로 변경하세요***
        )

        # 기존 IAM 사용자 파라미터 추가
        existing_user_name = CfnParameter(
            self,
            "ExistingUserArn",
            type="String",
            description="기존 IAM 사용자 이름 **arn 적지 말아요 **",
            default="",
        )

        # 프리티어 종료 알림을 위한 SNS 토픽 생성
        freetier_expiration_topic = sns.Topic(
            self, "FreeTierExpirationAlert", topic_name="freetier-expiration-alert"
        )

        # SNS 토픽 구독 설정 (이메일)
        freetier_expiration_topic.add_subscription(
            subscriptions.EmailSubscription(email_address.value_as_string)
        )

        # Lambda 함수 생성
        freetier_expiration_lambda = lambda_.Function(
            self,
            "FreeTierExpirationCheck",
            function_name="freetier-expiration-check",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="freetier_expiration_check.handler",
            code=lambda_.Code.from_asset("lambda"),
            timeout=Duration.seconds(10),
            environment={
                "ACCOUNT_CREATION_DATE": account_creation_date.value_as_string,
                "SNS_TOPIC_ARN": freetier_expiration_topic.topic_arn,
            },
        )

        # SNS 토픽에 게시 권한 부여
        freetier_expiration_topic.grant_publish(freetier_expiration_lambda)

        # CloudWatch 이벤트 규칙 생성 (매일 오전 9시에 실행)
        rule = events.Rule(
            self,
            "FreeTierExpirationReminder",
            rule_name="freetier-expiration-reminder",
            description="프리티어 종료 알림을 위한 CloudWatch 이벤트 규칙",
            schedule=events.Schedule.cron(hour="9", minute="0"),
        )

        # Lambda 함수를 이벤트 대상으로 추가
        rule.add_target(targets.LambdaFunction(freetier_expiration_lambda))

        # 예산 알림을 위한 SNS 토픽 생성
        budget_alert_topic = sns.Topic(self, "BudgetAlert", topic_name="budget-alert")

        # 예산 알림 SNS 토픽 구독 설정 (이메일)
        budget_alert_topic.add_subscription(
            subscriptions.EmailSubscription(email_address.value_as_string)
        )

        # 프리티어 예산 설정 (월별)
        budgets.CfnBudget(
            self,
            "FreeTierMonthlyBudget",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_type="COST",
                time_unit="MONTHLY",
                budget_limit=budgets.CfnBudget.SpendProperty(amount=10, unit="USD"),
            ),
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="ACTUAL",
                        threshold=80,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=email_address.value_as_string,
                            subscription_type="EMAIL",
                        ),
                        budgets.CfnBudget.SubscriberProperty(
                            address=budget_alert_topic.topic_arn,
                            subscription_type="SNS",
                        ),
                    ],
                ),
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="ACTUAL",
                        threshold=100,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=email_address.value_as_string,
                            subscription_type="EMAIL",
                        ),
                        budgets.CfnBudget.SubscriberProperty(
                            address=budget_alert_topic.topic_arn,
                            subscription_type="SNS",
                        ),
                    ],
                ),
            ],
        )

        # EC2 서비스별 예산 설정
        budgets.CfnBudget(
            self,
            "EC2MonthlyBudget",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_type="COST",
                time_unit="MONTHLY",
                budget_limit=budgets.CfnBudget.SpendProperty(amount=1, unit="USD"),
                cost_filters={"Service": ["Amazon Elastic Compute Cloud - Compute"]},
            ),
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="ACTUAL",
                        threshold=80,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=email_address.value_as_string,
                            subscription_type="EMAIL",
                        ),
                        budgets.CfnBudget.SubscriberProperty(
                            address=budget_alert_topic.topic_arn,
                            subscription_type="SNS",
                        ),
                    ],
                )
            ],
        )

        # S3 서비스별 예산 설정
        budgets.CfnBudget(
            self,
            "S3MonthlyBudget",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_type="COST",
                time_unit="MONTHLY",
                budget_limit=budgets.CfnBudget.SpendProperty(amount=0.5, unit="USD"),
                cost_filters={"Service": ["Amazon Simple Storage Service"]},
            ),
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="ACTUAL",
                        threshold=80,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=email_address.value_as_string,
                            subscription_type="EMAIL",
                        ),
                        budgets.CfnBudget.SubscriberProperty(
                            address=budget_alert_topic.topic_arn,
                            subscription_type="SNS",
                        ),
                    ],
                )
            ],
        )

        # RDS 서비스별 예산 설정
        budgets.CfnBudget(
            self,
            "RDSMonthlyBudget",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_type="COST",
                time_unit="MONTHLY",
                budget_limit=budgets.CfnBudget.SpendProperty(amount=1, unit="USD"),
                cost_filters={"Service": ["Amazon Relational Database Service"]},
            ),
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="ACTUAL",
                        threshold=80,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=email_address.value_as_string,
                            subscription_type="EMAIL",
                        ),
                        budgets.CfnBudget.SubscriberProperty(
                            address=budget_alert_topic.topic_arn,
                            subscription_type="SNS",
                        ),
                    ],
                )
            ],
        )

        # 프리티어 리소스만 생성 가능한 IAM 정책 생성
        freetier_admin_policy = iam.ManagedPolicy(
            self,
            "FreeTierAdminPolicy",
            managed_policy_name="FreeTierAdminPolicy",
            description="프리티어 리소스만 생성 가능하고 나머지는 관리자 권한을 가진 정책",
            statements=[
                iam.PolicyStatement(
                    sid="AdminAccess",
                    effect=iam.Effect.ALLOW,
                    actions=["*"],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="DenyNonFreeTierEC2Instances",
                    effect=iam.Effect.DENY,
                    actions=["ec2:RunInstances"],
                    resources=["arn:aws:ec2:*:*:instance/*"],
                    conditions={
                        "StringNotEquals": {
                            "ec2:InstanceType": ["t2.micro", "t3.micro"]
                        }
                    },
                ),
                iam.PolicyStatement(
                    sid="DenyNonFreeTierRDS",
                    effect=iam.Effect.DENY,
                    actions=["rds:CreateDBInstance"],
                    resources=["*"],
                    conditions={
                        "StringNotLike": {
                            "rds:DatabaseClass": ["db.t2.micro", "db.t3.micro"]
                        }
                    },
                ),
                iam.PolicyStatement(
                    sid="DenyLargeS3Storage",
                    effect=iam.Effect.DENY,
                    actions=["s3:PutObject"],
                    resources=["*"],
                    conditions={
                        "NumericGreaterThan": {"s3:TotalObjectSize": 5368709120}  # 5GB
                    },
                ),
                iam.PolicyStatement(
                    sid="DenyLargeDynamoDBTables",
                    effect=iam.Effect.DENY,
                    actions=["dynamodb:CreateTable"],
                    resources=["*"],
                    conditions={
                        "NumericGreaterThan": {
                            "dynamodb:ProvisionedReadCapacityUnits": 25,
                            "dynamodb:ProvisionedWriteCapacityUnits": 25,
                        }
                    },
                ),
                iam.PolicyStatement(
                    sid="DenyLambdaWithHighMemory",
                    effect=iam.Effect.DENY,
                    actions=[
                        "lambda:CreateFunction",
                        "lambda:UpdateFunctionConfiguration",
                    ],
                    resources=["*"],
                    conditions={"NumericGreaterThan": {"lambda:MemorySize": 512}},
                ),
            ],
        )

        # MFA 정책 생성
        with open("mfa_only.json", "r") as f:
            mfa_policy_document = json.load(f)
        
        mfa_policy = iam.ManagedPolicy(self, "MFAOnlyPolicy",
            managed_policy_name="MFAOnlyPolicy",
            description="MFA 필수 정책",
            document=iam.PolicyDocument.from_json(mfa_policy_document)
        )

        # 사용자 이름 추출
        username = existing_user_name.value_as_string.split("/")[-1]

        # 프리티어 정책 연결
        attach_freetier_policy = cr.AwsCustomResource(
            self,
            "AttachFreeTierPolicy",
            on_create=cr.AwsSdkCall(
                service="IAM",
                action="attachUserPolicy",
                parameters={
                    "UserName": username,
                    "PolicyArn": freetier_admin_policy.managed_policy_arn,
                },
                physical_resource_id=cr.PhysicalResourceId.of("AttachFreeTierPolicyToUser"),
            ),
            on_delete=cr.AwsSdkCall(
                service="IAM",
                action="detachUserPolicy",
                parameters={
                    "UserName": username,
                    "PolicyArn": freetier_admin_policy.managed_policy_arn,
                },
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )
        
        # MFA 정책 연결
        attach_mfa_policy = cr.AwsCustomResource(
            self,
            "AttachMFAPolicy",
            on_create=cr.AwsSdkCall(
                service="IAM",
                action="attachUserPolicy",
                parameters={
                    "UserName": username,
                    "PolicyArn": mfa_policy.managed_policy_arn,
                },
                physical_resource_id=cr.PhysicalResourceId.of("AttachMFAPolicyToUser"),
            ),
            on_delete=cr.AwsSdkCall(
                service="IAM",
                action="detachUserPolicy",
                parameters={
                    "UserName": username,
                    "PolicyArn": mfa_policy.managed_policy_arn,
                },
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )

        # 출력값 정의
        CfnOutput(
            self,
            "FreeTierExpirationTopicArn",
            value=freetier_expiration_topic.topic_arn,
            description="프리티어 종료 알림 SNS 토픽 ARN",
        )

        CfnOutput(
            self,
            "BudgetAlertTopicArn",
            value=budget_alert_topic.topic_arn,
            description="예산 알림 SNS 토픽 ARN",
        )

        CfnOutput(
            self,
            "FreeTierAdminPolicyArn",
            value=freetier_admin_policy.managed_policy_arn,
            description="프리티어 관리자 정책 ARN",
        )
        
        CfnOutput(
            self,
            "MFAOnlyPolicyArn",
            value=mfa_policy.managed_policy_arn,
            description="MFA 필수 정책 ARN",
        )

        CfnOutput(
            self,
            "AttachedUserArn",
            value=existing_user_name.value_as_string,
            description="정책이 연결된 사용자 ARN",
        )


app = App()
FreeTierAlertsStack(app, "FreeTierAlertsStack")
app.synth()
