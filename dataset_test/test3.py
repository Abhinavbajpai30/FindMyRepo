import json
import re
import time
import requests
from typing import Dict, List, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class ReadmeCleaner:
    """Clean and normalize README content for embeddings/NLP."""
    
    # Patterns for removing badges and unwanted content
    BADGE_PATTERNS = [
        r'\[!\[.*?\]\(.*?\)\]\(.*?\)',  # Markdown badges with links
        r'!\[.*?\]\(https?://.*?badge.*?\)',  # Image badges
        r'!\[.*?\]\(https?://.*?shields\.io.*?\)',  # Shields.io badges
        r'!\[.*?\]\(https?://img\.shields\.io.*?\)',  # Shields.io images
        r'\[!\[.*?\]\]',  # Nested badge patterns
    ]
    
    # Sections to remove entirely
    REMOVE_SECTIONS = [
        r'##?\s*(?:installation|install|getting started|setup)',
        r'##?\s*(?:license|licensing)',
        r'##?\s*(?:acknowledgments?|credits|contributors?|thanks)',
        r'##?\s*(?:badges?|build status|downloads?)',
        r'##?\s*(?:contributing|contribution|how to contribute)',
        r'##?\s*(?:support|sponsorship|donate)',
    ]
    
    # Boilerplate phrases to remove
    BOILERPLATE_PHRASES = [
        r'made with ❤️.*',
        r'built with ❤️.*',
        r'crafted with ❤️.*',
        r'build status:.*',
        r'downloads:.*',
        r'version:.*',
        r'npm version.*',
        r'pypi version.*',
        r'license:.*',
        r'coverage:.*',
        r'documentation:.*',
        r'\[view on github\]',
        r'\[⭐️ star us on github\]',
        r'if you (?:find this useful|like this project).*please (?:star|give).*',
    ]
    
    # Repository description tags
    REPO_TAGS = [r'\[WIP\]', r'\[BETA\]', r'\[ALPHA\]', r'\[DEPRECATED\]', r'\[ARCHIVED\]']
    
    def __init__(self, min_length: int = 50, max_length: int = 5000):
        self.min_length = min_length
        self.max_length = max_length
    
    def remove_html_tags(self, text: str) -> str:
        """Remove HTML tags from text."""
        # Remove HTML comments first
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        return text
    
    def remove_code_blocks(self, text: str) -> str:
        """Remove code blocks (``` or indented)."""
        # Remove fenced code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'~~~[\s\S]*?~~~', '', text)
        # Remove inline code
        text = re.sub(r'`[^`\n]+`', '', text)
        return text
    
    def clean_markdown_links(self, text: str) -> str:
        """Keep only link text, remove URLs."""
        # [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # <url> -> remove entirely
        text = re.sub(r'<https?://[^>]+>', '', text)
        # Bare URLs
        text = re.sub(r'https?://\S+', '', text)
        return text
    
    def remove_badges(self, text: str) -> str:
        """Remove badge patterns."""
        for pattern in self.BADGE_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        return text
    
    def remove_sections(self, text: str) -> str:
        """Remove entire sections by header."""
        lines = text.split('\n')
        cleaned_lines = []
        skip_section = False
        
        for line in lines:
            # Check if this is a header we want to remove
            if re.match(r'##?\s+', line):
                skip_section = any(
                    re.search(pattern, line, re.IGNORECASE) 
                    for pattern in self.REMOVE_SECTIONS
                )
            
            # Reset skip on next header if currently skipping
            if skip_section and re.match(r'#\s+', line):
                skip_section = False
            
            if not skip_section:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def remove_boilerplate(self, text: str) -> str:
        """Remove boilerplate marketing phrases."""
        for phrase in self.BOILERPLATE_PHRASES:
            text = re.sub(phrase, '', text, flags=re.IGNORECASE)
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace and newlines."""
        # Replace multiple spaces/tabs with single space
        text = re.sub(r'[ \t]+', ' ', text)
        # Replace multiple newlines with max 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Strip whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        return text.strip()
    
    def clean_description(self, description: str) -> str:
        """Clean repository description."""
        if not description:
            return ""
        
        # Remove tags
        for tag in self.REPO_TAGS:
            description = re.sub(tag, '', description, flags=re.IGNORECASE)
        
        # Remove trailing punctuation (except period)
        description = re.sub(r'[,;:]+$', '', description)
        
        # Normalize whitespace
        description = re.sub(r'\s+', ' ', description).strip()
        
        return description
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract potential keywords from text."""
        keywords = set()
        
        # Quoted text
        quoted = re.findall(r'"([^"]+)"', text)
        keywords.update(quoted)
        
        # Capitalized technical terms (e.g., React, FastAPI)
        cap_terms = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]*)*\b', text)
        keywords.update(cap_terms)
        
        # Hyphenated technical terms (e.g., react-native, machine-learning)
        hyphenated = re.findall(r'\b[a-z]+-[a-z]+(?:-[a-z]+)*\b', text)
        keywords.update(hyphenated)
        
        return list(keywords)
    
    def is_meaningful(self, text: str) -> bool:
        """Check if content has enough meaningful words."""
        if len(text) < self.min_length:
            return False
        
        # Count words (not just whitespace)
        words = re.findall(r'\b\w+\b', text)
        if len(words) < 10:
            return False
        
        # Check for variety (unique words)
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.3:  # Too repetitive
            return False
        
        return True
    
    def clean_readme(self, readme_text: str) -> str:
        """Apply all cleaning steps to README text."""
        if not readme_text:
            return ""
        
        text = readme_text
        
        # Remove unwanted content
        text = self.remove_badges(text)
        text = self.remove_html_tags(text)
        text = self.remove_code_blocks(text)
        text = self.remove_sections(text)
        text = self.remove_boilerplate(text)
        text = self.clean_markdown_links(text)
        
        # Normalize formatting
        text = self.normalize_whitespace(text)
        
        # Truncate if too long
        if len(text) > self.max_length:
            text = text[:self.max_length] + "..."
        
        # Validate meaningfulness
        if not self.is_meaningful(text):
            return ""
        
        return text
    
    def combine_repo_text(self, repo: Dict) -> str:
        """Combine all repo info into coherent text."""
        parts = []
        
        # Add name
        if repo.get('name'):
            parts.append(f"Repository: {repo['name']}")
        
        # Add cleaned description
        if repo.get('description'):
            clean_desc = self.clean_description(repo['description'])
            if clean_desc:
                parts.append(clean_desc)
        
        # Add language
        if repo.get('language'):
            parts.append(f"Primary language: {repo['language']}")
        
        # Add topics
        if repo.get('topics'):
            topics_str = ', '.join(repo['topics'][:10])  # Limit topics
            parts.append(f"Topics: {topics_str}")
        
        # Add cleaned README
        if repo.get('readme'):
            parts.append(repo['readme'])
        
        return '\n\n'.join(parts)


