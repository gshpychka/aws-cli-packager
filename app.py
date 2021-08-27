#!/usr/bin/env python3

from aws_cdk import core as cdk

from infrastructure.updater_stack import AwsCliPackageUpdaterStack 

app = cdk.App()
AwsCliPackageUpdaterStack(
    app,
    "AwsCliPackageUpdaterStack",
)

app.synth()
