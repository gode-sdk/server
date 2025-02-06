import uuid
import requests
import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from src.database.repository.github_login_attempts import get_one_by_ip, create, remove
from src.types.api import ApiError


class GithubStartAuth:
    def __init__(self, device_code: str, user_code: str, verification_uri: str, expires_in: int, interval: int):
        self.device_code = device_code
        self.user_code = user_code
        self.verification_uri = verification_uri
        self.expires_in = expires_in
        self.interval = interval


class GithubClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    async def start_polling_auth(self, ip: str, session: AsyncSession) -> Optional[dict]:
        login_attempt = await get_one_by_ip(ip, session)
        if login_attempt:
            if login_attempt.is_expired():
                await remove(uuid.UUID(login_attempt.uuid), session)
            else:
                return login_attempt

        response = requests.post(
            "https://github.com/login/device/code",
            auth=(self.client_id, self.client_secret),
            json={"client_id": self.client_id},
            headers={"Accept": "application/json"}
        )

        if not response.ok:
            raise ApiError("InternalError", "Failed to start OAuth device flow with GitHub")

        body = response.json()
        github_start_auth = GithubStartAuth(
            device_code=body["device_code"],
            user_code=body["user_code"],
            verification_uri=body["verification_uri"],
            expires_in=body["expires_in"],
            interval=body["interval"]
        )

        await create(
            ip,
            github_start_auth.device_code,
            github_start_auth.interval,
            github_start_auth.expires_in,
            github_start_auth.verification_uri,
            github_start_auth.user_code,
            session
        )

        return None

    async def poll_github(self, code: str, is_device: bool, redirect_uri: Optional[str]) -> str:
        if is_device:
            payload = {
                "client_id": self.client_id,
                "device_code": code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            }
        else:
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code
            }
            if redirect_uri:
                payload["redirect_uri"] = f"{redirect_uri}/login/github/callback"

        response = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            auth=(self.client_id, self.client_secret),
            json=payload
        )

        if not response.ok:
            raise ApiError("InternalError", "Failed to poll GitHub for developer access token")

        json_response = response.json()
        access_token = json_response.get("access_token")
        if not access_token:
            raise ApiError("BadRequest", "Request not accepted by user")

        return access_token

    async def get_user(self, token: str) -> dict:
        response = requests.get(
            "https://api.github.com/user",
            headers={"Accept": "application/json", "User-Agent": "geode_index"},
            auth=("Bearer", token)
        )

        if not response.ok:
            raise ApiError("InternalError", "Request to https://api.github.com/user failed")

        return response.json()

    async def get_installation(self, token: str) -> dict:
        response = requests.get(
            "https://api.github.com/installation/repositories",
            headers={"Accept": "application/json", "User-Agent": "geode_index"},
            auth=("Bearer", token)
        )

        if not response.ok:
            raise ApiError("InternalError", "Failed to fetch installation repositories")

        body = response.json()
        repositories = body.get("repositories", [])
        if len(repositories) != 1:
            raise ApiError("InternalError", "Expected exactly one repository")

        owner = repositories[0].get("owner")
        if not owner:
            raise ApiError("InternalError", "Failed to extract owner info from repository")

        return owner
