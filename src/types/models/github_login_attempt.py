from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import ipaddress

class StoredLoginAttempt(BaseModel):
    uuid: str
    ip: ipaddress.IPv4Network
    device_code: str
    uri: str
    user_code: str
    interval: int
    expires_in: int
    created_at: datetime
    last_poll: datetime

    class Config:
        orm_mode = True

    def is_expired(self) -> bool:
        """Check if the login attempt is expired"""
        now = datetime.utcnow()
        expire_time = self.created_at + timedelta(seconds=self.expires_in)
        return now > expire_time

    def interval_passed(self) -> bool:
        """Check if the interval has passed since the last poll"""
        now = datetime.utcnow()
        diff = (now - self.last_poll).total_seconds()
        return diff > self.interval