import os
import requests
import base64
import time
import re
import json
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from bs4 import BeautifulSoup

load_dotenv()

# Setup logging
os.makedirs("logs", exist_ok=True)
log_filename = f"logs/ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)  # Keep console output too
    ]
)
logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

SEARCH_QUERIES = [
    # General High-Quality Projects
    "stars:10000..50000 forks:>100 archived:false NOT tutorial NOT awesome NOT roadmap",
    "stars:1000..10000 forks:>50 archived:false pushed:>2023-01-01 NOT tutorial NOT awesome",
    "stars:500..1000 forks:>20 archived:false pushed:>2023-06-01 NOT tutorial NOT learn",
    "stars:100..500 forks:>10 archived:false pushed:>2024-01-01 NOT tutorial NOT example",
    "stars:>50 pushed:>2024-09-01 forks:>5 archived:false NOT tutorial NOT course",
    
    # Python
    "language:python stars:200..5000 forks:>20 archived:false NOT tutorial NOT awesome",
    "language:python topic:machine-learning stars:>100 forks:>10 NOT course NOT tutorial",
    "language:python topic:web-framework stars:>50 archived:false NOT boilerplate",
    "language:python stars:100..1000 forks:>10 archived:false NOT tutorial NOT learn",
    
    # JavaScript
    "language:javascript stars:200..5000 forks:>20 archived:false NOT tutorial NOT starter",
    "language:javascript topic:react stars:>100 forks:>10 NOT tutorial NOT example",
    "language:javascript topic:nodejs stars:>100 forks:>10 archived:false NOT tutorial",
    "language:javascript stars:100..1000 forks:>10 archived:false NOT boilerplate",
    
    # TypeScript
    "language:typescript stars:200..5000 forks:>20 archived:false NOT template NOT boilerplate",
    "language:typescript topic:react stars:>100 forks:>10 NOT tutorial NOT starter",
    "language:typescript stars:100..1000 forks:>10 archived:false NOT example",
    
    # Go
    "language:go stars:200..5000 forks:>15 archived:false NOT tutorial NOT awesome",
    "language:go topic:cli stars:>100 archived:false NOT learn",
    "language:go topic:microservices stars:>50 forks:>5 NOT tutorial",
    "language:go stars:100..1000 forks:>10 archived:false NOT example",
    
    # Rust
    "language:rust stars:100..5000 forks:>10 archived:false NOT tutorial NOT awesome",
    "language:rust topic:cli stars:>50 archived:false NOT example",
    "language:rust topic:systems-programming stars:>50 forks:>5",
    "language:rust stars:50..500 forks:>5 archived:false NOT tutorial",
    
    # Java
    "language:java stars:200..5000 forks:>20 archived:false NOT tutorial NOT awesome",
    "language:java topic:spring-boot stars:>50 forks:>10 NOT demo NOT sample",
    "language:java stars:100..1000 forks:>10 archived:false NOT tutorial",
    
    # C
    "language:c stars:200..5000 forks:>15 archived:false NOT tutorial NOT learn",
    "language:c topic:embedded stars:>50 archived:false NOT tutorial",
    "language:c stars:100..1000 forks:>10 archived:false NOT example",
    
    # C++
    "language:cpp stars:200..5000 forks:>15 archived:false NOT tutorial NOT example",
    "language:cpp topic:game-engine stars:>100 forks:>10 NOT tutorial",
    "language:cpp stars:100..1000 forks:>10 archived:false NOT learn",
    
    # Ruby
    "language:ruby stars:100..5000 forks:>10 archived:false NOT tutorial NOT awesome",
    "language:ruby topic:rails stars:>50 forks:>5 NOT tutorial",
    
    # PHP
    "language:php stars:100..5000 forks:>10 archived:false NOT tutorial NOT boilerplate",
    "language:php topic:laravel stars:>50 forks:>5 NOT tutorial",
    
    # Swift
    "language:swift stars:100..5000 forks:>10 archived:false NOT tutorial NOT example",
    "language:swift topic:ios stars:>50 forks:>5 NOT tutorial",
    
    # Kotlin
    "language:kotlin stars:100..5000 forks:>10 archived:false NOT sample NOT template",
    "language:kotlin topic:android stars:>50 forks:>5 NOT tutorial",
    
    # Scala
    "language:scala stars:50..5000 forks:>5 archived:false NOT tutorial",
    
    # Elixir
    "language:elixir stars:50..2000 forks:>5 archived:false NOT example",
    
    # C#
    "language:csharp stars:100..5000 forks:>10 archived:false NOT tutorial NOT example",
    "language:csharp topic:dotnet stars:>50 forks:>5 NOT tutorial",
    
    # Web Frameworks & Libraries
    "topic:web-framework stars:>100 forks:>10 archived:false NOT tutorial NOT boilerplate",
    "topic:frontend stars:>100 forks:>10 archived:false NOT template NOT starter",
    "topic:backend stars:>100 forks:>10 archived:false NOT example NOT demo",
    "topic:react stars:>200 forks:>20 archived:false NOT tutorial NOT template",
    "topic:vue stars:>100 forks:>10 archived:false NOT tutorial NOT starter",
    "topic:angular stars:>100 forks:>10 archived:false NOT tutorial NOT example",
    
    # DevOps & Infrastructure
    "topic:devops stars:>100 forks:>10 archived:false NOT tutorial NOT learn",
    "topic:kubernetes stars:>100 forks:>10 archived:false NOT example NOT demo",
    "topic:docker stars:>100 forks:>10 archived:false NOT template NOT boilerplate",
    "topic:terraform stars:>50 forks:>5 archived:false NOT example",
    "topic:monitoring stars:>100 forks:>10 archived:false NOT tutorial",
    "topic:ci-cd stars:>50 forks:>5 archived:false NOT tutorial",
    "topic:infrastructure stars:>100 forks:>10 archived:false NOT example",
    
    # Data & Machine Learning
    "topic:machine-learning stars:>100 forks:>10 archived:false NOT tutorial NOT course NOT notebook",
    "topic:deep-learning stars:>100 forks:>10 archived:false NOT tutorial NOT example NOT course",
    "topic:data-science stars:>100 forks:>10 archived:false NOT tutorial NOT notebook NOT learn",
    "topic:data-engineering stars:>50 forks:>5 archived:false NOT tutorial NOT example",
    "topic:nlp stars:>100 forks:>10 archived:false NOT tutorial NOT course",
    "topic:computer-vision stars:>100 forks:>10 archived:false NOT tutorial NOT course",
    "topic:pytorch stars:>100 forks:>10 archived:false NOT tutorial NOT example",
    "topic:tensorflow stars:>100 forks:>10 archived:false NOT tutorial NOT example",
    
    # Databases & Storage
    "topic:database stars:>100 forks:>10 archived:false NOT tutorial NOT example",
    "topic:nosql stars:>50 forks:>5 archived:false NOT example",
    "topic:sql stars:>50 forks:>5 archived:false NOT tutorial NOT learn",
    "topic:postgresql stars:>50 forks:>5 archived:false NOT tutorial",
    "topic:mongodb stars:>50 forks:>5 archived:false NOT tutorial",
    
    # CLI & Developer Tools
    "topic:cli stars:>100 forks:>5 archived:false NOT tutorial NOT example",
    "topic:developer-tools stars:>100 forks:>10 archived:false NOT tutorial",
    "topic:productivity stars:>100 forks:>10 archived:false NOT template",
    "topic:automation stars:>100 forks:>10 archived:false NOT tutorial NOT example",
    "topic:terminal stars:>50 forks:>5 archived:false NOT tutorial",
    
    # Security & Cryptography
    "topic:security stars:>100 forks:>10 archived:false NOT tutorial NOT learn",
    "topic:cryptography stars:>50 forks:>5 archived:false NOT tutorial NOT example",
    "topic:penetration-testing stars:>50 forks:>5 archived:false NOT tutorial",
    "topic:cybersecurity stars:>50 forks:>5 archived:false NOT tutorial",
    
    # API & Networking
    "topic:api stars:>100 forks:>10 archived:false NOT tutorial NOT example NOT template",
    "topic:rest-api stars:>50 forks:>5 archived:false NOT boilerplate NOT starter",
    "topic:graphql stars:>100 forks:>10 archived:false NOT tutorial NOT example",
    "topic:networking stars:>50 forks:>5 archived:false NOT tutorial",
    "topic:http stars:>50 forks:>5 archived:false NOT tutorial",
    
    # Mobile Development
    "topic:android stars:>100 forks:>10 archived:false NOT tutorial NOT example NOT template",
    "topic:ios stars:>100 forks:>10 archived:false NOT tutorial NOT example NOT sample",
    "topic:react-native stars:>100 forks:>10 archived:false NOT template NOT starter",
    "topic:flutter stars:>100 forks:>10 archived:false NOT template NOT example",
    "topic:mobile stars:>100 forks:>10 archived:false NOT tutorial NOT example",
    
    # Game Development
    "topic:game-engine stars:>100 forks:>10 archived:false NOT tutorial NOT example",
    "topic:gamedev stars:>100 forks:>10 archived:false NOT tutorial NOT assets",
    "topic:unity stars:>50 forks:>5 archived:false NOT tutorial NOT example",
    
    # Systems & Low-Level
    "topic:operating-system stars:>100 forks:>10 archived:false NOT tutorial",
    "topic:compiler stars:>50 forks:>5 archived:false NOT tutorial NOT learn",
    "topic:embedded stars:>50 forks:>5 archived:false NOT tutorial NOT example",
    "topic:linux stars:>100 forks:>10 archived:false NOT tutorial",
    
    # Blockchain & Web3
    "topic:blockchain stars:>100 forks:>10 archived:false NOT tutorial NOT example",
    "topic:cryptocurrency stars:>100 forks:>10 archived:false NOT tutorial NOT learn",
    "topic:ethereum stars:>50 forks:>5 archived:false NOT tutorial NOT example",
    "topic:smart-contracts stars:>50 forks:>5 archived:false NOT tutorial",
    
    # Cloud & Serverless
    "topic:serverless stars:>50 forks:>5 archived:false NOT tutorial NOT example",
    "topic:aws stars:>100 forks:>10 archived:false NOT tutorial NOT example",
    "topic:cloud stars:>100 forks:>10 archived:false NOT tutorial",
    
    # Testing & Quality
    "topic:testing stars:>100 forks:>10 archived:false NOT tutorial NOT example",
    "topic:test-automation stars:>50 forks:>5 archived:false NOT tutorial",
    
    # By License Type
    "license:mit stars:>100 forks:>10 archived:false NOT tutorial NOT awesome",
    "license:apache-2.0 stars:>100 forks:>10 archived:false NOT tutorial NOT awesome",
    "license:bsd-3-clause stars:>50 forks:>5 archived:false NOT tutorial",
    "license:gpl-3.0 stars:>100 forks:>10 archived:false NOT tutorial NOT awesome",
    
    # Combination Queries for Maximum Quality
    "stars:>200 forks:>20 pushed:>2023-06-01 archived:false license:mit NOT tutorial NOT awesome NOT roadmap",
    "stars:>100 forks:>30 archived:false good-first-issues:>3 NOT tutorial NOT awesome NOT example",
    "stars:>500 forks:>50 archived:false pushed:>2023-01-01 NOT tutorial NOT boilerplate",
    "stars:>100 forks:>10 archived:false pushed:>2024-01-01 NOT tutorial NOT awesome NOT example",
    
    # Well-maintained projects
    "stars:>100 forks:>10 archived:false pushed:>2024-06-01 NOT tutorial NOT learn",
    "stars:>200 has:releases archived:false pushed:>2023-01-01 NOT tutorial",
    
    # Projects with documentation
    "stars:>100 forks:>10 has:wiki archived:false NOT tutorial NOT awesome NOT roadmap",
    
    # Multi-contributor projects
    "stars:>100 forks:>20 archived:false pushed:>2024-01-01 NOT tutorial NOT example",
    
    # Cross-language coverage
    "stars:>100 forks:>10 archived:false NOT tutorial NOT awesome NOT learn NOT course",
]

