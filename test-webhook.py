import os
import time
import requests
from src.discordWebhook import NewModAcceptedEvent, NewModVersionAcceptedEvent
from dotenv import load_dotenv

load_dotenv()

webhook_url = os.getenv("DC_WEBHOOK_URL")

# Example for NewModAcceptedEvent
mod_event = NewModAcceptedEvent(
    name="Example Mod",
    version="1.0.0",
    mod_id="example_mod",
    owner={"display_name": "OwnerName", "username": "OwnerUsername"},
    verified_by={"display_name": "VerifierName", "username": "VerifierUsername"},
    base_url="https://geode-sdk.org"
)
mod_event.to_discord_webhook().send(webhook_url)

# Example for NewModVersionAcceptedEvent
version_event = NewModVersionAcceptedEvent(
    name="Example Mod",
    version="1.1.0",
    mod_id="example_mod",
    owner={"display_name": "OwnerName", "username": "OwnerUsername"},
    verified={"display_name": "AdminName", "username": "AdminUsername"},
    base_url="https://geode-sdk.org"
)
version_event.to_discord_webhook().send(webhook_url)
