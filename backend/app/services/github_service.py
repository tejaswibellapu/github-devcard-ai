import httpx
from typing import Dict, Any, List
from app.config import settings
from app.models.schemas import GitHubUserData

class GitHubService:
    def __init__(self):
        self.headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}
        self.base_url = "https://api.github.com"

    async def get_user_data(self, username: str) -> GitHubUserData:
        async with httpx.AsyncClient() as client:
            # Get basic user info
            user_resp = await client.get(f"{self.base_url}/users/{username}", headers=self.headers)
            user_resp.raise_for_status()
            user_data = user_resp.json()

            # Get repos to calculate stars and languages
            repos_resp = await client.get(f"{self.base_url}/users/{username}/repos?per_page=100", headers=self.headers)
            repos_resp.raise_for_status()
            repos = repos_resp.json()

            total_stars = sum(repo["stargazers_count"] for repo in repos)
            
            # Simple language extraction
            languages = list(set(repo["language"] for repo in repos if repo["language"]))

            return GitHubUserData(
                username=username,
                name=user_data.get("name"),
                bio=user_data.get("bio"),
                avatar_url=user_data["avatar_url"],
                followers=user_data["followers"],
                following=user_data["following"],
                public_repos=user_data["public_repos"],
                total_stars=total_stars,
                languages=languages[:5] # Top 5
            )

github_service = GitHubService()
