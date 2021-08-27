from aws_cdk import (
    core as cdk,
    aws_lambda as lambda_,
    aws_lambda_python as lambda_python,
    aws_events as events,
    aws_events_targets as events_targets,
)
import typing


class AwsCliPackageUpdaterStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        check_frequency = cdk.Duration.hours(1)

        updater_lambda = lambda_python.PythonFunction(self, "updater_fn", entry="src")

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
