from enum import Enum
from typing import List, Dict, Optional
import logging
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
import asyncpg
import sqlalchemy as sa

Base = declarative_base()

class DependencyImportance(str, Enum):
    suggested = "suggested"
    recommended = "recommended"
    required = "required"

class ModVersionCompare(str, Enum):
    exact = "="
    more = ">"
    more_eq = ">="
    less = "<"
    less_eq = "<="

    def __str__(self):
        return self.value

class Dependency(Base):
    __tablename__ = "dependencies"

    dependent_id = Column(Integer, primary_key=True)
    dependency_id = Column(String, primary_key=True)
    compare = Column(SQLEnum(ModVersionCompare), nullable=False)
    importance = Column(SQLEnum(DependencyImportance), default=DependencyImportance.required)

class DependencyCreate(BaseModel):
    dependency_id: str
    version: str
    compare: ModVersionCompare
    importance: DependencyImportance

class ResponseDependency(BaseModel):
    mod_id: str
    version: str
    importance: DependencyImportance

class FetchedDependency:
    def __init__(self, mod_version_id: int, version: str, dependency_id: str, compare: ModVersionCompare, importance: DependencyImportance):
        self.mod_version_id = mod_version_id
        self.version = version
        self.dependency_id = dependency_id
        self.compare = compare
        self.importance = importance

    def to_response(self) -> ResponseDependency:
        version_str = self.version if self.version != "*" else "*"
        return ResponseDependency(mod_id=self.dependency_id, version=f"{self.compare}{version_str}", importance=self.importance)

async def create_for_mod_version(id: int, deps: List[DependencyCreate], pool: asyncpg.Connection) -> None:
    try:
        async with pool.transaction():
            values = [
                (id, dep.dependency_id, dep.version, dep.compare.value, dep.importance.value)
                for dep in deps
            ]
            query = """
            INSERT INTO dependencies (dependent_id, dependency_id, version, compare, importance)
            VALUES ($1, $2, $3, $4, $5)
            """
            await pool.executemany(query, values)
    except Exception as e:
        logging.error(f"Error inserting dependencies: {e}")
        raise ApiError("DbError")

async def clear_for_mod_version(id: int, pool: asyncpg.Connection) -> None:
    try:
        await pool.execute("DELETE FROM dependencies WHERE dependent_id = $1", id)
    except Exception as e:
        logging.error(f"Failed to remove dependencies for mod version {id}: {e}")
        raise ApiError("DbError")

async def get_for_mod_versions(
    ids: List[int], platform: Optional[str], gd: Optional[str], geode: Optional[str], pool: asyncpg.Connection
) -> Dict[int, List[FetchedDependency]]:
    try:
        query = """
        WITH RECURSIVE dep_tree AS (
            -- Your recursive SQL query logic here
        )
        SELECT * FROM dep_tree
        """
        result = await pool.fetch(query, *ids, gd, platform, geode)
        
        dependencies = {}
        for row in result:
            dependency = FetchedDependency(
                mod_version_id=row['dependency_vid'],
                version=row['dependency_version'],
                dependency_id=row['dependency'],
                compare=ModVersionCompare(row['compare']),
                importance=DependencyImportance(row['importance'])
            )
            dependencies.setdefault(row['start_node'], []).append(dependency)
        return dependencies
    except Exception as e:
        logging.error(f"Error fetching dependencies: {e}")
        raise ApiError("DbError")

class ApiError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

