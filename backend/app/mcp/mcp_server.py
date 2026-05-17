import logging
import json
import os
from typing import Dict, Any, List
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google import genai
from google.genai import types
from fastmcp import FastMCP

from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# Create an MCP server
mcp = FastMCP("GitHub Card Generator Server")

# Initialize Gemini Client
genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

@mcp.tool()
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
)
async def scrape_github(username: str) -> Dict[str, Any]:
    """
    Scrape GitHub user profile and repositories.
    """
    logger.info(f"Scraping GitHub data for user: {username}")
    headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get user info
        user_url = f"https://api.github.com/users/{username}"
        user_resp = await client.get(user_url, headers=headers)
        if user_resp.status_code == 404:
            raise ValueError(f"GitHub user '{username}' not found.")
        user_resp.raise_for_status()
        user_data = user_resp.json()

        # Get repositories (up to 100)
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
        repos_resp = await client.get(repos_url, headers=headers)
        repos_resp.raise_for_status()
        repos = repos_resp.json()

    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    
    # Top 5 repositories by stars
    top_repos = sorted(repos, key=lambda x: x.get("stargazers_count", 0), reverse=True)[:5]
    top_repos_data = [
        {
            "name": r.get("name"),
            "stars": r.get("stargazers_count"),
            "language": r.get("language"),
            "description": r.get("description")
        } for r in top_repos
    ]

    # Languages distribution (aggregate from all repos)
    languages = {}
    for repo in repos:
        lang = repo.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
    
    # Sort languages by frequency
    sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
    lang_dist = {k: v for k, v in sorted_langs}

    result = {
        "avatar_url": user_data.get("avatar_url"),
        "name": user_data.get("name"),
        "username": user_data.get("login"),
        "bio": user_data.get("bio"),
        "location": user_data.get("location"),
        "followers": user_data.get("followers"),
        "following": user_data.get("following"),
        "public_repos": user_data.get("public_repos"),
        "total_stars": total_stars,
        "top_repositories": top_repos_data,
        "languages": lang_dist
    }
    
    return result

@mcp.tool()
async def analyze_profile(github_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze GitHub profile using Gemini AI to infer developer personality and skills.
    """
    logger.info(f"Analyzing GitHub profile for user: {github_data.get('username')}")
    
    system_prompt = """
    You are an expert technical recruiter and developer profiler. 
    Analyze the provided GitHub data and classify the developer into EXACTLY ONE of the following archetypes:
    
    1. neon_operator: Cyberpunk, glowing, low-level/security/systems/CLI.
    2. midnight_architect: Elegant dark UI, full-stack/platform engineering.
    3. quantum_researcher: Minimal academic, AI/ML/Data Science.
    4. pixel_craftsman: Creative modern, frontend/design-focused.
    5. open_source_legend: GitHub-inspired, community-centric, OSS maintainers.
    6. cloud_navigator: Cloud infra, observability-inspired, DevOps/Backend.
    7. ai_alchemist: Futuristic AI gradients, GenAI/LLM specialists.
    8. terminal_phantom: Monochrome terminal, hacker-console, cybersecurity.
    9. infra_tactician: Enterprise engineering, architecture-focused, platform/infra.
    10. devrel_icon: Vibrant social-first, presentation-oriented, educators/advocates.

    In your JSON response, provide:
    - developer_archetype (the slug from above, e.g., 'neon_operator')
    - personality_vibe (short description)
    - strongest_skills (top 3)
    - engineering_focus
    - likely_stack
    - fun_insight
    - recommended_card_theme (this MUST match the developer_archetype slug)

    Respond ONLY with a valid JSON object.
    """

    user_prompt = f"GitHub Data: {json.dumps(github_data)}"

    try:
        # Using aio for async support in google-genai
        response = await genai_client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json"
            )
        )
        
        analysis_text = response.text
        # Ensure we have valid JSON
        if not analysis_text:
            raise ValueError("Empty response from Gemini")
            
        analysis = json.loads(analysis_text)
        return analysis
    except Exception as e:
        logger.error(f"Error calling Gemini: {e}")
        # Fallback if AI fails
        return {
            "developer_archetype": "The Code Explorer",
            "personality_vibe": "Curious and active contributor",
            "strongest_skills": list(github_data.get("languages", {}).keys())[:3],
            "engineering_focus": "General Software Development",
            "likely_stack": "Mixed",
            "fun_insight": "A prolific explorer of new technologies.",
            "recommended_card_theme": "minimalist"
        }

@mcp.tool()
async def generate_card_data(github_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge GitHub data and AI analysis into a UI schema for the card.
    """
    logger.info(f"Generating card data for user: {github_data.get('username')}")
    
    card_data = {
        "profile": {
            "name": github_data.get("name") or github_data.get("username"),
            "username": github_data.get("username"),
            "avatar_url": github_data.get("avatar_url"),
            "bio": github_data.get("bio"),
            "location": github_data.get("location"),
        },
        "stats": {
            "followers": github_data.get("followers"),
            "following": github_data.get("following"),
            "public_repos": github_data.get("public_repos"),
            "total_stars": github_data.get("total_stars"),
        },
        "skills": {
            "top_languages": list(github_data.get("languages", {}).keys())[:5],
            "strongest_skills": analysis.get("strongest_skills", []),
            "likely_stack": analysis.get("likely_stack", []),
        },
        "analysis": {
            "archetype": analysis.get("developer_archetype"),
            "vibe": analysis.get("personality_vibe"),
            "focus": analysis.get("engineering_focus"),
            "fun_insight": analysis.get("fun_insight"),
        },
        "theme": analysis.get("recommended_card_theme", "minimalist"),
        "top_repos": github_data.get("top_repositories", [])
    }
    
    return card_data

@mcp.tool()
async def save_card(username: str, card_html: str) -> str:
    """
    Save the generated card HTML to the static directory.
    """
    logger.info(f"Saving card for user: {username}")
    
    # Determine the project root to ensure we save to the correct location
    # mcp_server.py is in backend/app/mcp/
    # We want backend/app/static/cards/
    current_file = Path(__file__).resolve()
    backend_root = current_file.parent.parent.parent
    
    cards_dir = backend_root / "app" / "static" / "cards"
    
    # Ensure directory exists
    cards_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = cards_dir / f"{username}.html"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(card_html)
    
    return f"/static/cards/{username}.html"

if __name__ == "__main__":
    mcp.run()
