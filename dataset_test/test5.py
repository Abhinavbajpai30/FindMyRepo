import json
import sys
from typing import Dict, List

def load_json_file(filepath: str) -> dict:
    """Load and parse a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{filepath}': {e}")
        sys.exit(1)

def merge_repositories(file1_data: dict, file2_data: dict) -> dict:
    """
    Merge repositories from two files, combining readme content.
    If readme is empty in one file but has content in another, use the non-empty one.
    """
    # Create a dictionary to store repos by their unique identifier
    repos_dict: Dict[str, dict] = {}
    
    # Process repositories from first file
    for repo in file1_data.get('repositories', []):
        repo_id = repo.get('id')
        if repo_id:
            repos_dict[repo_id] = repo.copy()
    
    # Process repositories from second file
    for repo in file2_data.get('repositories', []):
        repo_id = repo.get('id')
        if not repo_id:
            continue
            
        if repo_id in repos_dict:
            # Repo exists in both files - merge readme
            existing_readme = repos_dict[repo_id].get('readme', '').strip()
            new_readme = repo.get('readme', '').strip()
            
            # Use non-empty readme, prefer new one if both are non-empty
            if new_readme:
                repos_dict[repo_id]['readme'] = new_readme
            elif not existing_readme:
                repos_dict[repo_id]['readme'] = ''
            
            # Merge sources if they exist
            existing_sources = set(repos_dict[repo_id].get('sources', []))
            new_sources = set(repo.get('sources', []))
            repos_dict[repo_id]['sources'] = list(existing_sources | new_sources)
        else:
            # New repo from second file
            repos_dict[repo_id] = repo.copy()
    
    # Create merged result
    merged_data = {
        'metadata': file1_data.get('metadata', {}),
        'repositories': list(repos_dict.values())
    }
    
    # Update total repos count in metadata
    merged_data['metadata']['total_repos'] = len(merged_data['repositories'])
    merged_data['metadata']['merged_from_files'] = True
    
    return merged_data

def main():
    """Main function to merge repository JSON files."""
    # Get file paths from command line arguments
    if len(sys.argv) < 3:
        print("Usage: python merge_repos.py <file1.json> <file2.json> [output.json]")
        print("Example: python merge_repos.py repos1.json repos2.json merged_repos.json")
        sys.exit(1)
    
    file1_path = sys.argv[1]
    file2_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else 'merged_repositories.json'
    
    print(f"Loading {file1_path}...")
    file1_data = load_json_file(file1_path)
    
    print(f"Loading {file2_path}...")
    file2_data = load_json_file(file2_path)
    
    print("Merging repositories...")
    merged_data = merge_repositories(file1_data, file2_data)
    
    # Count repos with and without readmes
    repos_with_readme = sum(1 for r in merged_data['repositories'] if r.get('readme', '').strip())
    total_repos = len(merged_data['repositories'])
    
    print(f"\nMerge complete!")
    print(f"Total repositories: {total_repos}")
    print(f"Repositories with README: {repos_with_readme}")
    print(f"Repositories without README: {total_repos - repos_with_readme}")
    
    # Write merged data to output file
    print(f"\nWriting to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully saved merged data to {output_path}")

if __name__ == "__main__":
    main()