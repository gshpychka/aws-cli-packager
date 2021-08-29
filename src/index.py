import requests
import hashlib
import urllib
import boto3
import re

import os
import subprocess
import typing


def get_secret_string(secret_name: str) -> str:
    sm = boto3.client("secretsmanager")

    secret_response = sm.get_secret_value(SecretId=secret_name)

    assert "SecretString" in secret_response

    secret_string = secret_response["SecretString"]

    return secret_string


def parse_agent_env(agent_output: str) -> typing.Dict[str, str]:

    agent_env = {}
    for name, value in re.findall(f"([A-Z_]+)=([^;]+);", agent_output):
        agent_env[name] = value
    return agent_env


def setup_ssh_key_get_env(secret_name: str) -> typing.Dict[str, str]:
    ssh_private_key = get_secret_string(secret_name=secret_name)
    ssh_private_key_lines = ssh_private_key.split("\\n")

    key_file_path = "/tmp/ssh_private_key"
    with open(key_file_path, "w") as key_file:
        key_file.writelines(ssh_private_key_lines)

    os.chmod(key_file_path, 0o600)

    # agent_output = subprocess.run(
    #     ["ssh-agent", "-s"], check=True, shell=True, text=True, capture_output=True
    # ).stdout

    # agent_env = parse_agent_env(agent_output=agent_output)
    env = {}
    env.update(os.environ)
    # env.update(agent_env)
    env["GIT_SSH_COMMAND"] = f"ssh -i {key_file_path} -o StrictHostKeyChecking=no"
    # subprocess.run(f"ssh-add {key_file_path}", env=env, check=True, shell=True)
    return env


def update_remote_repo(
    git_repo_url: str, latest_version: str, sha256sum: str, env: typing.Dict[str, str]
) -> None:

    clone_path = "/tmp/remote_repo"
    try:

        subprocess.run(
            f"git clone --depth 1 {git_repo_url} {clone_path}",
            check=True,
            shell=True,
            universal_newlines=True,
            env=env,
        )

        print(f"Repo cloned")
    except subprocess.CalledProcessError as ex:
        print(f"Clone failed: {ex.output}")

    with open("PKGBUILD_template", "r") as template:
        filled_in = (
            template.read()
            .replace("{pkgver}", latest_version)
            .replace("{sha256sums}", sha256sum)
        )

    with open(os.path.join(clone_path, "PKGBUILD"), "w") as pkgbuild:
        pkgbuild.write(filled_in)

    with open("SRCINFO_template", "r") as template:
        filled_in = (
            template.read()
            .replace("{pkgver}", latest_version)
            .replace("{sha256sums}", sha256sum)
        )

    with open(os.path.join(clone_path, ".SRCINFO"), "w") as srcinfo:
        srcinfo.write(filled_in)

    subprocess.run(
        f"cd {clone_path}" + " && git add PKGBUILD" + " && git add .SRCINFO",
        check=True,
        shell=True,
    )
    subprocess.run(
        f"cd {clone_path}"
        + ' && git config user.email "glibshpychka@gmail.com"'
        + ' && git config user.name "Glib Shpychka"',
        check=True,
        shell=True,
    )
    subprocess.run(
        f"cd {clone_path} && git commit -m 'Updated to version {latest_version}'",
        check=True,
        shell=True,
    )
    try:
        subprocess.run(
            f"cd {clone_path}" + " && git push", check=True, shell=True, env=env
        )
    except subprocess.CalledProcessError as ex:
        print(f"Push failed: {ex.output}")


def get_latest_version(github_api_url: str) -> str:

    response = requests.get(github_api_url)

    data = response.json()

    latest_version = data[0]["name"]

    return latest_version


def calculate_sha256(bin_url: str) -> str:
    remote = urllib.request.urlopen(bin_url)
    hash = hashlib.sha256()
    total_read = 0
    chunk_size = 4096
    while True:
        data = remote.read(chunk_size)
        total_read += chunk_size

        if not data:
            break
        hash.update(data)

    return hash.hexdigest()


def handler(event, context):

    github_api_url = "https://api.github.com/repos/aws/aws-cli/tags"
    bin_url_template = (
        "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-{latest_version}.zip"
    )
    package_name = "aws-cli-v2-bin"
    # remote_repo_url = f"ssh://aur@aur.archlinux.org/{package_name}.git"
    remote_repo_url = f"ssh://git@github.com/gshpychka/aur-{package_name}.git"
    secret_name = os.environ["SSH_KEY_SECRET_NAME"]
    latest_version = get_latest_version(github_api_url=github_api_url)

    print(f"Latest version is {latest_version}")
    bin_url = bin_url_template.format(latest_version=latest_version)
    print(f"Bin URL is {bin_url}")

    sha256sum = calculate_sha256(bin_url=bin_url)

    print(sha256sum)

    env = setup_ssh_key_get_env(secret_name=secret_name)

    update_remote_repo(
        git_repo_url=remote_repo_url,
        latest_version=latest_version,
        sha256sum=sha256sum,
        env=env,
    )
