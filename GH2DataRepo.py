from dotenv import load_dotenv
import os
import requests
import base64
import json

load_dotenv()

GITHUB_API_URL = "https://api.github.com"
GH2DataRepoToken = os.getenv("GH2DataRepoToken")
GH2DataRepo= os.getenv("GH2DataRepo")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

HEADERS = {
    "Authorization": f"token {GH2DataRepoToken}",
    "Accept": "application/vnd.github.v3+json"
}

def getFileSha(path):
    url = f"{GITHUB_API_URL}/repos/{GH2DataRepo}/contents/{path}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.json()["sha"]
    return None


def updateFile(content, repo_path, commit_message):
    """ Instead of filepath we're going to use the data
    with open(filepath, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    """
    if type(content) == str: content = content.encode()
    content = base64.b64encode(content).decode()

    sha = getFileSha(repo_path)

    data = {
        "message": commit_message,
        "content": content,
        "branch": "main",
        "committer": {
            "name": GITHUB_USERNAME,
            "email": f"{GITHUB_USERNAME}@users.noreply.github.com"
        }
    }
    if sha:
        data["sha"] = sha

    url = f"{GITHUB_API_URL}/repos/{GH2DataRepo}/contents/{repo_path}"
    r = requests.put(url, headers=HEADERS, data=json.dumps(data))

    if r.status_code in [200, 201]:
        print(f"{repo_path} updated successfully.")
    else:
        print(f"Failed to update {repo_path}: {r.status_code} - {r.text}")

def readFile(repo_path):
    url = f"{GITHUB_API_URL}/repos/{GH2DataRepo}/contents/{repo_path}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code == 200:
        content = r.json()["content"]
        decoded = base64.b64decode(content).decode("utf-8")
        return decoded
    else:
        print(f"Failed to read {repo_path}: {r.status_code} - {r.text}")
        return None

