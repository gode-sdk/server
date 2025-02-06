import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Load GitHub OAuth credentials from .env file or environment variables
GH_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GH_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

# Step 1: Request device and user verification codes
device_code_url = "https://github.com/login/device/code"
access_token_url = "https://github.com/login/oauth/access_token"
user_url = "https://api.github.com/user"

headers = {"Accept": "application/json"}
data = {"client_id": GH_CLIENT_ID, "scope": "repo user"}

response = requests.post(device_code_url, headers=headers, data=data)
device_data = response.json()

if "error" in device_data:
    print("Error requesting device code:", device_data["error"])
    exit(1)

device_code = device_data["device_code"]
user_code = device_data["user_code"]
verification_uri = device_data["verification_uri"]
interval = device_data["interval"]

print(f"Go to {verification_uri} and enter this code: {user_code}")

# Step 2: Poll for user authentication
print("Waiting for user authorization...")

while True:
    time.sleep(interval)
    
    token_data = {
        "client_id": GH_CLIENT_ID,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    }

    token_response = requests.post(access_token_url, headers=headers, data=token_data)
    token_result = token_response.json()

    if "error" in token_result:
        if token_result["error"] == "authorization_pending":
            continue  # Keep polling
        elif token_result["error"] == "slow_down":
            interval += 5  # Increase polling interval
        else:
            print("Error:", token_result["error"])
            exit(1)
    else:
        access_token = token_result["access_token"]
        break

# Step 3: Use the access token to access the API
auth_headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
user_response = requests.get(user_url, headers=auth_headers)
user_data = user_response.json()

print(f"Authenticated as: {user_data['login']}")
