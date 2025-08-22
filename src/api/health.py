# api/health.py - Health check endpoint
import json
from datetime import datetime

def handler(request):
    """Health check endpoint for Vercel deployment"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'Luhya RAG Chatbot',
            'version': '1.0.0',
            'cost': '$0.00',
            'search_method': 'TF-IDF (Zero Cost)',
            'features': [
                'Intent Detection',
                'Multi-Dialect Support', 
                'Conversational Responses',
                'Direct Term Search',
                'Semantic Search'
            ]
        })
    }