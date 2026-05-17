import os
from jinja2 import Template
from app.config import settings
from app.models.schemas import GitHubUserData
import uuid

class CardService:
    def __init__(self):
        self.template_str = """
        <svg width="400" height="200" viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" rx="15" fill="url(#grad)" />
            <defs>
                <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#1a1a2e;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#16213e;stop-opacity:1" />
                </linearGradient>
            </defs>
            <circle cx="50" cy="50" r="35" fill="white" />
            <clipPath id="avatarClip">
                <circle cx="50" cy="50" r="35" />
            </clipPath>
            <image href="{{ avatar_url }}" x="15" y="15" width="70" height="70" clip-path="url(#avatarClip)" />
            
            <text x="100" y="45" font-family="Arial" font-size="20" fill="white" font-weight="bold">{{ name or username }}</text>
            <text x="100" y="65" font-family="Arial" font-size="14" fill="#4ecca3">@{{ username }}</text>
            
            <text x="25" y="110" font-family="Arial" font-size="12" fill="#adb5bd">Stars: {{ total_stars }}</text>
            <text x="100" y="110" font-family="Arial" font-size="12" fill="#adb5bd">Repos: {{ public_repos }}</text>
            <text x="180" y="110" font-family="Arial" font-size="12" fill="#adb5bd">Followers: {{ followers }}</text>
            
            <text x="25" y="140" font-family="Arial" font-size="12" fill="white" font-style="italic">"{{ analysis[:60] }}..."</text>
            
            <g transform="translate(25, 160)">
                {% for lang in languages %}
                <rect x="{{ loop.index0 * 60 }}" width="50" height="20" rx="5" fill="#0f3460" />
                <text x="{{ loop.index0 * 60 + 25 }}" y="14" font-family="Arial" font-size="10" fill="#e94560" text-anchor="middle">{{ lang }}</text>
                {% endfor %}
            </g>
        </svg>
        """
        self.html_template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>GitHub Card - {{ profile.username }}</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-color: #f0f2f5; }
                .card { background: white; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 450px; overflow: hidden; }
                .header { background: #24292e; color: white; padding: 20px; display: flex; align-items: center; }
                .avatar { width: 80px; height: 80px; border-radius: 50%; border: 3px solid white; margin-right: 20px; }
                .user-info h2 { margin: 0; font-size: 24px; }
                .user-info p { margin: 5px 0 0; color: #adb5bd; }
                .content { padding: 20px; }
                .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; text-align: center; }
                .stat-item { background: #f6f8fa; padding: 10px; border-radius: 8px; }
                .stat-value { font-weight: bold; display: block; }
                .stat-label { font-size: 12px; color: #586069; }
                .analysis { background: #fffdef; border-left: 4px solid #f1e05a; padding: 15px; margin-bottom: 20px; border-radius: 4px; }
                .analysis h3 { margin: 0 0 10px; font-size: 16px; color: #85702a; }
                .skills { display: flex; flex-wrap: wrap; gap: 8px; }
                .skill-tag { background: #0366d6; color: white; padding: 4px 10px; border-radius: 12px; font-size: 12px; }
                .theme-{{ theme }} { border-top: 5px solid #0366d6; }
            </style>
        </head>
        <body>
            <div class="card theme-{{ theme }}">
                <div class="header">
                    <img src="{{ profile.avatar_url }}" class="avatar" alt="{{ profile.username }}">
                    <div class="user-info">
                        <h2>{{ profile.name or profile.username }}</h2>
                        <p>@{{ profile.username }}</p>
                    </div>
                </div>
                <div class="content">
                    <div class="stats">
                        <div class="stat-item"><span class="stat-value">{{ stats.total_stars }}</span><span class="stat-label">Stars</span></div>
                        <div class="stat-item"><span class="stat-value">{{ stats.public_repos }}</span><span class="stat-label">Repos</span></div>
                        <div class="stat-item"><span class="stat-value">{{ stats.followers }}</span><span class="stat-label">Followers</span></div>
                        <div class="stat-item"><span class="stat-value">{{ stats.following }}</span><span class="stat-label">Following</span></div>
                    </div>
                    <div class="analysis">
                        <h3>{{ analysis.archetype }}</h3>
                        <p>{{ analysis.vibe }}</p>
                        <p><strong>Insight:</strong> {{ analysis.fun_insight }}</p>
                    </div>
                    <div class="skills">
                        {% for skill in skills.top_languages %}
                        <span class="skill-tag">{{ skill }}</span>
                        {% endfor %}
                        {% for skill in skills.strongest_skills %}
                        <span class="skill-tag" style="background-color: #28a745;">{{ skill }}</span>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    async def generate_svg(self, user_data: GitHubUserData, analysis: str) -> str:
        template = Template(self.template_str)
        svg_content = template.render(
            username=user_data.username,
            name=user_data.name,
            avatar_url=user_data.avatar_url,
            total_stars=user_data.total_stars,
            public_repos=user_data.public_repos,
            followers=user_data.followers,
            languages=user_data.languages,
            analysis=analysis
        )
        
        filename = f"{user_data.username}_{uuid.uuid4().hex[:8]}.svg"
        file_path = os.path.join(settings.CARDS_DIR, filename)
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(svg_content)
            
        return filename

    async def render_card(self, card_data: dict) -> str:
        template = Template(self.html_template_str)
        return template.render(**card_data)

card_service = CardService()
