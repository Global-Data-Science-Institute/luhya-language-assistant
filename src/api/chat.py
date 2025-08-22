# api/chat.py - Vercel serverless function for chat
import json
import os
import pickle
import re
import random
from typing import List, Dict, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class LuhyaRAGSystem:
    def __init__(self):
        self.vectorizer = None
        self.tfidf_matrix = None
        self.documents = []
        self.metadata = []
        self.is_initialized = False
        
        # Conversation patterns for human-like responses
        self.conversation_patterns = {
            'greeting_starters': [
                "Here's what I found: ",
                "Great question! ",
                "I can help with that! ",
                ""
            ],
            'enthusiasm_words': [
                "Beautiful!", "Wonderful!", "Perfect!",
                "That's a great question!", "Fascinating!"
            ]
        }
    
    def load_data_from_env(self):
        """Load preprocessed data from environment variables or external storage"""
        if self.is_initialized:
            return True
            
        try:
            # In production, you'd load from external storage (S3, Supabase, etc.)
            # For now, we'll use a simplified approach with HuggingFace dataset
            from datasets import load_dataset
            
            print("Loading Luhya dataset...")
            dataset = load_dataset("mamakobe/luhya-multilingual-dataset")
            
            # Process the dataset
            documents = []
            metadata = []
            
            # Combine all splits
            all_data = []
            for split_name in dataset.keys():
                split_data = dataset[split_name].to_pandas()
                all_data.append(split_data)
            
            import pandas as pd
            df = pd.concat(all_data, ignore_index=True)
            
            # Create documents for TF-IDF
            for idx, row in df.iterrows():
                if pd.notna(row['source_text']) and pd.notna(row['target_text']):
                    # Create bidirectional entries
                    content = f"Translation: {row['source_text']} → {row['target_text']} Dialect: {row.get('dialect', 'General')} Domain: {row.get('domain', 'general')}"
                    
                    documents.append(content)
                    metadata.append({
                        'type': 'translation',
                        'source_text': row['source_text'],
                        'target_text': row['target_text'],
                        'source_lang': row.get('source_lang', 'unknown'),
                        'target_lang': row.get('target_lang', 'unknown'),
                        'dialect': row.get('dialect', 'General'),
                        'domain': row.get('domain', 'general'),
                        'id': f"trans_{idx}"
                    })
            
            print(f"Processed {len(documents)} documents")
            
            # Build TF-IDF matrix
            self.vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=5000,  # Reduced for Vercel memory limits
                ngram_range=(1, 3),
                min_df=1,
                max_df=0.95
            )
            
            self.tfidf_matrix = self.vectorizer.fit_transform(documents)
            self.documents = documents
            self.metadata = metadata
            self.is_initialized = True
            
            print("TF-IDF system initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def detect_query_intent(self, query: str) -> Dict:
        """Detect user intent from query"""
        query_lower = query.lower().strip()
        
        intent_data = {
            'primary_intent': 'general',
            'key_terms': [],
            'response_style': 'conversational'
        }
        
        # Translation request patterns
        translation_patterns = [
            r'what (?:is|does|means?) ([^?]+?) in luhya(?:\?|$)',
            r'how (?:do you say|to say) ([^?]+?) in luhya(?:\?|$)',
            r'luhya (?:word|translation) for ([^?]+?)(?:\?|$)',
            r'translate ([^?]+?) (?:to|into) luhya(?:\?|$)',
            r'say ([^?]+?) in luhya(?:\?|$)'
        ]
        
        # Dictionary lookup patterns
        dictionary_patterns = [
            r'what (?:is|does|means?) ([a-zA-Z]+)(?:\?|$)',
            r'(?:meaning of|define) ([^?]+?)(?:\?|$)',
            r'what does ([^?]+?) mean(?:\?|$)'
        ]
        
        # Check translation patterns first
        for pattern in translation_patterns:
            match = re.search(pattern, query_lower)
            if match:
                intent_data['primary_intent'] = 'translation_request'
                intent_data['key_terms'] = [match.group(1).strip()]
                break
        
        # Check dictionary patterns
        if intent_data['primary_intent'] == 'general':
            for pattern in dictionary_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    intent_data['primary_intent'] = 'dictionary_lookup'
                    intent_data['key_terms'] = [match.group(1).strip()]
                    break
        
        # Extract key terms if not found
        if not intent_data['key_terms']:
            common_words = {'what', 'is', 'the', 'how', 'do', 'you', 'say', 'in', 'luhya', 'about'}
            words = [word for word in query_lower.split() if word not in common_words and len(word) > 2]
            intent_data['key_terms'] = words[:3]
        
        return intent_data
    
    def search_corpus(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search corpus using TF-IDF"""
        if not self.is_initialized:
            if not self.load_data_from_env():
                return []
        
        # Get intent analysis
        intent_data = self.detect_query_intent(query)
        
        # Direct term search
        direct_results = self.direct_term_search(intent_data['key_terms'])
        
        # Semantic TF-IDF search
        semantic_results = self.semantic_search(query, max_results)
        
        # Combine and deduplicate
        all_results = direct_results + semantic_results
        
        # Remove duplicates and sort by score
        seen_ids = set()
        unique_results = []
        
        for result in sorted(all_results, key=lambda x: x.get('similarity', 0), reverse=True):
            result_id = result['metadata'].get('id', '')
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
            
            if len(unique_results) >= max_results:
                break
        
        return unique_results
    
    def direct_term_search(self, key_terms: List[str]) -> List[Dict]:
        """Direct search for terms in translations"""
        results = []
        
        for term in key_terms:
            term_lower = term.lower().strip()
            if len(term_lower) < 2:
                continue
            
            for i, metadata in enumerate(self.metadata):
                source_text = metadata.get('source_text', '').lower()
                target_text = metadata.get('target_text', '').lower()
                
                score = 0
                
                # Exact matches get highest score
                if term_lower == source_text or term_lower == target_text:
                    score = 1.0
                elif term_lower in source_text or term_lower in target_text:
                    score = 0.8
                elif any(word in source_text or word in target_text for word in term_lower.split()):
                    score = 0.6
                
                if score > 0:
                    results.append({
                        'content': self.documents[i],
                        'metadata': metadata,
                        'similarity': score,
                        'match_reason': f'Direct match for "{term}"'
                    })
        
        return results
    
    def semantic_search(self, query: str, max_results: int) -> List[Dict]:
        """Semantic search using TF-IDF"""
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        results = []
        for idx, similarity in enumerate(similarities):
            if similarity > 0.1:
                results.append({
                    'content': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'similarity': float(similarity),
                    'match_reason': f'Semantic similarity: {similarity:.2%}'
                })
        
        return sorted(results, key=lambda x: x['similarity'], reverse=True)[:max_results]
    
    def generate_response(self, query: str, results: List[Dict], intent_data: Dict) -> str:
        """Generate human-like response"""
        if not results:
            return self.generate_no_results_response(query, intent_data)
        
        response_parts = []
        
        # Add conversational starter
        starter = random.choice(self.conversation_patterns['greeting_starters'])
        if starter:
            response_parts.append(starter)
        
        # Generate main content based on intent
        if intent_data['primary_intent'] in ['translation_request', 'dictionary_lookup']:
            main_content = self.format_translation_response(query, results, intent_data)
        else:
            main_content = self.format_general_response(query, results)
        
        response_parts.append(main_content)
        
        return "".join(response_parts)
    
    def format_translation_response(self, query: str, results: List[Dict], intent_data: Dict) -> str:
        """Format translation response"""
        response_parts = []
        
        # Extract the term being asked about
        query_term = intent_data['key_terms'][0] if intent_data['key_terms'] else ""
        
        # Group results by type
        translation_results = [r for r in results if r['metadata'].get('type') == 'translation']
        
        if translation_results:
            if query_term:
                response_parts.append(f'To say "{query_term}" in Luhya:\n\n')
            
            # Show top translations
            for i, result in enumerate(translation_results[:5]):
                meta = result['metadata']
                source = meta.get('source_text', '')
                target = meta.get('target_text', '')
                dialect = meta.get('dialect', 'General')
                
                if intent_data['primary_intent'] == 'translation_request':
                    # English to Luhya
                    if source.lower() == query_term.lower():
                        response_parts.append(f"**{target}** ({dialect} dialect)\n")
                else:
                    # Luhya to English or general lookup
                    response_parts.append(f"**{source}** → **{target}** ({dialect})\n")
            
            if len(translation_results) > 1:
                response_parts.append(f"\nFound {len(translation_results)} translations across different dialects.")
        
        else:
            response_parts.append(f'I couldn\'t find a translation for "{query_term}" in my Luhya database.')
            response_parts.append('\n\nTry being more specific, like "How do you say \'thank you\' in Luhya?"')
        
        return "".join(response_parts)
    
    def format_general_response(self, query: str, results: List[Dict]) -> str:
        """Format general response"""
        response_parts = []
        
        # Show top results
        for i, result in enumerate(results[:3]):
            meta = result['metadata']
            source = meta.get('source_text', '')
            target = meta.get('target_text', '')
            dialect = meta.get('dialect', 'General')
            
            response_parts.append(f"**{i+1}.** {source} → {target} ({dialect})\n")
        
        if len(results) > 3:
            response_parts.append(f"\n...and {len(results) - 3} more results found.")
        
        return "".join(response_parts)
    
    def generate_no_results_response(self, query: str, intent_data: Dict) -> str:
        """Generate helpful response when no results found"""
        return """I couldn't find specific information about that in my Luhya database.

Here are some things I can help with:
• **Translations**: "How do you say 'hello' in Luhya?"
• **Dictionary lookups**: "What does 'muraho' mean?"
• **Common phrases**: Ask about greetings, family terms, or everyday words

Try being more specific or use simpler terms!"""

# Initialize the RAG system
rag_system = LuhyaRAGSystem()

def handler(request):
    """Vercel serverless function handler"""
    try:
        # Parse request
        if request.method != 'POST':
            return {
                'statusCode': 405,
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        body = json.loads(request.body)
        message = body.get('message', '')
        max_results = body.get('max_results', 5)
        
        if not message:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Message is required'})
            }
        
        # Get intent analysis
        intent_data = rag_system.detect_query_intent(message)
        
        # Search for relevant content
        results = rag_system.search_corpus(message, max_results)
        
        # Generate response
        response = rag_system.generate_response(message, results, intent_data)
        
        # Format sources for frontend
        sources = [
            {
                'text': result['metadata'].get('source_text', '')[:100] + '...',
                'metadata': {
                    'type': result['metadata'].get('domain', 'translation'),
                    'dialect': result['metadata'].get('dialect', 'General'),
                    'confidence': result.get('similarity', 0)
                }
            }
            for result in results[:3]
        ]
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'response': response,
                'sources': sources
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
