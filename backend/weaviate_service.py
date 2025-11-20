import weaviate
from weaviate.classes.init import Auth
from dotenv import load_dotenv
import os
from typing import List, Dict, Any
from light_embed import TextEmbedding

load_dotenv()

class WeaviateService:
    def __init__(self):
        self.model = TextEmbedding('onnx-models/all-MiniLM-L6-v2-onnx')
        self.client = weaviate.connect_to_weaviate_cloud(
            cluster_url="9twbzcqrjcb3u5xymuliq.c0.asia-southeast1.gcp.weaviate.cloud",
            auth_credentials=Auth.api_key(os.getenv('WEAVIATE_API_KEY')),
        )
    
    def execute_search_code(self, generated_code: str, query_text: str) -> List[Dict[str, Any]]:
        """Execute the generated Weaviate code and return formatted results"""
        
        # Set up the execution environment
        exec_globals = {
            'client': self.client,
            'model': self.model,
            'query_text': query_text,
            'results': None
        }
        
        # Execute the generated code
        print(generated_code)
        exec(generated_code, exec_globals)
        
        # Get the results
        results = exec_globals.get('results')
        
        if not results or not hasattr(results, 'objects'):
            return []
        
        # Format results for API response
        formatted_results = []
        for obj in results.objects:
            props = obj.properties
            # Format topics as list instead of comma-separated string
            topics = []
            if props.get('topics'):
                topics = [topic.strip() for topic in props['topics'].split(',') if topic.strip()]
            
            # Format languages as list if it exists
            languages = []
            if props.get('languages'):
                languages = [lang.strip() for lang in props['languages'].split(',') if lang.strip()]
            
            result_item = {
                'name': props.get('name', ''),
                'full_name': props.get('full_name', ''),
                'description': props.get('description', ''),
                'url': props.get('url', ''),
                'homepage': props.get('homepage', ''),
                'language': props.get('language', ''),
                'languages': languages,
                'topics': topics,
                'stars': props.get('stars', 0),
                'forks': props.get('forks', 0),
                'open_issues': props.get('open_issues', 0),
                'license': props.get('license', ''),
                'has_issues': props.get('has_issues', False),
                'has_wiki': props.get('has_wiki', False),
                'created_at': props.get('created_at', ''),
                'updated_at': props.get('updated_at', '')
            }
            
            # Add search metadata if available
            if hasattr(obj.metadata, 'distance') and obj.metadata.distance is not None:
                result_item['distance'] = round(obj.metadata.distance, 4)
            elif hasattr(obj.metadata, 'score') and obj.metadata.score is not None:
                result_item['score'] = round(obj.metadata.score, 4)
            
            formatted_results.append(result_item)
        
        return formatted_results
    
    def search(self, query: str, generated_code: str) -> Dict[str, Any]:
        """Main search method that coordinates the search process"""
        try:
            results = self.execute_search_code(generated_code, query)
            
            return {
                'success': True,
                'query': query,
                'results_count': len(results),
                'results': results,
                'generated_code': generated_code  # Include for debugging
            }
            
        except Exception as e:
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'results_count': 0,
                'results': [],
                'generated_code': generated_code
            }
    
    def close(self):
        """Close the Weaviate client connection"""
        if self.client:
            self.client.close()
