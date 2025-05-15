#!/usr/bin/env python3
"""
Script to generate content for intoolswetrust.github.io by listing all public repositories
in the intoolswetrust GitHub organization.
"""

import os
import json
import requests
from datetime import datetime
from github import Github
import yaml
from jinja2 import Template

# Configuration
ORG_NAME = "intoolswetrust"
INDEX_PATH = "index.md"
CONFIG_PATH = "_config.yml"
TEMPLATE_PATH = "templates/index.md.j2"
GITHUB_PAGES_URL = f"https://{ORG_NAME}.github.io"

def fetch_repositories():
    """Fetch all public repositories from the organization."""
    token = os.environ.get("GH_TOKEN")
    
    if token:
        g = Github(token)
    else:
        # If no token is provided, use unauthenticated client
        # Note: This has very limited rate limits but works for small organizations
        print("Warning: No GH_TOKEN provided. Using unauthenticated client with limited rate limits.")
        g = Github()
    
    org = g.get_organization(ORG_NAME)
    
    repositories = []
    try:
        for repo in org.get_repos(type="public"):
            # Skip the website repository itself
            if repo.name == f"{ORG_NAME}.github.io":
                continue
            has_pages = repo.has_pages
            topics = repo.get_topics()
            description = repo.description or "No description available"
            if has_pages:
                page_url = f"{GITHUB_PAGES_URL}/{repo.name}"
                site_url = page_url
            else:
                site_url = repo.html_url
            last_updated = repo.updated_at
            repositories.append({
                "name": repo.name,
                "description": description,
                "url": site_url,
                "repo_url": repo.html_url,
                "topics": topics,
                "stars": repo.stargazers_count,
                "has_pages": has_pages,
                "last_updated": last_updated.strftime("%Y-%m-%d"),
                "language": repo.language or "Not specified"
            })
    except Exception as e:
        print(f"Error fetching repositories: {str(e)}")
        raise    
    # Sort repositories by stars (descending)
    repositories.sort(key=lambda x: x["stars"], reverse=True)
    return repositories


def generate_content(repositories):
    """Generate Markdown content from repository data."""
    # Check if template exists
    if os.path.exists(TEMPLATE_PATH):
        with open(TEMPLATE_PATH, "r") as f:
            template_content = f.read()
        template = Template(template_content)
        content = template.render(
            repositories=repositories,
            org_name=ORG_NAME,
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            count=len(repositories)
        )
    else:
        # Generate default template if none exists
        content = f"# {ORG_NAME} Projects\n\n"
        content += f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        content += f"This page lists all public repositories from the [{ORG_NAME}](https://github.com/{ORG_NAME}) GitHub organization.\n\n"
        
        for repo in repositories:
            content += f"## [{repo['name']}]({repo['url']})\n\n"
            content += f"{repo['description']}\n\n"
            if repo["topics"]:
                content += "**Topics:** " + ", ".join(repo["topics"]) + "\n\n"
            content += f"**Language:** {repo['language']} | **Stars:** {repo['stars']} | **Last updated:** {repo['last_updated']}\n\n"
            if repo["has_pages"]:
                content += f"[View Project Site]({GITHUB_PAGES_URL}/{repo['name']}) | "
            content += f"[View on GitHub]({repo['repo_url']})\n\n"
            content += "---\n\n"
            
        content += f"\nGenerated automatically for [{ORG_NAME}](https://github.com/{ORG_NAME}). See the [source code]({ORG_NAME}.github.io) for this site."
    
    return content

def ensure_directory_exists(path):
    """Ensure the directory for the file exists."""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def main():
    """Main function."""
    try:
        repositories = fetch_repositories()
        content = generate_content(repositories)
        
        # Ensure templates directory exists
        ensure_directory_exists(TEMPLATE_PATH)
        
        # Write default template if it doesn't exist
        if not os.path.exists(TEMPLATE_PATH):
            with open(TEMPLATE_PATH, "w") as f:
                f.write("""# {{ org_name }} Projects

*Last updated: {{ generated_date }}*

This page lists all {{ count }} public repositories from the [{{ org_name }}](https://github.com/{{ org_name }}) GitHub organization.

{% for repo in repositories %}
## [{{ repo.name }}]({{ repo.url }})

{{ repo.description }}

{% if repo.topics %}**Topics:** {{ repo.topics|join(", ") }}{% endif %}

**Language:** {{ repo.language }} | **Stars:** {{ repo.stars }} | **Last updated:** {{ repo.last_updated }}

{% if repo.has_pages %}[View Project Site](https://{{ org_name }}.github.io/{{ repo.name }}) | {% endif %}[View on GitHub]({{ repo.repo_url }})

---

{% endfor %}

Generated automatically for [{{ org_name }}](https://github.com/{{ org_name }}). See the [source code](https://github.com/{{ org_name }}/{{ org_name }}.github.io) for this site.
""")
        
        # Write to index.md
        with open(INDEX_PATH, "w") as f:
            f.write(content)
        
        # Create or update _config.yml if it doesn't exist
        if not os.path.exists(CONFIG_PATH):
            config = {
                "title": f"{ORG_NAME} Projects",
                "description": f"A collection of projects by {ORG_NAME}",
                "theme": "jekyll-theme-cayman",
                "show_downloads": False,
                "google_analytics": "",
                "repository": f"{ORG_NAME}/{ORG_NAME}.github.io",
                "github": {
                    "is_project_page": True,
                    "owner_url": f"https://github.com/{ORG_NAME}",
                    "owner_name": ORG_NAME
                }
            }
            with open(CONFIG_PATH, "w") as f:
                yaml.dump(config, f)
        
        print(f"Successfully generated content with {len(repositories)} repositories")
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
