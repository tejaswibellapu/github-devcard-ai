from google import genai
from app.config import settings
from app.models.schemas import GitHubUserData

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def analyze_developer(self, user_data: GitHubUserData) -> str:
        prompt = f"""
        Analyze this GitHub profile and provide a 2-sentence quirky and impressive developer persona.
        Username: {user_data.username}
        Bio: {user_data.bio}
        Languages: {', '.join(user_data.languages)}
        Stars: {user_data.total_stars}
        Repos: {user_data.public_repos}
        """
        # Using synchronous call as genai client might not be fully async-first in some versions, 
        # but wrapping it for future-proofing or using executor if needed.
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text

gemini_service = GeminiService()
