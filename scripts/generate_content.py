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
    with open(TEMPLATE_PATH, "r") as f:
        template_content = f.read()
    template = Template(template_content)
    content = template.render(
        repositories=repositories,
        org_name=ORG_NAME,
        count=len(repositories)
    )
    return content

def main():
    """Main function."""
    try:
        repositories = fetch_repositories()
        content = generate_content(repositories)
        # Write to index.md
        with open(INDEX_PATH, "w") as f:
            f.write(content)
        print(f"Successfully generated content with {len(repositories)} repositories")
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
