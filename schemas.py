"""
Database Schemas for the Networking App

Each Pydantic model below represents a MongoDB collection. The collection
name is the lowercase of the class name.

Examples:
- Profile -> "profile"
- Project -> "project"
- Endorsement -> "endorsement"
"""

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, EmailStr


class Profile(BaseModel):
    """
    Profiles collection schema
    Collection: "profile"
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    headline: Optional[str] = Field(None, description="Short role/summary")
    bio: Optional[str] = Field(None, description="About you")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    interests: List[str] = Field(default_factory=list, description="Interests/topics")
    timezone: Optional[str] = Field(None, description="IANA tz, e.g., 'America/Los_Angeles'")
    availability: Optional[str] = Field(None, description="Availability notes / windows")
    goals: Optional[str] = Field(None, description="Outcomes you're seeking now")
    links: List[HttpUrl] = Field(default_factory=list, description="Portfolio or socials")
    verified: bool = Field(default=False, description="Verification flag")
    reputation_score: float = Field(default=0.0, ge=0.0, description="Reputation score")


class Project(BaseModel):
    """
    Projects collection schema
    Collection: "project"
    """
    owner_id: str = Field(..., description="Profile _id string of owner")
    title: str = Field(..., description="Project title")
    brief: str = Field(..., description="Project description / brief")
    tags: List[str] = Field(default_factory=list, description="Tags / skills / topics")
    roles_needed: List[str] = Field(default_factory=list, description="Roles needed")
    status: str = Field(default="open", description="open | in_progress | completed")
    visibility: str = Field(default="public", description="public | community | private")


class Endorsement(BaseModel):
    """
    Endorsements collection schema
    Collection: "endorsement"
    """
    from_user: str = Field(..., description="Endorser profile _id string")
    to_user: str = Field(..., description="Endorsee profile _id string")
    skill: str = Field(..., description="Skill endorsed")
    comment: Optional[str] = Field(None, description="Optional note")
    evidence_url: Optional[HttpUrl] = Field(None, description="Link to evidence/artifact")
    weight: float = Field(default=1.0, ge=0.0, description="Trust weighting")


# Optional: simple message schema for future chat
class Conversation(BaseModel):
    participant_ids: List[str] = Field(..., description="Profile IDs participating")
    type: str = Field(default="1:1", description="1:1 | group | project")


class Message(BaseModel):
    conversation_id: str = Field(...)
    from_user: str = Field(...)
    text: str = Field(...)
