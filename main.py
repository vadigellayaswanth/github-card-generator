from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import urllib.request
import json

app = FastAPI(title="GitHub Dev Card Generator API")

# Enable CORS for communication with your index.html file
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    username: str

def fetch_github_data(username: str):
    """Safely fetches user profile and repository information using Python's standard library"""
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # 1. Fetch core profile statistics
    user_url = f"https://api.github.com/users/{username}"
    try:
        user_req = urllib.request.Request(user_url, headers=headers)
        with urllib.request.urlopen(user_req) as response:
            user_data = json.loads(response.read().decode())
    except Exception as e:
        raise Exception(f"GitHub User not found or API limit reached: {str(e)}")

    # 2. Fetch repository data to calculate stars, languages, and grab top projects
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    try:
        repos_req = urllib.request.Request(repos_url, headers=headers)
        with urllib.request.urlopen(repos_req) as response:
            repos_data = json.loads(response.read().decode())
    except Exception:
        repos_data = []

    # Calculate metrics dynamically
    public_repos = user_data.get("public_repos", 0)
    followers = user_data.get("followers", 0)
    avatar_url = user_data.get("avatar_url", "")
    bio = user_data.get("bio") or "A passionate developer building clean software architectures and tracking analytics."
    
    total_stars = 0
    languages_map = {}
    projects_list = []

    for r in repos_data:
        # Sum up total stargazers count
        total_stars += r.get("stargazers_count", 0)
        
        # Track main language frequency
        lang = r.get("language")
        if lang:
            languages_map[lang] = languages_map.get(lang, 0) + 1
            
        # Collect project metadata
        projects_list.append({
            "name": r.get("name", "Unnamed Repo"),
            "language": lang or "Mixed",
            "stars": r.get("stargazers_count", 0)
        })

    # Sort projects by star count (highest first) and take top 3
    projects_list = sorted(projects_list, key=lambda x: x["stars"], reverse=True)[:3]
    
    # Sort languages used by frequency and extract top 3 names
    sorted_langs = sorted(languages_map.items(), key=lambda x: x[1], reverse=True)
    top_languages = [lang[0] for lang in sorted_langs[:3]]
    if not top_languages:
        top_languages = ["Markdown", "Git"]

    return {
        "username": username,
        "avatar_url": avatar_url,
        "bio": bio,
        "repos": public_repos,
        "followers": followers,
        "stars": total_stars,
        "languages": top_languages,
        "projects": projects_list
    }

@app.get("/")
async def root():
    return {"message": "GitHub Dev Card Generator API is running"}

@app.post("/generate")
async def generate_card(request: GenerateRequest):
    try:
        # Pull live account statistics from GitHub
        git = fetch_github_data(request.username)
        
        # Format the tech stack badges dynamically
        lang_badges = "".join([
            f'<span style="background-color: #111b27; color: #58a6ff; border: 1px solid #41536b; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; margin-right: 6px;">{lang}</span>'
            for lang in git["languages"]
        ])

        # Format the top projects feed rows dynamically
        project_rows = ""
        for p in git["projects"]:
            project_rows += f"""
            <div style="margin-bottom: 8px; font-size: 13px; display: flex; justify-content: space-between;">
                <div>
                    <span style="color: #58a6ff; font-weight: 500;">{p['name']}</span> 
                    <span style="color: #8b949e;">· {p['language']}</span>
                </div>
                <span style="color: #e3b341;">★ {p['stars']}</span>
            </div>
            """
        if not project_rows:
            project_rows = '<p style="color: #8b949e; font-size: 13px; margin: 0;">No public repositories found.</p>'

        # Build dynamic HTML template injection using the live dictionary values
        dynamic_card = f"""
        <div style="background-color: #0d1117; color: #c9d1d9; padding: 24px; border-radius: 16px; border: 1px solid #30363d; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; max-width: 420px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); margin: 20px auto; text-align: left;">
            
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <img src="{git['avatar_url']}" alt="Avatar" style="width: 56px; height: 56px; border-radius: 50%; margin-right: 16px; border: 2px solid #58a6ff; background-color: #1f242c;" onerror="this.style.display='none'; document.getElementById('alt-avatar').style.display='flex';">
                <div id="alt-avatar" style="display: none; background: #1f242c; width: 56px; height: 56px; border-radius: 50%; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; color: #58a6ff; margin-right: 16px; border: 2px solid #58a6ff;">
                    {git['username'][0].upper()}
                </div>
                <div>
                    <h3 style="color: #f0f6fc; margin: 0; font-size: 18px; font-weight: 600;">{git['username']}</h3>
                    <p style="color: #8b949e; margin: 2px 0 0 0; font-size: 13px;">@{git['username']}</p>
                </div>
            </div>

            <p style="color: #8b949e; font-style: italic; font-size: 13px; line-height: 1.5; margin: 16px 0; border-left: 3px solid #30363d; padding-left: 12px;">
                "{git['bio']}"
            </p>

            <div style="display: flex; margin-bottom: 20px; flex-wrap: wrap; gap: 4px;">
                {lang_badges}
            </div>

            <div style="display: flex; justify-content: space-around; background-color: #161b22; padding: 12px; border-radius: 8px; border: 1px solid #21262d; text-align: center; margin-bottom: 20px;">
                <div>
                    <span style="color: #f0f6fc; font-size: 15px; font-weight: bold; display: block;">{git['repos']}</span>
                    <span style="color: #8b949e; font-size: 11px;">Repos</span>
                </div>
                <div style="border-left: 1px solid #30363d; height: 32px;"></div>
                <div>
                    <span style="color: #f0f6fc; font-size: 15px; font-weight: bold; display: block;">{git['stars']}</span>
                    <span style="color: #8b949e; font-size: 11px;">Total Stars</span>
                </div>
                <div style="border-left: 1px solid #30363d; height: 32px;"></div>
                <div>
                    <span style="color: #f0f6fc; font-size: 15px; font-weight: bold; display: block;">{git['followers']}</span>
                    <span style="color: #8b949e; font-size: 11px;">Followers</span>
                </div>
            </div>

            <div style="margin-top: 15px;">
                <h4 style="color: #f0f6fc; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px; border-bottom: 1px solid #21262d; padding-bottom: 5px;">Top Projects</h4>
                {project_rows}
            </div>
            
        </div>
        """
        return {"result": dynamic_card}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))