MINIMUM_STARS = 100;
MINIMUM_FORKS = 10;
STATE_FILE = "ingestion_state.json";
MIN_RATE_LIMIT = 50;
TOTAL_PAGES = 10;

client = MongoClient(MONGO_URI)
db = client["findmyrepo"]
collection = db["repos"]

logger.info("Loading embedding model")
model = SentenceTransformer("all-MiniLM-L6-v2")

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

def generate_embeddings(text=" "):
    return model.encode(text, show_progress_bar=False).tolist()

def get_rate_limit():
    try:
        response = requests.get("https://api.github.com/rate_limit", headers=headers)
        response.raise_for_status()
        data = response.json()
        remaining = data['rate']['remaining']
        reset = data['rate']['reset']
        return remaining,reset
    except Exception as e:
        logger.warning(f"Warning: Could not check rate limit: {e}")
    return 0, 0

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
            return data.get("last_index", -1)
    return -1

def save_state(index):
    with open(STATE_FILE, 'w') as f:
        json.dump({"last_index": index, "timestamp": time.time()}, f)

# This is generated -> Too lazy to do myself
def clean_readme_content(raw_text):
    """
    Removes noise from READMEs to improve vector search quality.
    """
    if not raw_text:
        return ""

    # 1. Remove Markdown Code Blocks (```python ... ```)
    # These confuse semantic search. We want descriptions, not syntax.
    text = re.sub(r'```[\s\S]*?```', '', raw_text)

    # 2. Remove HTML Tags (e.g., <div align="center">, <img src...>)
    # BeautifulSoup is safer than regex for HTML
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ")

    # 3. Remove Markdown Links/Images but keep text
    # Convert [Click Here](http://...) to "Click Here"
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text) # Remove images
    text = re.sub(r'\[([^\]]+)\]\(.*?\)', r'\1', text) # Keep link text

    # 4. Remove Badges & Shields (Common in GitHub Readmes)
    # e.g., [![Build Status]...]
    text = re.sub(r'\[!\[.*?\]\s*\]', '', text)

    # 5. Collapse multiple spaces/newlines into single space
    text = re.sub(r'\s+', ' ', text).strip()

    # 6. Limit Length (First 2000 chars is usually the "What is this?" part)
    return text[:2000]


