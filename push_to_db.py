import json
from sentence_transformers import SentenceTransformer
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from tqdm import tqdm
import os
from weaviate.classes.init import Auth
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🚀 Loading repos data...")
    with open('github_repos_enriched_final_main.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    repos = data['repositories']
    print(f"📦 Loaded {len(repos)} repos")

    # Load embedding model
    print("🤖 Loading Sentence Transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model loaded!")

    # Initialize Weaviate
    print("💾 Initializing Weaviate...")
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=os.getenv('WEAVIATE_URL'),
        auth_credentials=Auth.api_key(os.getenv('WEAVIATE_API_KEY')),
    )

    try:
        client.collections.delete("Repos")
        print("🗑️  Deleted existing collection")
    except:
        pass

    # Create collection with updated schema
    print("📋 Creating collection schema...")
    collection = client.collections.create(
        name="Repos",
        properties=[
            Property(name="repo_id", data_type=DataType.INT),
            Property(name="name", data_type=DataType.TEXT),
            Property(name="full_name", data_type=DataType.TEXT),
            Property(name="owner", data_type=DataType.TEXT),
            Property(name="url", data_type=DataType.TEXT),
            Property(name="homepage", data_type=DataType.TEXT),
            Property(name="description", data_type=DataType.TEXT),
            Property(name="readme", data_type=DataType.TEXT),
            Property(name="language", data_type=DataType.TEXT),
            Property(name="languages", data_type=DataType.TEXT),
            Property(name="topics", data_type=DataType.TEXT),
            Property(name="stars", data_type=DataType.INT),
            Property(name="forks", data_type=DataType.INT),
            Property(name="open_issues", data_type=DataType.INT),
            Property(name="created_at", data_type=DataType.TEXT),
            Property(name="updated_at", data_type=DataType.TEXT),
            Property(name="license", data_type=DataType.TEXT),
            Property(name="has_issues", data_type=DataType.BOOL),
            Property(name="has_wiki", data_type=DataType.BOOL),
            Property(name="default_branch", data_type=DataType.TEXT),
            Property(name="is_gsoc", data_type=DataType.BOOL),
            Property(name="is_hacktoberfest", data_type=DataType.BOOL),
            Property(name="is_underrated", data_type=DataType.BOOL),
            Property(name="has_good_first_issues", data_type=DataType.BOOL),
            Property(name="sources", data_type=DataType.TEXT),
            Property(name="combined_text", data_type=DataType.TEXT),
        ],
        vectorizer_config=Configure.Vectorizer.none(),
    )

    # Insert repos in batches
    print("🔄 Creating embeddings and storing...")
    batch_size = 100
    for i in tqdm(range(0, len(repos), batch_size), desc="Processing"):
        batch = repos[i:i+batch_size]
        texts = [repo.get('combined_text', '') for repo in batch]

        embeddings = model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        with collection.batch.dynamic() as batch_insert:
            for repo, embedding in zip(batch, embeddings):
                properties = {
                    'repo_id': int(repo.get('id', 0)),
                    'name': repo.get('name', ''),
                    'full_name': repo.get('full_name', ''),
                    'owner': repo.get('owner', ''),
                    'url': repo.get('url', ''),
                    'homepage': repo.get('homepage', ''),
                    'description': repo.get('description', '')[:500],
                    'readme': repo.get('readme', '')[:2000],
                    'language': str(repo.get('language', '')).lower(),
                    'languages': ','.join([lang.lower() for lang in (repo.get('languages') or [])]),
                    'topics': ','.join(repo.get('topics') or []),
                    'stars': int(repo.get('stars', 0)),
                    'forks': int(repo.get('forks', 0)),
                    'open_issues': int(repo.get('open_issues', 0)),
                    'created_at': repo.get('created_at', ''),
                    'updated_at': repo.get('updated_at', ''),
                    'license': repo.get('license', ''),
                    'has_issues': bool(repo.get('has_issues', False)),
                    'has_wiki': bool(repo.get('has_wiki', False)),
                    'default_branch': repo.get('default_branch', ''),
                    'is_gsoc': bool(repo.get('is_gsoc', False)),
                    'is_hacktoberfest': bool(repo.get('is_hacktoberfest', False)),
                    'is_underrated': bool(repo.get('is_underrated', False)),
                    'has_good_first_issues': bool(repo.get('has_good_first_issues', False)),
                    'sources': ','.join(repo.get('sources', [])),
                    'combined_text': repo.get('combined_text', ''),
                }

                batch_insert.add_object(
                    properties=properties,
                    vector=embedding.tolist()
                )

    print(f"\n✅ Successfully stored {len(repos)} repos!")

    # Test search
    print("\n🔍 Testing search...")
    test_query = "Python machine learning library"
    query_embedding = model.encode([test_query])[0]

    response = collection.query.near_vector(
        near_vector=query_embedding.tolist(),
        limit=5,
        return_properties=["name", "description", "stars"]
    )

    print(f"\nTest query: '{test_query}'")
    print("\nTop 5 results:")
    for i, obj in enumerate(response.objects):
        print(f"{i+1}. {obj.properties['name']} - {obj.properties['description'][:100]}")

    client.close()
    print("\n🎉 Setup complete! Ready for hackathon!")

if __name__ == "__main__":
    main()
