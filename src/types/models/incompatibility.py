from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
import ipaddress

import sqlalchemy
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select

Base = declarative_base()

class IncompatibilityImportance(str, Enum):
    breaking = "breaking"
    conflicting = "conflicting"
    superseded = "superseded"

class FetchedIncompatibility(BaseModel):
    mod_id: int
    version: str
    incompatibility_id: str
    compare: str
    importance: IncompatibilityImportance

    class Config:
        orm_mode = True

    def to_response(self) -> 'ResponseIncompatibility':
        version = self.version if self.version != "*" else "*"
        return ResponseIncompatibility(
            mod_id=self.incompatibility_id,
            version=f"{self.compare}{self.version}" if self.version != "*" else version,
            importance=self.importance
        )


class Incompatibility(Base):
    __tablename__ = 'incompatibilities'
    mod_id = Column(Integer, ForeignKey('mod_versions.id'), primary_key=True)
    incompatibility_id = Column(String, primary_key=True)
    compare = Column(String)
    importance = Column(SQLEnum(IncompatibilityImportance))

    def __repr__(self):
        return f"<Incompatibility(mod_id={self.mod_id}, incompatibility_id={self.incompatibility_id})>"

    @classmethod
    async def create_for_mod_version(cls, session, id: int, incompats: List['IncompatibilityCreate']):
        query = []
        for i in incompats:
            query.append(
                cls(mod_id=id, 
                    incompatibility_id=i.incompatibility_id, 
                    compare=i.compare, 
                    importance=i.importance)
            )
        session.add_all(query)
        await session.commit()

    @classmethod
    async def clear_for_mod_version(cls, session, id: int):
        await session.execute(sqlalchemy.delete(cls).where(cls.mod_id == id))
        await session.commit()

    @classmethod
    async def get_for_mod_version(cls, session, id: int) -> List[FetchedIncompatibility]:
        result = await session.execute(select(cls).filter(cls.mod_id == id))
        return result.scalars().all()

    @classmethod
    async def get_for_mod_versions(
        cls, 
        session, 
        ids: List[int], 
        platform: Optional[str] = None, 
        gd: Optional[str] = None, 
        geode: Optional[str] = None
    ) -> Dict[int, List[FetchedIncompatibility]]:
        result = await session.execute(
            select(cls).filter(cls.mod_id.in_(ids))
        )
        incompatibilities = result.scalars().all()

        grouped = {}
        for incompat in incompatibilities:
            if incompat.mod_id not in grouped:
                grouped[incompat.mod_id] = []
            grouped[incompat.mod_id].append(incompat)

        return grouped

    @classmethod
    async def get_supersedes_for(cls, session, ids: List[str], platform: str, gd: str, geode: str) -> Dict[str, 'Replacement']:
        query = """
        SELECT
            replaced.incompatibility_id AS replaced, 
            replacement.mod_id AS replacement, 
            replacement.version AS replacement_version,
            replacement.id AS replacement_id
        FROM incompatibilities replaced
        INNER JOIN mod_versions replacement ON replacement.id = replaced.mod_id
        WHERE replaced.importance = 'superseded'
        AND replaced.incompatibility_id = ANY(:ids)
        AND replacement.gd = :gd
        AND replacement.platform = :platform
        """
        result = await session.execute(query, {'ids': ids, 'gd': gd, 'platform': platform})
        rows = result.fetchall()

        supersedes = {}
        for row in rows:
            supersedes[row.replaced] = Replacement(
                id=row.replacement,
                version=row.replacement_version,
                replacement_id=row.replacement_id,
                download_link="",
                dependencies=[],
                incompatibilities=[]
            )
        return supersedes


class IncompatibilityCreate(BaseModel):
    incompatibility_id: str
    version: str
    compare: str
    importance: IncompatibilityImportance


class ResponseIncompatibility(BaseModel):
    mod_id: str
    version: str
    importance: IncompatibilityImportance


class Replacement(BaseModel):
    id: str
    version: str
    replacement_id: int
    download_link: str
    dependencies: List[str]
    incompatibilities: List[str]