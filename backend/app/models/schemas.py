from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

class CardGenerationRequest(BaseModel):
    username: str = Field(..., description="The GitHub username to generate a card for")

class GithubStats(BaseModel):
    followers: int
    following: int
    public_repos: int
    total_stars: int

class ProfileInfo(BaseModel):
    name: Optional[str]
    username: str
    avatar_url: str
    bio: Optional[str]
    location: Optional[str]

class DevAnalysis(BaseModel):
    archetype: str
    vibe: str
    focus: str
    fun_insight: str

class CardData(BaseModel):
    profile: ProfileInfo
    stats: GithubStats
    skills: Dict[str, List[str]]
    analysis: DevAnalysis
    theme: str
    top_repos: List[Dict[str, Any]]

class CardGenerationResponse(BaseModel):
    success: bool
    image_url: Optional[str] = None
    message: str
    card_data: Optional[CardData] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
