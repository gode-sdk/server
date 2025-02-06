import requests

class DiscordMessage:
    def __init__(self):
        self.embeds = []

    def embed(self, title, description=None, image_url=None):
        embed = {"title": title}
        if description:
            embed["description"] = description
        if image_url:
            embed["image"] = {"url": image_url}
        self.embeds.append(embed)
        return self

    def send(self, webhook_url):
        payload = {"embeds": self.embeds}
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()

class NewModAcceptedEvent:
    def __init__(self, name, version, mod_id, owner, verified_by, base_url):
        self.name = name
        self.version = version
        self.id = mod_id
        self.owner = owner
        self.verified_by = verified_by
        self.base_url = base_url

    def to_discord_webhook(self):
        return DiscordMessage().embed(
            f"\u2705 New mod: {self.name} {self.version}",
            f"https://geode-sdk.org/mods/{self.id}\n\nOwned by [{self.owner['display_name']}](https://github.com/{self.owner['username']})\nAccepted by [{self.verified_by['display_name']}](https://github.com/{self.verified_by['username']})",
            f"{self.base_url}/v1/mods/{self.id}/logo"
        )

class NewModVersionAcceptedEvent:
    def __init__(self, name, version, mod_id, owner, verified, base_url):
        self.name = name
        self.version = version
        self.id = mod_id
        self.owner = owner
        self.verified = verified
        self.base_url = base_url

    def to_discord_webhook(self):
        accepted_msg = (
            "Developer is verified" if self.verified == "VerifiedDev" else
            f"Accepted by [{self.verified['display_name']}](https://github.com/{self.verified['username']})"
        )
        
        return DiscordMessage().embed(
            f"\u2B06\uFE0F Updated {self.name} to {self.version}",
            f"https://geode-sdk.org/mods/{self.id}\n\nOwned by [{self.owner['display_name']}](https://github.com/{self.owner['username']})\n{accepted_msg}",
            f"{self.base_url}/v1/mods/{self.id}/logo"
        )
