#!/usr/bin/env python3
"""
MongoDB Index Creation Script for FindMyRepo
Run this script to automatically create all necessary indexes
"""

import os
import sys
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_indexes():
    """Create all necessary MongoDB indexes"""
    
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("❌ Error: MONGO_URI not found in environment variables")
        print("Make sure you have a .env file with MONGO_URI set")
        sys.exit(1)
    
    print("🔌 Connecting to MongoDB...")
    
    try:
        client = MongoClient(mongo_uri)
        db = client["findmyrepo"]
        collection = db["repos"]
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")
        
        # Get existing indexes
        existing_indexes = collection.index_information()
        print(f"\n📊 Current indexes: {len(existing_indexes)}")
        for idx_name in existing_indexes.keys():
            print(f"   - {idx_name}")
        
        print("\n🔨 Creating indexes...")
        
        # 1. Compound index for sorting by stars and date
        print("\n1️⃣  Creating compound index: stars + pushed_at")
        try:
            collection.create_index(
                [("stars", DESCENDING), ("pushed_at", DESCENDING)],
                name="stars_pushed_at_idx"
            )
            print("   ✅ Created stars_pushed_at_idx")
        except Exception as e:
            print(f"   ⚠️  Index may already exist or error: {e}")
        
        # 2. Language array index
        print("\n2️⃣  Creating index: languages")
        try:
            collection.create_index(
                [("languages", ASCENDING)],
                name="languages_idx"
            )
            print("   ✅ Created languages_idx")
        except Exception as e:
            print(f"   ⚠️  Index may already exist or error: {e}")
        
        # 3. Topics array index
        print("\n3️⃣  Creating index: topics")
        try:
            collection.create_index(
                [("topics", ASCENDING)],
                name="topics_idx"
            )
            print("   ✅ Created topics_idx")
        except Exception as e:
            print(f"   ⚠️  Index may already exist or error: {e}")
        
        # 4. Pushed_at index for recency filtering
        print("\n4️⃣  Creating index: pushed_at")
        try:
            collection.create_index(
                [("pushed_at", DESCENDING)],
                name="pushed_at_idx"
            )
            print("   ✅ Created pushed_at_idx")
        except Exception as e:
            print(f"   ⚠️  Index may already exist or error: {e}")
        
        # 5. Stars index for sorting
        print("\n5️⃣  Creating index: stars")
        try:
            collection.create_index(
                [("stars", DESCENDING)],
                name="stars_idx"
            )
            print("   ✅ Created stars_idx")
        except Exception as e:
            print(f"   ⚠️  Index may already exist or error: {e}")
        
        # 6. Unique index on github_id
        print("\n6️⃣  Creating unique index: github_id")
        try:
            collection.create_index(
                [("github_id", ASCENDING)],
                name="github_id_unique_idx",
                unique=True
            )
            print("   ✅ Created github_id_unique_idx")
        except Exception as e:
            print(f"   ⚠️  Index may already exist or error: {e}")
        
        # 7. Compound index for hidden gems
        print("\n7️⃣  Creating compound index: stars + pushed_at + readme (for hidden gems)")
        try:
            collection.create_index(
                [("stars", ASCENDING), ("pushed_at", DESCENDING), ("readme", ASCENDING)],
                name="hidden_gems_idx"
            )
            print("   ✅ Created hidden_gems_idx")
        except Exception as e:
            print(f"   ⚠️  Index may already exist or error: {e}")
        
        # 8. Name index for searching
        print("\n8️⃣  Creating index: name")
        try:
            collection.create_index(
                [("name", ASCENDING)],
                name="name_idx"
            )
            print("   ✅ Created name_idx")
        except Exception as e:
            print(f"   ⚠️  Index may already exist or error: {e}")
        
        # 9. Description index for searching
        print("\n9️⃣  Creating index: description")
        try:
            collection.create_index(
                [("description", ASCENDING)],
                name="description_idx"
            )
            print("   ✅ Created description_idx")
        except Exception as e:
            print(f"   ⚠️  Index may already exist or error: {e}")
        
        print("\n" + "="*60)
        print("✅ Index creation complete!")
        print("="*60)
        
        # List all indexes
        updated_indexes = collection.index_information()
        print(f"\n📊 Total indexes after creation: {len(updated_indexes)}")
        for idx_name, idx_info in updated_indexes.items():
            print(f"   - {idx_name}: {idx_info.get('key', [])}")
        
        print("\n⚠️  IMPORTANT: Vector Search Index")
        print("="*60)
        print("The vector search index must be created manually in MongoDB Atlas:")
        print("\n1. Go to MongoDB Atlas → Your Cluster → Search")
        print("2. Click 'Create Search Index'")
        print("3. Choose 'JSON Editor'")
        print("4. Index Name: vector_index")
        print("5. Database: findmyrepo")
        print("6. Collection: repos")
        print("\n7. Paste this JSON definition:")
        print("""
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 384,
      "similarity": "cosine"
    }
  ]
}
        """)
        print("8. Click 'Create Search Index'")
        print("="*60)
        
        # Get collection stats
        print("\n📈 Collection Statistics:")
        stats = db.command("collstats", "repos")
        print(f"   Total documents: {stats.get('count', 'N/A')}")
        print(f"   Total size: {stats.get('size', 0) / (1024*1024):.2f} MB")
        print(f"   Average document size: {stats.get('avgObjSize', 0) / 1024:.2f} KB")
        
        client.close()
        print("\n✅ Done! Your MongoDB is now optimized for FindMyRepo")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPossible solutions:")
        print("1. Check your MONGO_URI in .env file")
        print("2. Verify network access in MongoDB Atlas")
        print("3. Ensure you have write permissions on the database")
        sys.exit(1)

def main():
    print("="*60)
    print("  MongoDB Index Creation for FindMyRepo")
    print("="*60)
    print("\nThis script will create the following indexes:")
    print("  • Compound indexes for efficient sorting")
    print("  • Single-field indexes for filtering")
    print("  • Unique index for data integrity")
    print("\n⏱️  Estimated time: 1-2 minutes")
    
    response = input("\nDo you want to proceed? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        sys.exit(0)
    
    create_indexes()

if __name__ == "__main__":
    main()