from aws_cdk import (
    core as cdk,
    aws_lambda as lambda_,
    aws_lambda_python as lambda_python,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_secretsmanager as sm,
    aws_iam as iam,
)
import typing


class AwsCliPackageUpdaterStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        check_frequency = cdk.Duration.hours(1)

        secret_name = "misc/ssh_keys/aur"
        private_ssh_key = sm.Secret.from_secret_name_v2(
            self, "ssh_key", secret_name=secret_name
        )

        # https://github.com/lambci/git-lambda-layer
        git_layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            "git",
            layer_version_arn=f"arn:aws:lambda:{self.region}:553035198032:layer:git-lambda2:8",
        )

        updater_lambda = lambda_python.PythonFunction(
            self,
            "updater_fn",
            entry="src",
            environment={"SSH_KEY_SECRET_NAME": secret_name},
            runtime=typing.cast(lambda_.Runtime, lambda_.Runtime.PYTHON_3_8),
            timeout=cdk.Duration.seconds(10),
            layers=[git_layer],
        )

        private_ssh_key.grant_read(typing.cast(iam.Role, updater_lambda.role))

        event_target = events_targets.LambdaFunction(
            handler=typing.cast(lambda_.IFunction, updater_lambda),
            event=events.RuleTargetInput.from_text("trigger"),
            retry_attempts=1,
        )

        trigger_rule = events.Rule(
            self,
            "trigger",
            schedule=events.Schedule.rate(check_frequency),
            targets=[typing.cast(events.IRuleTarget, event_target)],
        )
