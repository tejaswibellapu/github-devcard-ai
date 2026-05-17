import logging
import httpx
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"

class GitHubCardAgent:

    async def fetch_github_profile(self, username: str):

        headers = {
            "Authorization": f"Bearer {settings.GITHUB_TOKEN}"
        }

        async with httpx.AsyncClient() as client:

            user_res = await client.get(
                f"{GITHUB_API}/users/{username}",
                headers=headers
            )

            repos_res = await client.get(
                f"{GITHUB_API}/users/{username}/repos?sort=updated&per_page=100",
                headers=headers
            )

        if user_res.status_code != 200:
            raise Exception("GitHub user not found")

        user = user_res.json()
        repos = repos_res.json()

        total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)

        top_repos = sorted(
            repos,
            key=lambda x: x.get("stargazers_count", 0),
            reverse=True
        )[:4]

        languages = {}

        for repo in repos:
            lang = repo.get("language")

            if lang:
                languages[lang] = languages.get(lang, 0) + 1

        top_languages = sorted(
            languages,
            key=languages.get,
            reverse=True
        )[:4]

        return {
            "user": user,
            "repos": repos,
            "top_repos": top_repos,
            "top_languages": top_languages,
            "total_stars": total_stars
        }

    async def generate_for_user(self, username: str) -> Dict[str, Any]:

        logger.info(f"Generating REAL card for {username}")

        data = await self.fetch_github_profile(username)

        user = data["user"]

        return {
            "success": True,
            "image_url": "",

            "card_data": {

                "theme": "midnight_architect",

                "profile": {
                    "username": user.get("login"),
                    "name": user.get("name") or user.get("login"),
                    "bio": user.get("bio") or "GitHub Developer",
                    "location": user.get("location") or "Unknown",
                    "avatar_url": user.get("avatar_url")
                },

                "stats": {
                    "total_stars": data["total_stars"],
                    "public_repos": user.get("public_repos", 0),
                    "followers": user.get("followers", 0),
                    "following": user.get("following", 0)
                },

                "skills": {
                    "top_languages": data["top_languages"],

                    "strongest_skills": [
                        "Software Engineering",
                        "Open Source",
                        "Backend Development"
                    ]
                },

                "analysis": {
                    "archetype": "Open Source Architect",
                    "vibe": "Passionate builder with strong engineering focus.",
                    "focus": "Full Stack & Open Source",
                    "fun_insight": f"Owns {user.get('public_repos', 0)} public repositories."
                },

                "top_repos": [
                    {
                        "name": repo.get("name"),
                        "description": repo.get("description"),
                        "stars": repo.get("stargazers_count"),
                        "language": repo.get("language")
                    }

                    for repo in data["top_repos"]
                ]
            }
        }

github_card_agent = GitHubCardAgent()