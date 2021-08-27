import requests
import hashlib
import urllib

def handler(event, context):
    
    response = requests.get("https://api.github.com/repos/aws/aws-cli/tags")

    data = response.json()


    latest_version = data[0]['name']


    print(f"Latest version is {latest_version}")
    source_url = f"https://awscli.amazonaws.com/awscli-exe-linux-x86_64-{latest_version}.zip"
    print(f"Bin URL is {source_url}")
    
    remote = urllib.request.urlopen(source_url)
    hash = hashlib.sha256()
    total_read = 0
    chunk_size = 4096
    while True:
        data = remote.read(chunk_size)
        total_read += chunk_size
        
        if not data:
            break
        hash.update(data)
    print(hash.hexdigest())
