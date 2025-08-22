# api/chat.py - Production Vercel serverless function with JSON dataset
import json
import os
import re
import random
from typing import List, Dict, Optional
from urllib.request import urlopen
from urllib.error import URLError

class LuhyaRAGSystem:
    def __init__(self):
        self.is_initialized = False
        self.documents = []
        self.metadata = []
        self.dialect_index = {}
        self.domain_index = {}
        self.lang_pair_index = {}
        
        # URL to  processed dataset (JSON format)
        self.dataset_url = "https://raw.githubusercontent.com/Global-Data-Science-Institute/luhya-language-assistant/refs/heads/main/data/luhya_dataset.json"
        
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
    
    def load_dataset_from_url(self, url: str, timeout: int = 10) -> bool:
        """Load dataset from URL with timeout"""
        try:
            print(f"Loading dataset from {url}...")
            with urlopen(url, timeout=timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            print(f"Loaded {len(data)} entries from dataset")
            return self.process_dataset(data)
            
        except (URLError, json.JSONDecodeError, Exception) as e:
            print(f"Failed to load from URL: {e}")
            return False
    
    def load_dataset_from_env(self) -> bool:
        """Load dataset from environment variable (base64 encoded JSON)"""
        try:
            import base64
            
            dataset_b64 = os.environ.get('LUHYA_DATASET_B64')
            if not dataset_b64:
                return False
            
            # Decode base64 and parse JSON
            dataset_json = base64.b64decode(dataset_b64).decode('utf-8')
            data = json.loads(dataset_json)
            
            print(f"Loaded {len(data)} entries from environment")
            return self.process_dataset(data)
            
        except Exception as e:
            print(f"Failed to load from environment: {e}")
            return False
    
    def load_fallback_data(self) -> bool:
        """Load basic fallback data if external sources fail"""
        fallback_data = [
            {"source_text": "good morning", "target_text": "bulamasawa", "dialect": "Bukusu", "domain": "greetings", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "good morning", "target_text": "bushiangala", "dialect": "Maragoli", "domain": "greetings", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "thank you", "target_text": "nyasaye akurinde", "dialect": "Bukusu", "domain": "courtesy", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "thank you", "target_text": "nyasaye akurunde", "dialect": "Maragoli", "domain": "courtesy", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "thank you", "target_text": "nyasayene", "dialect": "Bukusu", "domain": "courtesy", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "how are you", "target_text": "oli otia", "dialect": "Bukusu", "domain": "greetings", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "how are you", "target_text": "uli wahi", "dialect": "Maragoli", "domain": "greetings", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "water", "target_text": "machi", "dialect": "General", "domain": "basic", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "food", "target_text": "shikulia", "dialect": "General", "domain": "basic", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "house", "target_text": "ingu", "dialect": "General", "domain": "basic", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "mother", "target_text": "mama", "dialect": "General", "domain": "family", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "father", "target_text": "papa", "dialect": "General", "domain": "family", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "child", "target_text": "omwana", "dialect": "General", "domain": "family", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "love", "target_text": "okhenda", "dialect": "General", "domain": "emotions", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "peace", "target_text": "amalembe", "dialect": "General", "domain": "abstract", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "hello", "target_text": "mulembe", "dialect": "General", "domain": "greetings", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "goodbye", "target_text": "leka busalaamu", "dialect": "Bukusu", "domain": "greetings", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "yes", "target_text": "ee", "dialect": "General", "domain": "basic", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "no", "target_text": "sitini", "dialect": "General", "domain": "basic", "source_lang": "en", "target_lang": "luy"},
            {"source_text": "please", "target_text": "nyiise", "dialect": "General", "domain": "courtesy", "source_lang": "en", "target_lang": "luy"},
        ]
        
        print("Using fallback dataset")
        return self.process_dataset(fallback_data)
    
    def process_dataset(self, data: List[Dict]) -> bool:
        """Process dataset into searchable format"""
        try:
            self.documents = []
            self.metadata = []
            self.dialect_index = {}
            self.domain_index = {}
            self.lang_pair_index = {}
            
            for idx, item in enumerate(data):
                # Validate required fields
                if not item.get('source_text') or not item.get('target_text'):
                    continue
                
                # Create searchable content
                content = (f"Translation: {item['source_text']} → {item['target_text']} "
                          f"Dialect: {item.get('dialect', 'General')} "
                          f"Domain: {item.get('domain', 'general')} "
                          f"Languages: {item.get('source_lang', 'unknown')}-{item.get('target_lang', 'luy')}")
                
                self.documents.append(content)
                
                # Create metadata
                metadata = {
                    'type': 'translation',
                    'source_text': item['source_text'].strip(),
                    'target_text': item['target_text'].strip(),
                    'source_lang': item.get('source_lang', 'unknown'),
                    'target_lang': item.get('target_lang', 'luy'),
                    'dialect': item.get('dialect', 'General'),
                    'domain': item.get('domain', 'general'),
                    'id': item.get('id', f"entry_{idx}")
                }
                
                self.metadata.append(metadata)
                
                # Build indexes for faster searching
                dialect = metadata['dialect']
                if dialect not in self.dialect_index:
                    self.dialect_index[dialect] = []
                self.dialect_index[dialect].append(idx)
                
                domain = metadata['domain']
                if domain not in self.domain_index:
                    self.domain_index[domain] = []
                self.domain_index[domain].append(idx)
                
                lang_pair = f"{metadata['source_lang']}-{metadata['target_lang']}"
                if lang_pair not in self.lang_pair_index:
                    self.lang_pair_index[lang_pair] = []
                self.lang_pair_index[lang_pair].append(idx)
            
            print(f"Processed {len(self.documents)} entries")
            print(f"Dialects: {list(self.dialect_index.keys())}")
            print(f"Domains: {list(self.domain_index.keys())}")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"Error processing dataset: {e}")
            return False
    
    def initialize(self) -> bool:
        """Initialize the system with multiple fallback options"""
        if self.is_initialized:
            return True
        
        # Try loading from environment first (fastest)
        if self.load_dataset_from_env():
            return True
        
        # Try loading from URL (if you host the JSON file)
        if self.load_dataset_from_url(self.dataset_url):
            return True
        
        # Fallback to basic dataset
        return self.load_fallback_data()
    
    def detect_query_intent(self, query: str) -> Dict:
        """Detect user intent from query"""
        query_lower = query.lower().strip()
        
        intent_data = {
            'primary_intent': 'general',
            'key_terms': [],
            'response_style': 'conversational',
            'target_dialect': None,
            'target_domain': None
        }
        
        # Check for dialect-specific requests
        dialect_mentions = {
            'bukusu': 'Bukusu',
            'maragoli': 'Maragoli', 
            'luwanga': 'Luwanga',
            'luhya': 'General'
        }
        
        for dialect_key, dialect_name in dialect_mentions.items():
            if dialect_key in query_lower:
                intent_data['target_dialect'] = dialect_name
                break
        
        # Translation request patterns
        translation_patterns = [
            r'what (?:is|does|means?) ([^?]+?) in luhya(?:\?|$)',
            r'how (?:do you say|to say) ([^?]+?) in luhya(?:\?|$)',
            r'luhya (?:word|translation) for ([^?]+?)(?:\?|$)',
            r'translate ([^?]+?) (?:to|into) luhya(?:\?|$)',
            r'say ([^?]+?) in luhya(?:\?|$)',
            r'how do you say ([^?]+?)(?:\?|$)'
        ]
        
        # Dictionary lookup patterns
        dictionary_patterns = [
            r'what (?:is|does|means?) ([a-zA-Z]+)(?:\?|$)',
            r'(?:meaning of|define) ([^?]+?)(?:\?|$)',
            r'what does ([^?]+?) mean(?:\?|$)'
        ]
        
        # Check translation patterns
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
            common_words = {'what', 'is', 'the', 'how', 'do', 'you', 'say', 'in', 'luhya', 
                           'about', 'different', 'dialects', 'mean', 'means', 'translate'}
            words = [word for word in query_lower.split() if word not in common_words and len(word) > 2]
            intent_data['key_terms'] = words[:3]
        
        return intent_data
    
    def smart_search(self, query: str, intent_data: Dict, max_results: int = 15) -> List[Dict]:
        """Intelligent search with multiple strategies"""
        if not self.is_initialized:
            return []
        
        all_results = []
        
        # Strategy 1: Exact term matching
        exact_results = self.exact_term_search(intent_data['key_terms'], intent_data)
        all_results.extend(exact_results)
        
        # Strategy 2: Fuzzy term matching
        fuzzy_results = self.fuzzy_term_search(intent_data['key_terms'], intent_data)
        all_results.extend(fuzzy_results)
        
        # Strategy 3: Dialect-specific search
        if intent_data.get('target_dialect'):
            dialect_results = self.dialect_search(intent_data['target_dialect'], intent_data['key_terms'])
            all_results.extend(dialect_results)
        
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
    
    def exact_term_search(self, key_terms: List[str], intent_data: Dict) -> List[Dict]:
        """Search for exact term matches"""
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
                if term_lower == source_text:
                    score = 1.0
                elif term_lower == target_text:
                    score = 0.95
                elif term_lower in source_text and len(term_lower) > 3:
                    score = 0.8
                elif term_lower in target_text and len(term_lower) > 3:
                    score = 0.75
                
                # Boost score for dialect preference
                if intent_data.get('target_dialect') and metadata.get('dialect') == intent_data['target_dialect']:
                    score *= 1.2
                
                if score > 0:
                    results.append({
                        'content': self.documents[i],
                        'metadata': metadata,
                        'similarity': score,
                        'match_reason': f'Exact match for "{term}"'
                    })
        
        return results
    
    def fuzzy_term_search(self, key_terms: List[str], intent_data: Dict) -> List[Dict]:
        """Search for partial term matches"""
        results = []
        
        for term in key_terms:
            term_lower = term.lower().strip()
            if len(term_lower) < 3:
                continue
            
            for i, metadata in enumerate(self.metadata):
                source_text = metadata.get('source_text', '').lower()
                target_text = metadata.get('target_text', '').lower()
                
                score = 0
                
                # Word-level matching
                term_words = term_lower.split()
                source_words = source_text.split()
                target_words = target_text.split()
                
                for term_word in term_words:
                    if any(term_word in sw for sw in source_words):
                        score += 0.3
                    if any(term_word in tw for tw in target_words):
                        score += 0.25
                
                # Boost for dialect preference
                if intent_data.get('target_dialect') and metadata.get('dialect') == intent_data['target_dialect']:
                    score *= 1.3
                
                if score > 0.2:
                    results.append({
                        'content': self.documents[i],
                        'metadata': metadata,
                        'similarity': min(score, 0.9),  # Cap fuzzy scores
                        'match_reason': f'Partial match for "{term}"'
                    })
        
        return results
    
    def dialect_search(self, dialect: str, key_terms: List[str]) -> List[Dict]:
        """Search within specific dialect"""
        results = []
        
        if dialect not in self.dialect_index:
            return results
        
        indices = self.dialect_index[dialect]
        
        for idx in indices:
            metadata = self.metadata[idx]
            source_text = metadata.get('source_text', '').lower()
            target_text = metadata.get('target_text', '').lower()
            
            score = 0.5  # Base score for dialect match
            
            # Check if any key terms match
            for term in key_terms:
                term_lower = term.lower()
                if term_lower in source_text or term_lower in target_text:
                    score += 0.3
            
            if score > 0.5:
                results.append({
                    'content': self.documents[idx],
                    'metadata': metadata,
                    'similarity': score,
                    'match_reason': f'Dialect-specific: {dialect}'
                })
        
        return results
    
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
        
        # Group results by dialect
        dialect_groups = {}
        for result in results[:10]:
            dialect = result['metadata'].get('dialect', 'General')
            if dialect not in dialect_groups:
                dialect_groups[dialect] = []
            dialect_groups[dialect].append(result)
        
        if dialect_groups:
            if query_term:
                response_parts.append(f'**"{query_term}"** in Luhya:\n\n')
            
            # Show results grouped by dialect
            for dialect, dialect_results in dialect_groups.items():
                if len(dialect_groups) > 1:  # Only show dialect header if multiple dialects
                    response_parts.append(f"**{dialect} dialect:**\n")
                
                # Show unique translations for this dialect
                seen_targets = set()
                for result in dialect_results[:3]:
                    meta = result['metadata']
                    target = meta.get('target_text', '')
                    if target and target not in seen_targets:
                        response_parts.append(f"• **{target}**\n")
                        seen_targets.add(target)
                
                if len(dialect_groups) > 1:
                    response_parts.append("\n")
            
            # Add helpful context
            total_dialects = len(dialect_groups)
            if total_dialects > 1:
                response_parts.append(f"Found translations in {total_dialects} dialect(s). ")
            
            # Show domain if relevant
            domains = set(r['metadata'].get('domain', '') for r in results[:5])
            domains.discard('')
            if domains and len(domains) == 1:
                domain = domains.pop()
                if domain != 'general':
                    response_parts.append(f"(Category: {domain})")
        
        else:
            response_parts.append(f'I couldn\'t find a translation for **"{query_term}"** in my current database.')
            response_parts.append('\n\nTry asking about common words like "thank you", "good morning", or "water".')
        
        return "".join(response_parts)
    
    def format_general_response(self, query: str, results: List[Dict]) -> str:
        """Format general response"""
        response_parts = []
        
        response_parts.append("Here are relevant Luhya translations:\n\n")
        
        # Show top results
        for i, result in enumerate(results[:6]):
            meta = result['metadata']
            source = meta.get('source_text', '')
            target = meta.get('target_text', '')
            dialect = meta.get('dialect', 'General')
            
            response_parts.append(f"**{i+1}.** {source} → **{target}** ({dialect})\n")
        
        if len(results) > 6:
            response_parts.append(f"\n...and {len(results) - 6} more found.")
        
        return "".join(response_parts)
    
    def generate_no_results_response(self, query: str, intent_data: Dict) -> str:
        """Generate helpful response when no results found"""
        
        # Get some statistics
        total_entries = len(self.metadata)
        available_dialects = list(self.dialect_index.keys())
        
        return f"""I couldn't find specific information about that in my Luhya database ({total_entries:,} translations).

**Try asking about:**
• **Greetings**: "How do you say 'good morning' in Luhya?"
• **Courtesy**: "What's 'thank you' in different Luhya dialects?"
• **Basic words**: "How to say 'water' or 'food' in Luhya?"
• **Family terms**: "What's 'mother' in Luhya?"

**Available dialects**: {', '.join(available_dialects)}

Make your question more specific or try simpler terms!"""