class GitHubReadmeFetcher:
    """Fetch README files from GitHub repositories with concurrent processing."""
    
    def __init__(self, token: Optional[str] = None, rate_limit_delay: float = 0.1):
        self.token = token
        self.rate_limit_delay = rate_limit_delay
        self.lock = threading.Lock()
    
    def create_session(self):
        """Create a new session for each thread."""
        session = requests.Session()
        if self.token:
            session.headers.update({
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json'
            })
        return session
    
    def fetch_readme(self, owner: str, repo: str) -> str:
        """Fetch README content from a repository."""
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        session = self.create_session()
        
        try:
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Content is base64 encoded
                import base64
                content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
                return content
            elif response.status_code == 404:
                return ""
            else:
                return ""
        
        except Exception as e:
            return ""
        
        finally:
            session.close()
            time.sleep(self.rate_limit_delay)
    
    def process_single_repo(self, repo: Dict, index: int, total: int, cleaner: ReadmeCleaner) -> Dict:
        """Process a single repository (fetch and clean README)."""
        owner = repo.get('owner')
        name = repo.get('name')
        
        if not owner or not name:
            with self.lock:
                print(f"[{index}/{total}] Skipping repo with missing owner/name")
            return repo
        
        with self.lock:
            print(f"[{index}/{total}] Fetching README for {owner}/{name}")
        
        # Fetch README
        readme_raw = self.fetch_readme(owner, name)
        
        # Clean README
        readme_cleaned = cleaner.clean_readme(readme_raw)
        
        # Update repo dict
        repo['readme'] = readme_cleaned
        repo['combined_text'] = cleaner.combine_repo_text(repo)
        
        if readme_cleaned:
            repo['extracted_keywords'] = cleaner.extract_key_phrases(readme_cleaned)
        
        return repo
    
    def process_repositories(self, input_file: str, output_file: str, 
                           github_token: Optional[str] = None,
                           max_workers: int = 10):
        """Process all repositories and fetch their READMEs concurrently."""
        
        # Load input data
        print(f"Loading repositories from {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        repositories = data.get('repositories', [])
        print(f"Found {len(repositories)} repositories")
        print(f"Using {max_workers} concurrent workers\n")
        
        # Update token if provided
        if github_token:
            self.token = github_token
        
        # Initialize cleaner
        cleaner = ReadmeCleaner(min_length=50, max_length=5000)
        
        # Process repositories concurrently
        processed_repos = [None] * len(repositories)
        processed_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(
                    self.process_single_repo, 
                    repo.copy(), 
                    i + 1, 
                    len(repositories), 
                    cleaner
                ): i
                for i, repo in enumerate(repositories)
            }
            
            # Process completed tasks
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    processed_repo = future.result()
                    processed_repos[index] = processed_repo
                    processed_count += 1
                    
                    # Save progress periodically
                    if processed_count % 50 == 0:
                        with self.lock:
                            print(f"\n💾 Saving progress... ({processed_count}/{len(repositories)} completed)")
                            data['repositories'] = [r for r in processed_repos if r is not None]
                            with open(output_file, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                            print()
                
                except Exception as e:
                    print(f"Error processing repository at index {index}: {str(e)}")
                    processed_repos[index] = repositories[index]
        
        # Update data with processed repos
        data['repositories'] = processed_repos
        
        # Final save
        print(f"\n{'='*60}")
        print(f"Saving final results to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Completed! Processed {len(repositories)} repositories")
        
        # Print statistics
        with_readme = sum(1 for r in processed_repos if r and r.get('readme'))
        print(f"📊 Repositories with README: {with_readme}/{len(repositories)}")
        print(f"{'='*60}\n")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch and clean GitHub READMEs concurrently')
    parser.add_argument('input_file', help='Input JSON file with repository data')
    parser.add_argument('output_file', help='Output JSON file with cleaned READMEs')
    parser.add_argument('--token', help='GitHub personal access token (optional but recommended)')
    parser.add_argument('--delay', type=float, default=0.1, 
                       help='Delay between API requests in seconds (default: 0.1)')
    parser.add_argument('--workers', type=int, default=10,
                       help='Number of concurrent workers (default: 10)')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input_file).exists():
        print(f"Error: Input file '{args.input_file}' not found!")
        return
    
    # Create fetcher and process
    fetcher = GitHubReadmeFetcher(token=args.token, rate_limit_delay=args.delay)
    fetcher.process_repositories(
        args.input_file, 
        args.output_file, 
        args.token,
        max_workers=args.workers
    )


if __name__ == '__main__':
    main()