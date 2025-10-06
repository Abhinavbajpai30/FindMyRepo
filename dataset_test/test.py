import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Set
import os
import concurrent.futures
import base64

class GitHubRepoFetcher:
    def __init__(self, token: str = None):
        """
        Initialize the fetcher with optional GitHub token for higher rate limits.
        Get token from: https://github.com/settings/tokens
        """
        self.token = token
        self.headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        if token:
            self.headers['Authorization'] = f'token {token}'
        
        self.base_url = 'https://api.github.com'
        self.all_repos = {}  # Use dict to avoid duplicates by full_name
        self.rate_limit_remaining = 60
        self.state_file = 'fetcher_state.json'
        self.progress_state = self.load_state()
    
    def load_state(self) -> Dict:
        """Load previous progress state"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    print(f"Loaded previous state from {self.state_file}")
                    return state
            except Exception as e:
                print(f"Error loading state: {e}")
        return {
            'phase': 'raw_data',
            'completed_tasks': [],
            'enrichment_progress': 0,
            'enriched_repos': []
        }
    
    def save_state(self):
        """Save current progress state"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_state, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def mark_task_complete(self, task_name: str):
        """Mark a fetching task as complete"""
        if task_name not in self.progress_state['completed_tasks']:
            self.progress_state['completed_tasks'].append(task_name)
            self.save_state()
    
    def is_task_complete(self, task_name: str) -> bool:
        """Check if a task was already completed"""
        return task_name in self.progress_state['completed_tasks']
    
    def check_rate_limit(self):
        """Check and display current rate limit status"""
        try:
            response = requests.get(f'{self.base_url}/rate_limit', headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.rate_limit_remaining = data['resources']['core']['remaining']
                reset_time = datetime.fromtimestamp(data['resources']['core']['reset'])
                print(f"Rate limit: {self.rate_limit_remaining} requests remaining. Resets at {reset_time}")
                
                # If rate limit is exhausted, save and exit
                if self.rate_limit_remaining < 5:
                    print("\n" + "="*70)
                    print("RATE LIMIT ALMOST EXHAUSTED!")
                    print(f"Resets at: {reset_time}")
                    print("Saving progress and exiting...")
                    print("Run the script again after rate limit resets to continue.")
                    print("="*70)
                    self.save_current_data()
                    self.save_state()
                    return False
                return self.rate_limit_remaining
            return 0
        except Exception as e:
            print(f"Error checking rate limit: {e}")
            return self.rate_limit_remaining
    
    def wait_for_rate_limit(self) -> bool:
        """
        Check rate limit and return False if we should stop
        Returns True if we can continue, False if we should stop
        """
        if self.rate_limit_remaining < 10:
            result = self.check_rate_limit()
            if result is False:
                return False
        return True
    
    def search_repos(self, query: str, max_results: int = 100, sort: str = 'stars') -> List[Dict]:
        """Generic function to search repositories"""
        repos = []
        per_page = 100
        max_pages = (max_results + per_page - 1) // per_page
        
        print(f"Searching: {query} (target: {max_results} repos)")
        
        for page in range(1, min(max_pages + 1, 11)):  # GitHub limits to 1000 results (10 pages)
            if not self.wait_for_rate_limit():
                print(f"  ⚠️  Stopping search due to rate limit (collected {len(repos)} repos so far)")
                return repos
            
            print(f"  📄 Fetching page {page}/{min(max_pages, 10)}...", end=' ')
            
            url = f'{self.base_url}/search/repositories'
            params = {
                'q': query,
                'sort': sort,
                'order': 'desc',
                'per_page': per_page,
                'page': page
            }
            
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    total_count = data.get('total_count', 0)
                    
                    if not items:
                        print("No more results")
                        break
                    
                    repos.extend(items)
                    print(f"✓ Got {len(items)} repos (total: {len(repos)}/{min(total_count, max_results)}) | Rate limit: {self.rate_limit_remaining}")
                    # time.sleep(2)  # Be nice to GitHub API
                    
                elif response.status_code == 403:
                    print("❌ Rate limit exceeded!")
                    if not self.wait_for_rate_limit():
                        return repos
                else:
                    print(f"❌ Error {response.status_code}: {response.text[:100]}")
                    break
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        print(f"  ✅ Search complete: collected {len(repos)} repos")
        return repos[:max_results]
    
    def fetch_top_repos(self, limit: int = 10000):
        """Fetch top starred repositories"""
        task_name = 'top_repos'
        if self.is_task_complete(task_name):
            print(f"\n=== Skipping Top Repos (already completed) ===")
            return
        
        print("\n=== Fetching Top Starred Repos ===")
        query = "stars:>300 help-wanted-issues:>15"  # Lowered threshold to get more repos
        repos = self.search_repos(query, limit, sort='stars')
        
        if repos is None:  # Rate limit hit
            return
        
        for repo in repos:
            full_name = repo['full_name']
            if full_name not in self.all_repos:
                self.all_repos[full_name] = {
                    'source': ['top_starred'],
                    'raw_data': repo
                }
            else:
                self.all_repos[full_name]['source'].append('top_starred')
        
        print(f"Fetched {len(repos)} top repos")
        self.mark_task_complete(task_name)
        self.save_current_data()
    
    def fetch_gsoc_repos(self, limit: int = 500):
        """Fetch GSoC (Google Summer of Code) related repositories"""
        task_name = 'gsoc_repos'
        if self.is_task_complete(task_name):
            print(f"\n=== Skipping GSoC Repos (already completed) ===")
            return
        
        print("\n=== Fetching GSoC Repos ===")
        queries = [
            'gsoc in:name,description,readme',
            'google-summer-of-code in:name,description',
            'topic:gsoc',
            'topic:google-summer-of-code'
        ]
        
        for query in queries:
            repos = self.search_repos(query, limit // len(queries))
            if repos is None:  # Rate limit hit
                self.save_current_data()
                return
            
            for repo in repos:
                full_name = repo['full_name']
                if full_name not in self.all_repos:
                    self.all_repos[full_name] = {
                        'source': ['gsoc'],
                        'is_gsoc': True,
                        'raw_data': repo
                    }
                else:
                    if 'gsoc' not in self.all_repos[full_name]['source']:
                        self.all_repos[full_name]['source'].append('gsoc')
                    self.all_repos[full_name]['is_gsoc'] = True
        
        print(f"Total unique GSoC repos: {sum(1 for r in self.all_repos.values() if r.get('is_gsoc'))}")
        self.mark_task_complete(task_name)
        self.save_current_data()
    
    def fetch_hacktoberfest_repos(self, limit: int = 500):
        """Fetch Hacktoberfest repositories"""
        task_name = 'hacktoberfest_repos'
        if self.is_task_complete(task_name):
            print(f"\n=== Skipping Hacktoberfest Repos (already completed) ===")
            return
        
        print("\n=== Fetching Hacktoberfest Repos ===")
        queries = [
            'hacktoberfest in:name,description,readme',
            'topic:hacktoberfest',
            'label:hacktoberfest'
        ]
        
        for query in queries:
            repos = self.search_repos(query, limit // len(queries))
            if repos is None:  # Rate limit hit
                self.save_current_data()
                return
            
            for repo in repos:
                full_name = repo['full_name']
                if full_name not in self.all_repos:
                    self.all_repos[full_name] = {
                        'source': ['hacktoberfest'],
                        'is_hacktoberfest': True,
                        'raw_data': repo
                    }
                else:
                    if 'hacktoberfest' not in self.all_repos[full_name]['source']:
                        self.all_repos[full_name]['source'].append('hacktoberfest')
                    self.all_repos[full_name]['is_hacktoberfest'] = True
        
        print(f"Total unique Hacktoberfest repos: {sum(1 for r in self.all_repos.values() if r.get('is_hacktoberfest'))}")
        self.mark_task_complete(task_name)
        self.save_current_data()
    
    def fetch_repos_by_topics(self, topics: List[str], limit_per_topic: int = 100):
        """Fetch repositories by topics"""
        print("\n=== Fetching Repos by Topics ===")
        
        for topic in topics:
            task_name = f'topic_{topic}'
            if self.is_task_complete(task_name):
                print(f"Skipping topic: {topic} (already completed)")
                continue
            
            print(f"Topic: {topic}")
            query = f'topic:{topic}'
            repos = self.search_repos(query, limit_per_topic)
            
            if repos is None:  # Rate limit hit
                self.save_current_data()
                return
            
            for repo in repos:
                full_name = repo['full_name']
                if full_name not in self.all_repos:
                    self.all_repos[full_name] = {
                        'source': [f'topic_{topic}'],
                        'topics': [topic],
                        'raw_data': repo
                    }
                else:
                    self.all_repos[full_name]['source'].append(f'topic_{topic}')
                    if 'topics' not in self.all_repos[full_name]:
                        self.all_repos[full_name]['topics'] = []
                    if topic not in self.all_repos[full_name]['topics']:
                        self.all_repos[full_name]['topics'].append(topic)
            
            self.mark_task_complete(task_name)
            self.save_current_data()
    
    def fetch_repos_by_languages(self, languages: List[str], limit_per_lang: int = 100):
        """Fetch repositories by programming languages"""
        print("\n=== Fetching Repos by Languages ===")
        
        for language in languages:
            task_name = f'language_{language}'
            if self.is_task_complete(task_name):
                print(f"Skipping language: {language} (already completed)")
                continue
            
            print(f"Language: {language}")
            query = f'language:{language} stars:>100'
            repos = self.search_repos(query, limit_per_lang)
            
            if repos is None:  # Rate limit hit
                self.save_current_data()
                return
            
            for repo in repos:
                full_name = repo['full_name']
                if full_name not in self.all_repos:
                    self.all_repos[full_name] = {
                        'source': [f'language_{language}'],
                        'languages': [language],
                        'raw_data': repo
                    }
                else:
                    self.all_repos[full_name]['source'].append(f'language_{language}')
                    if 'languages' not in self.all_repos[full_name]:
                        self.all_repos[full_name]['languages'] = []
                    if language not in self.all_repos[full_name]['languages']:
                        self.all_repos[full_name]['languages'].append(language)
            
            self.mark_task_complete(task_name)
            self.save_current_data()
    
    def fetch_good_first_issue_repos(self, limit: int = 300):
        """Fetch repositories with good-first-issue label"""
        task_name = 'good_first_issue'
        if self.is_task_complete(task_name):
            print(f"\n=== Skipping Good First Issue Repos (already completed) ===")
            return
        
        print("\n=== Fetching Good First Issue Repos ===")
        queries = [
            'good-first-issue in:name,description,readme',
            'label:"good first issue"',
            'help-wanted in:name,description'
        ]
        
        for query in queries:
            repos = self.search_repos(query, limit // len(queries))
            if repos is None:  # Rate limit hit
                self.save_current_data()
                return
            
            for repo in repos:
                full_name = repo['full_name']
                if full_name not in self.all_repos:
                    self.all_repos[full_name] = {
                        'source': ['good_first_issue'],
                        'has_good_first_issues': True,
                        'raw_data': repo
                    }
                else:
                    if 'good_first_issue' not in self.all_repos[full_name]['source']:
                        self.all_repos[full_name]['source'].append('good_first_issue')
                    self.all_repos[full_name]['has_good_first_issues'] = True
        
        print(f"Total repos with good first issues: {sum(1 for r in self.all_repos.values() if r.get('has_good_first_issues'))}")
        self.mark_task_complete(task_name)
        self.save_current_data()
    
    def fetch_underrated_repos(self, limit: int = 300):
        """Fetch potentially underrated repositories (high quality but lower stars)"""
        task_name = 'underrated'
        if self.is_task_complete(task_name):
            print(f"\n=== Skipping Underrated Repos (already completed) ===")
            return
        
        print("\n=== Fetching Underrated Repos ===")
        queries = [
            'stars:100..1000 forks:>20',
            'stars:500..2000 pushed:>2024-01-01',
            'stars:200..1500 watchers:>50'
        ]
        
        for query in queries:
            repos = self.search_repos(query, limit // len(queries), sort='updated')
            if repos is None:  # Rate limit hit
                self.save_current_data()
                return
            
            for repo in repos:
                full_name = repo['full_name']
                # Mark as underrated if stars < 2000 but has good engagement
                stars = repo.get('stargazers_count', 0)
                forks = repo.get('forks_count', 0)
                watchers = repo.get('watchers_count', 0)
                
                is_underrated = stars < 2000 and (forks > 20 or watchers > 50)
                
                if full_name not in self.all_repos:
                    self.all_repos[full_name] = {
                        'source': ['underrated'],
                        'is_underrated': is_underrated,
                        'raw_data': repo
                    }
                else:
                    if 'underrated' not in self.all_repos[full_name]['source']:
                        self.all_repos[full_name]['source'].append('underrated')
                    self.all_repos[full_name]['is_underrated'] = is_underrated
        
        print(f"Total underrated repos: {sum(1 for r in self.all_repos.values() if r.get('is_underrated'))}")
        self.mark_task_complete(task_name)
        self.save_current_data()
    
    def save_current_data(self, filename: str = 'github_repos_raw.json'):
        """Save current data (used for checkpointing)"""
        if not self.all_repos:
            return
        
        output = {
            'metadata': {
                'total_repos': len(self.all_repos),
                'fetched_at': datetime.now().isoformat(),
                'github_token_used': self.token is not None,
                'completed_tasks': self.progress_state['completed_tasks']
            },
            'repositories': self.all_repos
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    
    def load_existing_repos(self, filename: str = 'github_repos_raw.json'):
        """Load existing repos if resuming"""
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.all_repos = data.get('repositories', {})
                    print(f"Loaded {len(self.all_repos)} existing repos from {filename}")
                    return True
            except Exception as e:
                print(f"Error loading existing repos: {e}")
        return False
    
    def save_raw_data(self, filename: str = 'github_repos_raw.json'):
        """Save raw repository data"""
        print(f"\n=== Saving raw data to {filename} ===")
        
        output = {
            'metadata': {
                'total_repos': len(self.all_repos),
                'fetched_at': datetime.now().isoformat(),
                'github_token_used': self.token is not None,
                'completed_tasks': self.progress_state['completed_tasks']
            },
            'repositories': self.all_repos
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(self.all_repos)} unique repositories")
        
        # Print statistics
        print("\n=== Statistics ===")
        print(f"Total repos: {len(self.all_repos)}")
        print(f"GSoC repos: {sum(1 for r in self.all_repos.values() if r.get('is_gsoc'))}")
        print(f"Hacktoberfest repos: {sum(1 for r in self.all_repos.values() if r.get('is_hacktoberfest'))}")
        print(f"Good first issue repos: {sum(1 for r in self.all_repos.values() if r.get('has_good_first_issues'))}")
        print(f"Underrated repos: {sum(1 for r in self.all_repos.values() if r.get('is_underrated'))}")
      
    def format_repo_for_output(self, repo_data: Dict, enriched_data: Dict) -> Dict:
        """Format repository data to match the desired output structure"""
        raw = repo_data.get('raw_data', {})
        detailed = enriched_data.get('detailed_info', raw)
        
        return {
            'id': detailed.get('id'),
            'name': detailed.get('name'),
            'full_name': detailed.get('full_name'),
            'owner': detailed.get('owner', {}).get('login') if isinstance(detailed.get('owner'), dict) else detailed.get('owner'),
            'description': detailed.get('description'),
            'url': detailed.get('html_url'),
            'homepage': detailed.get('homepage'),
            'language': enriched_data.get('primary_language') or detailed.get('language'),
            'topics': enriched_data.get('topics', []) or detailed.get('topics', []),
            'stars': detailed.get('stargazers_count'),
            'forks': detailed.get('forks_count'),
            'open_issues': detailed.get('open_issues_count'),
            'created_at': detailed.get('created_at'),
            'updated_at': detailed.get('updated_at'),
            'license': enriched_data.get('license') or (detailed.get('license', {}).get('name') if detailed.get('license') else None),
            'has_issues': detailed.get('has_issues'),
            'has_wiki': detailed.get('has_wiki'),
            'default_branch': detailed.get('default_branch'),
            'readme': enriched_data.get('readme_content', ''),
            # 'readme_url': enriched_data.get('readme_url', ''),
            'languages': list(enriched_data.get('languages_breakdown', {}).keys()) if enriched_data.get('languages_breakdown') else [],
            # Add custom tags
            'is_gsoc': repo_data.get('is_gsoc', False),
            'is_hacktoberfest': repo_data.get('is_hacktoberfest', False),
            'is_underrated': repo_data.get('is_underrated', False),
            'has_good_first_issues': repo_data.get('has_good_first_issues', False),
            'sources': repo_data.get('source', [])
        }

    def enrich_repo_data_single(self, repo_full_name: str) -> Dict:
        """Fetch additional details for a repository using concurrent requests"""
        if not self.wait_for_rate_limit():
            return None
        
        enriched = {}
        
        # Define all API calls
        endpoints = {
            'details': f'{self.base_url}/repos/{repo_full_name}',
            'languages': f'{self.base_url}/repos/{repo_full_name}/languages',
            'readme': f'{self.base_url}/repos/{repo_full_name}/readme'
        }
        
        def fetch_endpoint(name, url):
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                if response.status_code == 200:
                    return (name, response.json())
                elif response.status_code == 403:
                    return (name, None)
            except Exception as e:
                print(f"  Error fetching {name} for {repo_full_name}: {e}")
            return (name, None)
        
        # Fetch all endpoints concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_endpoint = {executor.submit(fetch_endpoint, name, url): name 
                                  for name, url in endpoints.items()}
            
            for future in concurrent.futures.as_completed(future_to_endpoint):
                name, data = future.result()
                
                if data is None:
                    continue
                    
                if name == 'details':
                    enriched['detailed_info'] = data
                    enriched['primary_language'] = data.get('language')
                    enriched['license'] = data.get('license', {}).get('name') if data.get('license') else None
                    enriched['topics'] = data.get('topics', [])
                
                elif name == 'languages':
                    enriched['languages_breakdown'] = data
                
                elif name == 'readme':
                    enriched['readme_url'] = data.get('download_url')
                    enriched['readme_name'] = data.get('name')
                    
                    if data.get('content') and data.get('encoding') == 'base64':
                        try:
                            readme_content = base64.b64decode(data['content']).decode('utf-8')
                            enriched['readme_content'] = readme_content
                        except Exception as decode_error:
                            print(f"  Error decoding README content: {decode_error}")
        
        return enriched

    def enrich_repo_data(self, repo_full_name: str) -> Dict:
        """Fetch additional details for a repository"""
        if not self.wait_for_rate_limit():
            return None
        
        enriched = {}
        
        # Fetch detailed repo info
        try:
            url = f'{self.base_url}/repos/{repo_full_name}'
            response = requests.get(url, headers=self.headers, timeout=30)
            self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            
            if response.status_code == 200:
                repo_data = response.json()
                enriched['detailed_info'] = repo_data
                enriched['primary_language'] = repo_data.get('language')
                enriched['license'] = repo_data.get('license', {}).get('name') if repo_data.get('license') else None
                enriched['topics'] = repo_data.get('topics', [])
            elif response.status_code == 403:
                print(f"  Rate limit hit")
                return None
        except Exception as e:
            print(f"  Error fetching repo details for {repo_full_name}: {e}")
        
        # time.sleep(1)
        
        # Fetch languages
        if not self.wait_for_rate_limit():
            return enriched
        
        try:
            url = f'{self.base_url}/repos/{repo_full_name}/languages'
            response = requests.get(url, headers=self.headers, timeout=30)
            self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            
            if response.status_code == 200:
                enriched['languages_breakdown'] = response.json()
            elif response.status_code == 403:
                return enriched
        except Exception as e:
            print(f"  Error fetching languages for {repo_full_name}: {e}")
        
        # time.sleep(1)
        
        # Fetch README
        if not self.wait_for_rate_limit():
            return enriched

        try:
            import base64
            url = f'{self.base_url}/repos/{repo_full_name}/readme'
            response = requests.get(url, headers=self.headers, timeout=30)
            self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            
            if response.status_code == 200:
                readme_data = response.json()
                enriched['readme_url'] = readme_data.get('download_url')
                enriched['readme_name'] = readme_data.get('name')
                
                # Decode base64 content to UTF-8
                if readme_data.get('content') and readme_data.get('encoding') == 'base64':
                    try:
                        readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
                        enriched['readme_content'] = readme_content
                    except Exception as decode_error:
                        print(f"  Error decoding README content: {decode_error}")
            elif response.status_code == 403:
                return enriched
        except Exception as e:
            print(f"  Error fetching README for {repo_full_name}: {e}")

        # time.sleep(1)
        
        # Fetch contributors count
        if not self.wait_for_rate_limit():
            return enriched
        
        try:
            url = f'{self.base_url}/repos/{repo_full_name}/contributors'
            response = requests.get(url, headers=self.headers, params={'per_page': 1, 'anon': 'true'}, timeout=30)
            self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            
            if response.status_code == 200:
                link_header = response.headers.get('Link', '')
                if 'last' in link_header:
                    # Parse the last page number from Link header
                    import re
                    match = re.search(r'page=(\d+)>; rel="last"', link_header)
                    if match:
                        enriched['contributors_count'] = int(match.group(1))
                else:
                    enriched['contributors_count'] = len(response.json())
            elif response.status_code == 403:
                return enriched
        except Exception as e:
            print(f"  Error fetching contributors for {repo_full_name}: {e}")
        
        # time.sleep(1)
        
        return enriched
    
    def enrich_all_repos(self, input_file: str = 'github_repos_raw.json', 
                        output_file: str = 'github_repos_enriched.json',
                        limit: int = None):
        """Enrich all repositories with additional data"""
        
        # Check if we should start enrichment phase
        if self.progress_state['phase'] != 'enrichment':
            print("\n=== Phase 1 (Raw Data) not complete yet ===")
            return
        
        print(f"\n=== Enriching Repository Data ===")
        
        # Load raw data
        if not os.path.exists(input_file):
            print(f"Error: {input_file} not found!")
            return
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        repos = data['repositories']
        total = len(repos)
        
        # Load existing enriched data if resuming
        enriched_repos = {}
        already_enriched = set()
        
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    # Rebuild enriched_repos from formatted data
                    for repo in existing_data.get('repositories', []):
                        full_name = repo.get('full_name')
                        if full_name and full_name in repos:
                            already_enriched.add(full_name)
                            enriched_repos[full_name] = {
                                **repos[full_name],
                                'enriched_data': {
                                    'primary_language': repo.get('language'),
                                    'license': repo.get('license'),
                                    'topics': repo.get('topics', []),
                                    'readme_url': repo.get('readme'),
                                    'languages_breakdown': {lang: 0 for lang in repo.get('languages', [])}
                                }
                            }
                    print(f"Resuming: {len(already_enriched)} repos already enriched")
            except Exception as e:
                print(f"Could not load existing enriched data: {e}")
        
        # Get list of repos to enrich
        repos_to_enrich = {k: v for k, v in repos.items() if k not in already_enriched}
        
        if limit:
            print(f"Limiting enrichment to {limit} repositories")
            repos_to_enrich = dict(list(repos_to_enrich.items())[:limit])
        
        if not repos_to_enrich:
            print("All repositories already enriched!")
            return
        
        print(f"Will enrich {len(repos_to_enrich)} repositories")
        
        progress_counter = len(already_enriched)

        # Process repos in batches of 10 for parallel execution
        batch_size = 10
        repos_list = list(repos_to_enrich.items())

        for batch_start in range(0, len(repos_list), batch_size):
            batch = repos_list[batch_start:batch_start + batch_size]
            
            print(f"\nProcessing batch {batch_start//batch_size + 1}/{(len(repos_list) + batch_size - 1)//batch_size}")
            
            # Process batch concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_repo = {executor.submit(self.enrich_repo_data_single, full_name): (full_name, repo_data) 
                                  for full_name, repo_data in batch}
                
                for future in concurrent.futures.as_completed(future_to_repo):
                    full_name, repo_data = future_to_repo[future]
                    current_index = progress_counter + len(enriched_repos) + 1
                    
                    try:
                        enriched = future.result()
                        
                        if enriched is None:  # Rate limit hit
                            print("\n" + "="*70)
                            print("RATE LIMIT REACHED!")
                            print(f"Progress: {len(enriched_repos)}/{total} repos enriched")
                            print("Saving progress...")
                            self._save_enriched_data(enriched_repos, output_file, data['metadata'])
                            print("Run the script again after rate limit resets to continue.")
                            print("="*70)
                            return
                        
                        # Combine original and enriched data
                        enriched_repos[full_name] = {
                            **repo_data,
                            'enriched_data': enriched
                        }
                        
                        # Update progress
                        self.progress_state['enrichment_progress'] = len(enriched_repos)
                        if full_name not in self.progress_state['enriched_repos']:
                            self.progress_state['enriched_repos'].append(full_name)
                        
                        print(f"✓ Enriched {current_index}/{total}: {full_name}")
                        
                    except Exception as e:
                        print(f"✗ Error enriching {full_name}: {e}")
            
            # Save after each batch
            self._save_enriched_data(enriched_repos, output_file, data['metadata'])
            self.save_state()
            print(f"  Batch checkpoint saved ({len(enriched_repos)}/{total})")
    
    def _save_enriched_data(self, enriched_repos: Dict, filename: str, metadata: Dict):
        """Helper to save enriched data in clean format"""
        # Format all repos to match the desired structure
        formatted_repos = []
        
        for full_name, repo_data in enriched_repos.items():
            enriched_data = repo_data.get('enriched_data', {})
            formatted_repo = self.format_repo_for_output(repo_data, enriched_data)
            formatted_repos.append(formatted_repo)
        
        output = {
            'metadata': {
                'total_repos': len(formatted_repos),
                'fetched_at': metadata.get('fetched_at'),
                'enriched_at': datetime.now().isoformat(),
                'github_token_used': metadata.get('github_token_used'),
                'completed_tasks': metadata.get('completed_tasks', [])
            },
            'repositories': formatted_repos
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)


def main():
    # Initialize fetcher
    # IMPORTANT: Add your GitHub token here for higher rate limits (5000 req/hour vs 60 req/hour)
    # Get token from: https://github.com/settings/tokens
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', "")  # Or paste your token here
    
    if not GITHUB_TOKEN:
        print("WARNING: No GitHub token provided. Rate limit will be 60 requests/hour.")
        print("Get a token from: https://github.com/settings/tokens")
        print("Then set it: export GITHUB_TOKEN='your_token_here'")
        print()
    
    fetcher = GitHubRepoFetcher(token=GITHUB_TOKEN)
    
    # Check initial rate limit
    result = fetcher.check_rate_limit()
    if result is False:
        print("Rate limit exhausted. Please try again later.")
        return
    
    # Load existing data if resuming
    if os.path.exists('github_repos_raw.json'):
        fetcher.load_existing_repos('github_repos_raw.json')
        print("Resuming from previous run...")
    
    # Check current phase
    current_phase = fetcher.progress_state.get('phase', 'raw_data')
    
    if current_phase == 'raw_data':
        print("\n" + "="*70)
        print("PHASE 1: Fetching Raw Repository Data")
        print("="*70)
        
        # Fetch repositories from different sources
        fetcher.fetch_top_repos(limit=10000)
        fetcher.fetch_gsoc_repos(limit=500)
        fetcher.fetch_hacktoberfest_repos(limit=500)
        
        # Fetch by topics
        topics = ['machine-learning', 'web-development', 'data-science', 
                  'artificial-intelligence', 'blockchain', 'cybersecurity',
                  'mobile-development', 'devops', 'open-source']
        fetcher.fetch_repos_by_topics(topics, limit_per_topic=500)
        
        # Fetch by languages
        languages = ['Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 
                    'Rust', 'C++', 'Ruby', 'PHP', 'Swift']
        fetcher.fetch_repos_by_languages(languages, limit_per_lang=500)
        
        fetcher.fetch_good_first_issue_repos(limit=500)
        fetcher.fetch_underrated_repos(limit=500)
        
        # Save raw data
        fetcher.save_raw_data('github_repos_raw.json')
        
        # Mark phase 1 as complete
        fetcher.progress_state['phase'] = 'enrichment'
        fetcher.save_state()
        
        print("\n" + "="*70)
        print("Phase 1 Complete: Raw data saved!")
        print("="*70)
    
    if current_phase == 'enrichment' or fetcher.progress_state['phase'] == 'enrichment':
        print("\n" + "="*70)
        print("PHASE 2: Enriching Repository Data")
        print("This will take significantly longer due to multiple API calls per repo.")
        print("="*70)
        
        # Check rate limit before starting enrichment
        result = fetcher.check_rate_limit()
        if result is False:
            print("Rate limit exhausted. Please try again later.")
            return
        
        # Enrich data (remove limit parameter to enrich all repos)
        fetcher.enrich_all_repos('github_repos_raw.json', 'github_repos_enriched.json')
        
        print("\n" + "="*70)
        print("All Done! Files created:")
        print("  1. github_repos_raw.json - Raw repository data")
        print("  2. github_repos_enriched.json - Enriched with languages, topics, README, etc.")
        print("  3. fetcher_state.json - Progress tracking (can be deleted after completion)")
        print("="*70)


if __name__ == '__main__':
    main()