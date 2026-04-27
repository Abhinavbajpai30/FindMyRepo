import os
from pymongo import MongoClient
from pymongo.collection import Collection
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Database:
    """MongoDB Database Connection Manager"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection: Optional[Collection] = None
        
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                raise ValueError("MONGO_URI not found in environment variables")
            
            self.client = MongoClient(mongo_uri)
            self.db = self.client["findmyrepo"]
            self.collection = self.db["repos"]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            return self
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def get_collection(self) -> Collection:
        """Get the repos collection"""
        if self.collection is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.collection

# Global database instance
db_instance = Database()

def get_database() -> Database:
    """Dependency function to get database instance"""
    return db_instance