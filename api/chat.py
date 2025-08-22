# api/chat.py - Memory-efficient Python version
from http.server import BaseHTTPRequestHandler
import json
import re
import urllib.request
import csv
from io import StringIO

class LuhyaRAG:
    def __init__(self):
        self.dataset = None
        self.loaded = False
    
    def load_dataset(self):
        """Load dataset with memory efficiency"""
        if self.loaded:
            return True
        
        try:
            print("Loading Luhya dataset...")
            url = "https://huggingface.co/datasets/mamakobe/luhya-multilingual-dataset/resolve/main/train.csv"
            
            with urllib.request.urlopen(url) as response:
                csv_data = response.read().decode('utf-8')
            
            # Parse CSV efficiently
            csv_reader = csv.DictReader(StringIO(csv_data))
            self.dataset = []
            
            for i, row in enumerate(csv_reader):
                if i > 5000:  # Limit to first 5000 for memory efficiency
                    break
                    
                if row.get('source_text') and row.get('target_text'):
                    self.dataset.append({
                        'source_text': row['source_text'].strip(),
                        'target_text': row['target_text'].strip(),
                        'source_lang': row.get('source_lang', '').strip(),
                        'target_lang': row.get('target_lang', '').strip(),
                        'dialect': row.get('dialect', 'General').strip(),
                        'domain': row.get('domain', 'general').strip()
                    })
            
            print(f"Loaded {len(self.dataset)} translations")
            self.loaded = True
            return True
            
        except Exception as e:
            print(f"Error loading dataset: {e}")
            # Fallback to demo data
            self.dataset = [
                {'source_text': 'good morning', 'target_text': 'bwakhera', 'dialect': 'Bukusu', 'domain': 'greetings'},
                {'source_text': 'hello', 'target_text': 'muraho', 'dialect': 'General', 'domain': 'greetings'},
                {'source_text': 'thank you', 'target_text': 'webale', 'dialect': 'Wanga', 'domain': 'courtesy'},
                {'source_text': 'water', 'target_text': 'amatsi', 'dialect': 'General', 'domain': 'nouns'},
                {'source_text': 'goodbye', 'target_text': 'khwilindila', 'dialect': 'General', 'domain': 'greetings'}
            ]
            self.loaded = True
            return False
    
    def detect_intent(self, query):
        """Detect user intent"""
        query_lower = query.lower().strip()
        
        # Translation patterns
        translation_patterns = [
            r'what (?:is|does|means?) (.+?) in luhya',
            r'how (?:do you say|to say) (.+?) in luhya',
            r'luhya (?:word|translation) for (.+?)$',
            r'translate (.+?) (?:to|into) luhya',
            r'say (.+?) in luhya'
        ]
        
        # Dictionary patterns
        dictionary_patterns = [
            r'what (?:is|does|means?) ([a-zA-Z]+)$',
            r'(?:meaning of|define) (.+?)$',
            r'what does (.+?) mean'
        ]
        
        # Check translation patterns
        for pattern in translation_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return {
                    'type': 'translation_request',
                    'term': match.group(1).strip(),
                    'confidence': 0.9
                }
        
        # Check dictionary patterns
        for pattern in dictionary_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return {
                    'type': 'dictionary_lookup',
                    'term': match.group(1).strip(),
                    'confidence': 0.8
                }
        
        return {
            'type': 'general',
            'term': query_lower,
            'confidence': 0.5
        }
    
    def search_dataset(self, query, intent, limit=10):
        """Memory-efficient search"""
        if not self.dataset:
            return []
        
        results = []
        search_term = intent['term'].lower()
        
        # Direct search - more efficient than TF-IDF
        for item in self.dataset:
            source_lower = item['source_text'].lower()
            target_lower = item['target_text'].lower()
            
            score = 0
            
            # Exact matches
            if source_lower == search_term or target_lower == search_term:
                score = 1.0
            # Substring matches
            elif search_term in source_lower or search_term in target_lower:
                score = 0.8
            # Word matches
            elif any(word == search_term for word in source_lower.split()) or \
                 any(word == search_term for word in target_lower.split()):
                score = 0.7
            # Partial word matches
            elif any(search_term in word for word in source_lower.split()) or \
                 any(search_term in word for word in target_lower.split()):
                score = 0.5
            
            if score > 0:
                results.append({
                    'content': f"{item['source_text']} → {item['target_text']}",
                    'metadata': item,
                    'similarity': score
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
    
    def generate_response(self, query, results, intent):
        """Generate response based on results"""
        if not results:
            return self.generate_no_results_response(query, intent)
        
        if intent['type'] == 'translation_request':
            return self.format_translation_response(results, intent)
        elif intent['type'] == 'dictionary_lookup':
            return self.format_dictionary_response(results, intent)
        else:
            return self.format_general_response(results)
    
    def format_translation_response(self, results, intent):
        """Format translation response"""
        response_parts = []
        term = intent['term']
        
        # Group by dialect
        by_dialect = {}
        for result in results[:5]:
            dialect = result['metadata']['dialect'] or 'General'
            if dialect not in by_dialect:
                by_dialect[dialect] = []
            by_dialect[dialect].append(result)
        
        response_parts.append(f"To say \"{term}\" in Luhya:\n")
        
        for dialect, dialect_results in by_dialect.items():
            for result in dialect_results[:1]:  # One per dialect
                meta = result['metadata']
                # Show the Luhya translation
                if meta['source_text'].lower() == term.lower():
                    response_parts.append(f"**{meta['target_text']}** ({dialect} dialect)")
                elif meta['target_text'].lower() == term.lower():
                    response_parts.append(f"**{meta['source_text']}** ({dialect} dialect)")
        
        if len(by_dialect) > 1:
            response_parts.append(f"\nFound in {len(by_dialect)} dialects.")
        
        return "\n".join(response_parts)
    
    def format_dictionary_response(self, results, intent):
        """Format dictionary response"""
        response_parts = []
        
        for i, result in enumerate(results[:3]):
            meta = result['metadata']
            response_parts.append(
                f"**{i+1}.** {meta['source_text']} → {meta['target_text']} ({meta['dialect']} dialect)"
            )
        
        return "\n".join(response_parts)
    
    def format_general_response(self, results):
        """Format general response"""
        response_parts = []
        
        for result in results[:5]:
            meta = result['metadata']
            response_parts.append(
                f"**{meta['source_text']}** → **{meta['target_text']}** ({meta['dialect']})"
            )
        
        return "\n".join(response_parts)
    
    def generate_no_results_response(self, query, intent):
        """Generate no results response"""
        term = intent.get('term', query)
        return f"""I couldn't find "{term}" in my Luhya database.

Try asking about common words like:
- "How do you say 'hello' in Luhya?"
- "What does 'muraho' mean?"  
- "Luhya word for water"

Or search for greetings, family terms, or everyday phrases."""

# Global instance
rag = LuhyaRAG()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Load dataset if needed
            rag.load_dataset()
            
            # Parse request
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            message = data.get('message', '')
            if not message:
                self.send_error_response({'error': 'Message is required'}, 400)
                return
            
            # Process query
            intent = rag.detect_intent(message)
            results = rag.search_dataset(message, intent, 10)
            response_text = rag.generate_response(message, results, intent)
            
            # Format sources
            sources = [
                {
                    'text': f"{r['metadata']['source_text']} → {r['metadata']['target_text']}",
                    'metadata': {
                        'type': r['metadata']['domain'],
                        'dialect': r['metadata']['dialect'],
                        'confidence': r['similarity']
                    }
                }
                for r in results[:3]
            ]
            
            self.send_json_response({
                'response': response_text,
                'sources': sources
            })
            
        except Exception as e:
            print(f"Error: {e}")
            self.send_error_response({
                'error': 'Internal server error',
                'message': str(e)
            }, 500)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_cors_headers() 
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def send_error_response(self, data, status_code):
        self.send_response(status_code)
        self.send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')