def get_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
        return clean_readme_content(content)
    except Exception as e:
        logger.error(f"Error occurred while fetching repo reachme {owner}/{repo}: {e}")
    return None

def get_languages(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/languages"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return list(data.keys())
    except Exception as e:
        logger.error(f"Error occurred while fetching repo languages {owner}/{repo}: {e}")
    return None

def is_valid_project(repo):
    exclude_terms = ['tutorial', 'awesome', 'roadmap', 'learn', 
                     'course', 'resources', 'interview', 'cheatsheet',
                     'curated', 'collection', 'examples']
    
    name_desc = ((repo.get('name') or '') + ' ' + (repo.get('description') or '')).lower()
    if any(term in name_desc for term in exclude_terms):
        return False
    
    # Exclude by topics
    exclude_topics = {'tutorial', 'learning', 'awesome-list', 
                      'roadmap', 'resources', 'course'}
    if any(topic in exclude_topics for topic in repo.get('topics', [])):
        return False
    
    if not repo.get('language'):
        return False
    
    if repo.get('stargazers_count', 0) < MINIMUM_STARS:
        return False
    if repo.get('forks_count', 0) < MINIMUM_FORKS:
        return False
    if repo.get('size', 0) < 100:  # KB
        return False
    
    if not repo.get('license'):
        return False
    
    return True


def fetch_repos(query="", sort="updated", order="desc", per_page=100):
    logger.info(f"Fetching repos for query: {query}, sorting: {sort}, order: {order}, Per Page: {per_page}")
    url = "https://api.github.com/search/repositories"

    try:
        repos = []
        for page in range(1, TOTAL_PAGES+1):
            params = {
                "q": query,
                "sort": sort,
                "order": order,
                "per_page": per_page,
                "page": page
            }
            logger.info(f"Fetching page {page}/{TOTAL_PAGES}")
            response = requests.get(url, params=params, headers=headers)

            if response.status_code==403 or response.status_code==429:
                logger.warning("!!!!!! RATE LIMIT REACHED !!!!!!")
                return False

            response.raise_for_status()
            curr_repos = response.json().get("items", [])
            repos.extend(curr_repos)
        
        total = len(repos)
        logger.info(f"Found {total} repos. Starting enrichment...")

        for i in range(len(repos)):
            repo = repos[i]
            if not is_valid_project(repo):
                logger.info(f"Skipped ({i+1}/{total}) - {repo.get('owner', {}).get('login', '')}/{repo.get('name', '')} (Invalid Project)")
                continue

            remaining, _ = get_rate_limit()
            if remaining<MIN_RATE_LIMIT:
                logger.warning(f"!!! Low Rate limit: {remaining}. Stopping...")
                return False
            
            repo_id = repo.get("id")
            name = repo.get("name", "")
            owner = repo.get("owner", {}).get("login", "")
            description = repo.get("description") or ""
            stars = repo.get("stargazers_count", 0)
            language = repo.get("language") or ""
            issues = repo.get("open_issues_count", 0)
            topics = repo.get("topics") or []
            pushed_at = repo.get("pushed_at", "")

            existing_repo = collection.find_one({"github_id": repo_id})
            if existing_repo:
                logger.info(f"Skipped ({i+1}/{total}) - {owner}/{name} (Already in database)")
                continue

            languages_list = get_languages(owner, name)
            readme = get_readme(owner, name)

            if languages_list is None or readme is None or name == "" or description == "":
                logger.info(f"Skipped ({i+1}/{total}) - {repo.get('owner', {}).get('login', '')}/{repo.get('name', '')} (Incomplete info)")
                continue

            to_embed = (f"Title: {name}. Languages: {', '.join(languages_list)}. Topics: {', '.join(topics)}. Overview: {readme}")

            vector = generate_embeddings(to_embed)

            document = {
                "github_id": repo_id,
                "name": name,
                "owner": owner,
                "description": description,
                "stars": stars,
                "languages": languages_list,
                "issues": issues,
                "topics": topics,
                "pushed_at": pushed_at,
                "readme": readme,
                "embedding": vector,
                "last_crawled": time.time()
            }

            collection.update_one(
                {"github_id": repo_id},
                {"$set": document},
                upsert=True
            )

            logger.info(f"--> Processed ({i+1}/{total}): {owner}/{name}")
            time.sleep(0.1)
        
        return True

    except Exception as e:
        logger.error(f"Error occurred while fetching repos: {e}")
        return False


def main():
    start_index = load_state()+1

    logger.info(f"Startings from Index {start_index} (Skipped {start_index} queries)")
    
    i = start_index
    while i<len(SEARCH_QUERIES):
        query = SEARCH_QUERIES[i]

        remaining, reset_ts = get_rate_limit()
        logger.info(f"API Quota Remaining: {remaining}")

        if remaining<MIN_RATE_LIMIT:
            wait_time = int(reset_ts - time.time()) + 10
            logger.info(f"Limit reached! Sleeping for {wait_time}")
            time.sleep(wait_time)
        
        success = fetch_repos(query)
        if not success:
            logger.info(f"Requerying Index {i}")
            continue
            
        save_state(i)
        logger.info(f"State Saved: Completed Index: {i}")
        i+=1
    
    logger.info("COMPLETED ALL THE QUERIES!")

if __name__ == "__main__":
    main()