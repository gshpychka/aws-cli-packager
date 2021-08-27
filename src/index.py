import requests

def handler(event, context):
    
    response = requests.get("https://api.github.com/repos/aws/aws-cli/tags")

    data = response.json()

    print(data)

    latest_tag = data[0]

    print(latest_tag)

    print(f"Latest version is {latest_tag['name']}")