# Initialize the RAG system globally
rag_system = LuhyaRAGSystem()

def handler(request):
    """Vercel serverless function handler"""
    try:
        # CORS preflight
        if request.method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Max-Age': '86400'
                },
                'body': ''
            }
        
        # Only allow POST
        if request.method != 'POST':
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        # Parse request body
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Invalid JSON in request body'})
            }
        
        message = body.get('message', '').strip()
        max_results = body.get('max_results', 10)
        
        if not message:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Message is required'})
            }
        
        # Initialize system if needed
        if not rag_system.initialize():
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'System initialization failed',
                    'response': 'Sorry, the translation system is having trouble starting. Please try again.'
                })
            }
        
        # Get intent analysis
        intent_data = rag_system.detect_query_intent(message)
        
        # Search for relevant content
        results = rag_system.smart_search(message, intent_data, max_results)
        
        # Generate response
        response = rag_system.generate_response(message, results, intent_data)
        
        # Format sources for frontend
        sources = []
        for result in results[:5]:
            meta = result['metadata']
            sources.append({
                'text': f"{meta.get('source_text', '')} → {meta.get('target_text', '')}",
                'metadata': {
                    'type': meta.get('domain', 'translation'),
                    'dialect': meta.get('dialect', 'General'),
                    'confidence': result.get('similarity', 0),
                    'lang_pair': f"{meta.get('source_lang', '')}-{meta.get('target_lang', '')}"
                }
            })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'response': response,
                'sources': sources,
                'intent': intent_data['primary_intent'],
                'query_terms': intent_data['key_terms'],
                'target_dialect': intent_data.get('target_dialect'),
                'total_results': len(results)
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
                'message': str(e),
                'response': 'Sorry, something went wrong. Please try again.'
            })
        }

# Vercel expects the handler to be named 'app' for Python functions
app = handler