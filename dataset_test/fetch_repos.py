import requests
import json
import time
import re
from datetime import datetime
from typing import List, Dict, Set, Optional
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
        self.all_repos = {}
        self.rate_limit_remaining = 60
        self.state_file = 'fetcher_state.json'
        self.progress_state = self.load_state()
        
        # Filtering thresholds
        self.min_stars = 10
        self.min_forks = 3
        self.max_fork_star_ratio = 2.0  # Forks/Stars ratio
        
        # Patterns for filtering out non-legitimate projects
        self.tutorial_patterns = [
            r'\btutorial\b', r'\bexample\b', r'\bdemo\b', r'\bsample\b',
            r'\bboilerplate\b', r'\btemplate\b', r'\bstarter\b',
            r'\blearning\b', r'\bcourse\b', r'\bworkshop\b',
            r'\bpractice\b', r'\bexercise\b'
        ]
        
        self.portfolio_patterns = [
            r'\bportfolio\b', r'\bresume\b', r'\bcv\b', r'\bpersonal[\s-]?site\b',
            r'\bmy[\s-]?website\b', r'\bprofile\b'
        ]
        
        self.awesome_patterns = [
            r'^awesome[\s-]', r'\bawesome[\s-]list\b', r'\bcurated[\s-]list\b',
            r'\bresources\b.*\blist\b', r'\bcollection\b'
        ]
    
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
            'enriched_repos': [],
            'filtered_count': 0
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
                
                if self.rate_limit_remaining < 5:
                    print("\n" + "="*70)
                    print("RATE LIMIT ALMOST EXHAUSTED!")
                    print(f"Resets at: {reset_time}")
                    print("="*70)
                    return False
                return self.rate_limit_remaining
            return 0
        except Exception as e:
            print(f"Error checking rate limit: {e}")
            return self.rate_limit_remaining
    
    def wait_for_rate_limit(self) -> bool:
        """Check rate limit and return False if we should stop"""
        if self.rate_limit_remaining < 10:
            result = self.check_rate_limit()
            if result is False:
                return False
        return True
    
    def matches_pattern(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the given regex patterns"""
        if not text:
            return False
        text_lower = text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in patterns)
    
    def is_legitimate_project(self, repo: Dict) -> tuple[bool, Optional[str]]:
        """
        Tier 2: Validate if a repository is a legitimate project.
        Returns (is_valid, reason_for_rejection)
        """
        name = repo.get('name', '')
        description = repo.get('description', '') or ''
        full_name = repo.get('full_name', '')
        
        # Check for license
        if not repo.get('license'):
            return False, "No license"
        
        # Check for meaningful description
        if not description or len(description.strip()) < 20:
            return False, "No meaningful description"
        
        # Check if it's a tutorial/demo/example
        combined_text = f"{name} {description}"
        if self.matches_pattern(combined_text, self.tutorial_patterns):
            return False, "Tutorial/demo/example project"
        
        # Check if it's a portfolio/personal site
        if self.matches_pattern(combined_text, self.portfolio_patterns):
            return False, "Portfolio/personal project"
        
        # Check if it's an "awesome" list
        if self.matches_pattern(combined_text, self.awesome_patterns):
            return False, "Curated list/awesome collection"
        
        # Check engagement ratios
        stars = repo.get('stargazers_count', 0)
        forks = repo.get('forks_count', 0)
        watchers = repo.get('watchers_count', 0)
        open_issues = repo.get('open_issues_count', 0)
        
        # High fork-to-star ratio suggests inactive fork
        if stars > 0 and forks / stars > self.max_fork_star_ratio:
            return False, f"High fork/star ratio ({forks}/{stars})"
        
        # Very low engagement
        if stars > 50 and watchers < 2:
            return False, "Low engagement (watchers)"
        
        # No activity indicators
        if stars > 100 and open_issues == 0 and forks < 5:
            return False, "Low engagement (no issues/forks)"
        
        return True, None
    
    def build_tier1_query(self, base_query: str) -> str:
        """
        Tier 1: Build query with database-level pre-filtering
        """
        filters = [
            f"stars:>={self.min_stars}",
            f"forks:>={self.min_forks}",
            "is:public",
            "archived:false"
        ]
        
        # Combine base query with filters
        if base_query:
            return f"{base_query} {' '.join(filters)}"
        return ' '.join(filters)
    
    def fetch_page(self, query: str, page: int, per_page: int, sort: str) -> tuple:
        """Fetch a single page of search results"""
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
                
                # Apply Tier 2 filtering
                valid_repos = []
                filtered_out = 0
                for item in items:
                    is_valid, reason = self.is_legitimate_project(item)
                    if is_valid:
                        valid_repos.append(item)
                    else:
                        filtered_out += 1
                
                return {
                    'success': True,
                    'page': page,
                    'repos': valid_repos,
                    'filtered_out': filtered_out,
                    'total_items': len(items),
                    'total_count': total_count
                }
            elif response.status_code == 403:
                return {'success': False, 'page': page, 'error': 'rate_limit'}
            else:
                return {'success': False, 'page': page, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'page': page, 'error': str(e)}
    
    def search_repos(self, query: str, max_results: int = 100, sort: str = 'stars') -> Optional[List[Dict]]:
        """Generic function to search repositories with Tier 1 filtering and parallel page fetching"""
        repos = []
        per_page = 100
        max_pages = min((max_results + per_page - 1) // per_page, 10)  # GitHub limits to 1000 results (10 pages)
        
        # Apply Tier 1 filters
        filtered_query = self.build_tier1_query(query)
        
        print(f"Searching: {filtered_query} (target: {max_results} repos)")
        
        total_filtered_out = 0
        
        # Process pages in batches for parallel fetching
        batch_size = 5  # Fetch 5 pages at a time
        
        for batch_start in range(0, max_pages, batch_size):
            batch_pages = range(batch_start + 1, min(batch_start + batch_size + 1, max_pages + 1))
            
            if not self.wait_for_rate_limit():
                print(f"  Rate limit reached (collected {len(repos)} repos so far)")
                return None  # Signal rate limit hit
            
            print(f"  Fetching pages {batch_pages.start}-{batch_pages.stop - 1} in parallel...", end=' ')
            
            # Fetch pages in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
                future_to_page = {
                    executor.submit(self.fetch_page, filtered_query, page, per_page, sort): page 
                    for page in batch_pages
                }
                
                batch_results = []
                for future in concurrent.futures.as_completed(future_to_page):
                    result = future.result()
                    batch_results.append(result)
                
                # Sort results by page number to maintain order
                batch_results.sort(key=lambda x: x.get('page', 0))
                
                # Process results
                batch_valid_repos = 0
                batch_filtered = 0
                
                for result in batch_results:
                    if not result['success']:
                        if result.get('error') == 'rate_limit':
                            print("\nRate limit exceeded!")
                            return None  # Signal rate limit hit
                        else:
                            print(f"\nError on page {result['page']}: {result.get('error')}")
                        continue
                    
                    page_repos = result.get('repos', [])
                    if not page_repos:
                        print(f"\n  Page {result['page']}: No more results")
                        return repos[:max_results]
                    
                    repos.extend(page_repos)
                    batch_valid_repos += len(page_repos)
                    batch_filtered += result.get('filtered_out', 0)
                    total_filtered_out += result.get('filtered_out', 0)
                
                print(f"Got {batch_valid_repos} valid repos (filtered {batch_filtered}) | Rate limit: {self.rate_limit_remaining}")
                
                # Check if we have enough repos
                if len(repos) >= max_results:
                    break
        
        print(f"  Search complete: collected {len(repos)} repos (filtered out {total_filtered_out})")
        self.progress_state['filtered_count'] = self.progress_state.get('filtered_count', 0) + total_filtered_out
        return repos[:max_results]
    
    def fetch_top_repos(self, limit: int = 10000) -> bool:
        """Fetch top starred repositories"""
        task_name = 'top_repos'
        if self.is_task_complete(task_name):
            print(f"\n=== Skipping Top Repos (already completed) ===")
            return True
        
        print("\n=== Fetching Top Starred Repos ===")
        query = "help-wanted-issues:>5"
        repos = self.search_repos(query, limit, sort='stars')
        
        if repos is None:
            print("Rate limit reached during top repos fetch")
            return False
        
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
        return True
    
    def fetch_gsoc_repos(self, limit: int = 500) -> bool:
        """Fetch GSoC related repositories"""
        task_name = 'gsoc_repos'
        if self.is_task_complete(task_name):
            print(f"\n=== Skipping GSoC Repos (already completed) ===")
            return True
        
        print("\n=== Fetching GSoC Repos ===")
        queries = [
            'gsoc in:name,description',
            'google-summer-of-code in:name,description',
            'topic:gsoc',
            'topic:google-summer-of-code'
        ]
        
        for query in queries:
            repos = self.search_repos(query, limit // len(queries))
            if repos is None:
                print("Rate limit reached during GSoC repos fetch")
                return False
            
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
        return True
    
    def fetch_hacktoberfest_repos(self, limit: int = 500) -> bool:
        """Fetch Hacktoberfest repositories"""
        task_name = 'hacktoberfest_repos'
        if self.is_task_complete(task_name):
            print(f"\n=== Skipping Hacktoberfest Repos (already completed) ===")
            return True
        
        print("\n=== Fetching Hacktoberfest Repos ===")
        queries = [
            'hacktoberfest in:name,description',
            'topic:hacktoberfest'
        ]
        
        for query in queries:
            repos = self.search_repos(query, limit // len(queries))
            if repos is None:
                print("Rate limit reached during Hacktoberfest repos fetch")
                return False
            
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
        return True
    
    def fetch_repos_by_topics(self, topics: List[str], limit_per_topic: int = 100) -> bool:
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
            
            if repos is None:
                print("Rate limit reached during topics fetch")
                return False
            
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
        
        return True
    
    def fetch_repos_by_languages(self, languages: List[str], limit_per_lang: int = 100) -> bool:
        """Fetch repositories by programming languages"""
        print("\n=== Fetching Repos by Languages ===")
        
        for language in languages:
            task_name = f'language_{language}'
            if self.is_task_complete(task_name):
                print(f"Skipping language: {language} (already completed)")
                continue
            
            print(f"Language: {language}")
            query = f'language:{language}'
            repos = self.search_repos(query, limit_per_lang)
            
            if repos is None:
                print("Rate limit reached during languages fetch")
                return False
            
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
        
        return True
    
    def fetch_good_first_issue_repos(self, limit: int = 300) -> bool:
        """Fetch repositories with good-first-issue label"""
        task_name = 'good_first_issue'
        if self.is_task_complete(task_name):
            print(f"\n=== Skipping Good First Issue Repos (already completed) ===")
            return True
        
        print("\n=== Fetching Good First Issue Repos ===")
        queries = [
            'good-first-issue in:name,description',
            'help-wanted in:name,description'
        ]
        
        for query in queries:
            repos = self.search_repos(query, limit // len(queries))
            if repos is None:
                print("Rate limit reached during good first issue repos fetch")
                return False
            
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
        return True
    
    def fetch_underrated_repos(self, limit: int = 300) -> bool:
        """Fetch potentially underrated repositories"""
        task_name = 'underrated'
        if self.is_task_complete(task_name):
            print(f"\n=== Skipping Underrated Repos (already completed) ===")
            return True
        
        print("\n=== Fetching Underrated Repos ===")
        queries = [
            'stars:100..1000 forks:>20',
            'stars:500..2000 pushed:>2024-01-01',
            'stars:200..1500 watchers:>50'
        ]
        
        for query in queries:
            repos = self.search_repos(query, limit // len(queries), sort='updated')
            if repos is None:
                print("Rate limit reached during underrated repos fetch")
                return False
            
            for repo in repos:
                full_name = repo['full_name']
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
        return True
    
    def save_current_data(self, filename: str = 'github_repos_raw.json'):
        """Save current data"""
        if not self.all_repos:
            return
        
        output = {
            'metadata': {
                'total_repos': len(self.all_repos),
                'fetched_at': datetime.now().isoformat(),
                'github_token_used': self.token is not None,
                'completed_tasks': self.progress_state['completed_tasks'],
                'filtered_count': self.progress_state.get('filtered_count', 0),
                'filtering_criteria': {
                    'min_stars': self.min_stars,
                    'min_forks': self.min_forks,
                    'max_fork_star_ratio': self.max_fork_star_ratio,
                    'requires_license': True,
                    'requires_description': True
                }
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
                'completed_tasks': self.progress_state['completed_tasks'],
                'filtered_count': self.progress_state.get('filtered_count', 0),
                'filtering_criteria': {
                    'min_stars': self.min_stars,
                    'min_forks': self.min_forks,
                    'max_fork_star_ratio': self.max_fork_star_ratio,
                    'requires_license': True,
                    'requires_description': True
                }
            },
            'repositories': self.all_repos
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(self.all_repos)} unique repositories")
        print(f"Filtered out {self.progress_state.get('filtered_count', 0)} non-legitimate projects")
        
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
            'languages': list(enriched_data.get('languages_breakdown', {}).keys()) if enriched_data.get('languages_breakdown') else [],
            'is_gsoc': repo_data.get('is_gsoc', False),
            'is_hacktoberfest': repo_data.get('is_hacktoberfest', False),
            'is_underrated': repo_data.get('is_underrated', False),
            'has_good_first_issues': repo_data.get('has_good_first_issues', False),
            'sources': repo_data.get('source', [])
        }

    def enrich_repo_data_single(self, repo_full_name: str) -> Dict:
        """Fetch additional details for a repository"""
        if not self.wait_for_rate_limit():
            return None
        
        enriched = {}
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

    def enrich_all_repos(self, input_file: str = 'github_repos_raw.json', 
                        output_file: str = 'github_repos_enriched.json',
                        limit: int = None):
        """Enrich all repositories with additional data"""
        
        if self.progress_state['phase'] != 'enrichment':
            print("\n=== Phase 1 (Raw Data) not complete yet ===")
            return
        
        print(f"\n=== Enriching Repository Data ===")
        
        if not os.path.exists(input_file):
            print(f"Error: {input_file} not found!")
            return
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        repos = data['repositories']
        total = len(repos)
        
        enriched_repos = {}
        already_enriched = set()
        
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
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
        
        repos_to_enrich = {k: v for k, v in repos.items() if k not in already_enriched}
        
        if limit:
            print(f"Limiting enrichment to {limit} repositories")
            repos_to_enrich = dict(list(repos_to_enrich.items())[:limit])
        
        if not repos_to_enrich:
            print("All repositories already enriched!")
            return
        
        print(f"Will enrich {len(repos_to_enrich)} repositories")
        
        progress_counter = len(already_enriched)
        batch_size = 10
        repos_list = list(repos_to_enrich.items())

        for batch_start in range(0, len(repos_list), batch_size):
            batch = repos_list[batch_start:batch_start + batch_size]
            
            print(f"\nProcessing batch {batch_start//batch_size + 1}/{(len(repos_list) + batch_size - 1)//batch_size}")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_repo = {executor.submit(self.enrich_repo_data_single, full_name): (full_name, repo_data) 
                                  for full_name, repo_data in batch}
                
                for future in concurrent.futures.as_completed(future_to_repo):
                    full_name, repo_data = future_to_repo[future]
                    current_index = progress_counter + len(enriched_repos) + 1
                    
                    try:
                        enriched = future.result()
                        
                        if enriched is None:
                            print("\n" + "="*70)
                            print("RATE LIMIT REACHED!")
                            print(f"Progress: {len(enriched_repos)}/{total} repos enriched")
                            print("Saving progress...")
                            self._save_enriched_data(enriched_repos, output_file, data['metadata'])
                            print("Run the script again after rate limit resets to continue.")
                            print("="*70)
                            return
                        
                        enriched_repos[full_name] = {
                            **repo_data,
                            'enriched_data': enriched
                        }
                        
                        self.progress_state['enrichment_progress'] = len(enriched_repos)
                        if full_name not in self.progress_state['enriched_repos']:
                            self.progress_state['enriched_repos'].append(full_name)
                        
                        print(f"Enriched {current_index}/{total}: {full_name}")
                        
                    except Exception as e:
                        print(f"Error enriching {full_name}: {e}")
            
            self._save_enriched_data(enriched_repos, output_file, data['metadata'])
            self.save_state()
            print(f"  Batch checkpoint saved ({len(enriched_repos)}/{total})")
    
    def _save_enriched_data(self, enriched_repos: Dict, filename: str, metadata: Dict):
        """Helper to save enriched data in clean format"""
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
                'completed_tasks': metadata.get('completed_tasks', []),
                'filtered_count': metadata.get('filtered_count', 0),
                'filtering_criteria': metadata.get('filtering_criteria', {})
            },
            'repositories': formatted_repos
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)


def main():
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', "")
    
    if not GITHUB_TOKEN:
        print("WARNING: No GitHub token provided. Rate limit will be 60 requests/hour.")
        print("Get a token from: https://github.com/settings/tokens")
        print("Then set it: export GITHUB_TOKEN='your_token_here'")
        print()
    
    fetcher = GitHubRepoFetcher(token=GITHUB_TOKEN)
    
    result = fetcher.check_rate_limit()
    if result is False:
        print("Rate limit exhausted. Please try again later.")
        return
    
    if os.path.exists('github_repos_raw.json'):
        fetcher.load_existing_repos('github_repos_raw.json')
        print("Resuming from previous run...")
    
    current_phase = fetcher.progress_state.get('phase', 'raw_data')
    
    if current_phase == 'raw_data':
        print("\n" + "="*70)
        print("PHASE 1: Fetching Raw Repository Data")
        print("Using Tier 1 + Tier 2 Filtering")
        print(f"  - Min Stars: {fetcher.min_stars}")
        print(f"  - Min Forks: {fetcher.min_forks}")
        print(f"  - Requires: License, Meaningful Description, Issues Enabled")
        print(f"  - Filters out: Tutorials, Demos, Portfolios, Awesome Lists")
        print("="*70)
        
        if not fetcher.fetch_top_repos(limit=10000):
            print("\nRate limit reached. Please run again after limit resets.")
            return
        
        if not fetcher.fetch_gsoc_repos(limit=500):
            print("\nRate limit reached. Please run again after limit resets.")
            return
        
        if not fetcher.fetch_hacktoberfest_repos(limit=500):
            print("\nRate limit reached. Please run again after limit resets.")
            return
        
        topics = ['machine-learning', 'web-development', 'data-science', 
                  'artificial-intelligence', 'blockchain', 'cybersecurity',
                  'mobile-development', 'devops', 'open-source']
        if not fetcher.fetch_repos_by_topics(topics, limit_per_topic=500):
            print("\nRate limit reached. Please run again after limit resets.")
            return
        
        languages = ['Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 
                    'Rust', 'C++', 'Ruby', 'PHP', 'Swift']
        if not fetcher.fetch_repos_by_languages(languages, limit_per_lang=500):
            print("\nRate limit reached. Please run again after limit resets.")
            return
        
        if not fetcher.fetch_good_first_issue_repos(limit=500):
            print("\nRate limit reached. Please run again after limit resets.")
            return
        
        if not fetcher.fetch_underrated_repos(limit=500):
            print("\nRate limit reached. Please run again after limit resets.")
            return
        
        fetcher.save_raw_data('github_repos_raw.json')
        
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
        
        result = fetcher.check_rate_limit()
        if result is False:
            print("Rate limit exhausted. Please try again later.")
            return
        
        fetcher.enrich_all_repos('github_repos_raw.json', 'github_repos_enriched.json')
        
        print("\n" + "="*70)
        print("All Done! Files created:")
        print("  1. github_repos_raw.json - Raw repository data")
        print("  2. github_repos_enriched.json - Enriched with languages, topics, README, etc.")
        print("  3. fetcher_state.json - Progress tracking (can be deleted after completion)")
        print("="*70)


if __name__ == '__main__':
    main()