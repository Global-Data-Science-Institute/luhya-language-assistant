# api/chat.py - Refined Vercel serverless function with better filtering
import json
import os
import re
import random
from typing import List, Dict, Optional
from urllib.request import urlopen
from urllib.error import URLError
from werkzeug.wrappers import Request, Response

class RefinedLuhyaRAGSystem:
    def __init__(self):
        self.is_initialized = False
        self.documents = []
        self.metadata = []
        self.dialect_index = {}
        self.domain_index = {}
        
        # URL to your processed dataset
        self.dataset_url = "https://raw.githubusercontent.com/Global-Data-Science-Institute/luhya-language-assistant/refs/heads/main/data/luhya_dataset.json"
        
        # Conversation patterns
        self.conversation_patterns = {
            'greeting_starters': [
                "",  # Most common - direct response
                "Here's what I found: ",
                "In Luhya, ",
            ],
            'meaning_starters': [
                "",  # Direct response
                "Let me explain: ",
                "Here's the meaning: ",
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
            
        except Exception as e:
            print(f"Failed to load from URL: {e}")
            return False
    
    def load_dataset_from_env(self) -> bool:
        """Load dataset from environment variable"""
        try:
            import base64
            
            dataset_b64 = os.environ.get('LUHYA_DATASET_B64')
            if not dataset_b64:
                return False
            
            dataset_json = base64.b64decode(dataset_b64).decode('utf-8')
            data = json.loads(dataset_json)
            
            print(f"Loaded {len(data)} entries from environment")
            return self.process_dataset(data)
            
        except Exception as e:
            print(f"Failed to load from environment: {e}")
            return False
    
    def load_fallback_data(self) -> bool:
        """Load basic fallback data"""
        fallback_data = [
            # Greetings
            {"source_text": "good morning", "target_text": "bulamasawa", "dialect": "Bukusu", "domain": "greetings"},
            {"source_text": "good morning", "target_text": "bushiangala", "dialect": "Maragoli", "domain": "greetings"},
            {"source_text": "good morning", "target_text": "vushiere", "dialect": "Tsotso", "domain": "greetings"},
            {"source_text": "good morning", "target_text": "bushere", "dialect": "Luwanga", "domain": "greetings"},
            
            # Common courtesy
            {"source_text": "thank you", "target_text": "nyasaye akurinde", "dialect": "Bukusu", "domain": "courtesy"},
            {"source_text": "thank you", "target_text": "orio", "dialect": "Luwanga", "domain": "courtesy"},
            {"source_text": "thank you", "target_text": "asante", "dialect": "Maragoli", "domain": "courtesy"},
            
            # Basic greetings
            {"source_text": "hello", "target_text": "mulembe", "dialect": "General", "domain": "greetings"},
            {"source_text": "how are you", "target_text": "oli otia", "dialect": "Bukusu", "domain": "greetings"},
            {"source_text": "how are you", "target_text": "uli wahi", "dialect": "Maragoli", "domain": "greetings"},
            
            # Basic words
            {"source_text": "water", "target_text": "machi", "dialect": "General", "domain": "basic"},
            {"source_text": "food", "target_text": "shikulia", "dialect": "General", "domain": "basic"},
            {"source_text": "house", "target_text": "ingu", "dialect": "General", "domain": "basic"},
        ]
        
        print("Using fallback dataset")
        return self.process_dataset(fallback_data)
    
    def process_dataset(self, data: List[Dict]) -> bool:
        """Process dataset with better filtering"""
        try:
            self.documents = []
            self.metadata = []
            self.dialect_index = {}
            self.domain_index = {}
            
            for idx, item in enumerate(data):
                if not item.get('source_text') or not item.get('target_text'):
                    continue
                
                source_text = str(item['source_text']).strip()
                target_text = str(item['target_text']).strip()
                
                # Skip overly long entries (likely Bible verses or long passages)
                if len(source_text) > 100 or len(target_text) > 100:
                    continue
                
                # Skip entries with HTML-like tags or formatting issues
                if any(tag in target_text.lower() for tag in ['<en>', '<sw>', '<luy_']):
                    # Clean the target text by removing tags
                    target_text = re.sub(r'<[^>]+>', '', target_text).strip()
                    if not target_text or len(target_text) > 100:
                        continue
                
                # Skip biblical or very formal language for basic queries
                domain = str(item.get('domain', 'general')).lower()
                
                # Create searchable content
                content = f"{source_text} → {target_text} ({item.get('dialect', 'General')})"
                
                # Create metadata
                metadata = {
                    'source_text': source_text,
                    'target_text': target_text,
                    'source_lang': item.get('source_lang', 'en'),
                    'target_lang': item.get('target_lang', 'luy'),
                    'dialect': item.get('dialect', 'General'),
                    'domain': domain,
                    'id': f"entry_{idx}",
                    'length_score': self.calculate_length_score(source_text, target_text),
                    'quality_score': self.calculate_quality_score(source_text, target_text, domain)
                }
                
                self.documents.append(content)
                self.metadata.append(metadata)
                
                # Build indexes
                dialect = metadata['dialect']
                if dialect not in self.dialect_index:
                    self.dialect_index[dialect] = []
                self.dialect_index[dialect].append(idx)
                
                if domain not in self.domain_index:
                    self.domain_index[domain] = []
                self.domain_index[domain].append(idx)
            
            print(f"Processed {len(self.documents)} entries")
            print(f"Dialects: {list(self.dialect_index.keys())}")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"Error processing dataset: {e}")
            return False
    
    def calculate_length_score(self, source: str, target: str) -> float:
        """Calculate score based on text length (shorter is better for basic translations)"""
        avg_length = (len(source) + len(target)) / 2
        if avg_length <= 20:
            return 1.0  # Perfect for single words/short phrases
        elif avg_length <= 50:
            return 0.8  # Good for phrases
        elif avg_length <= 100:
            return 0.5  # OK for sentences
        else:
            return 0.1  # Poor for long passages
    
    def calculate_quality_score(self, source: str, target: str, domain: str) -> float:
        """Calculate quality score based on various factors"""
        score = 1.0
        
        # Prefer dictionary and basic translation entries
        if domain in ['dictionary', 'translations', 'greetings', 'courtesy', 'basic']:
            score += 0.5
        elif domain == 'bible':
            score -= 0.3  # Deprioritize biblical text for basic queries
        
        # Prefer entries without complex punctuation
        if not any(char in source + target for char in ['"', '(', ')', '[', ']', ';', ':']):
            score += 0.2
        
        # Penalize entries with numbers or special characters
        if re.search(r'\d', source + target):
            score -= 0.2
        
        return max(0.1, score)
    
    def initialize(self) -> bool:
        """Initialize system with fallbacks"""
        if self.is_initialized:
            return True
        
        # Try environment first
        if self.load_dataset_from_env():
            return True
        
        # Try URL
        if self.load_dataset_from_url(self.dataset_url):
            return True
        
        # Fallback
        return self.load_fallback_data()
    
    def detect_query_intent(self, query: str) -> Dict:
        """Enhanced intent detection"""
        query_lower = query.lower().strip()
        
        intent_data = {
            'primary_intent': 'general',
            'key_terms': [],
            'target_dialect': None,
            'query_type': 'translation'  # translation, meaning, general
        }
        
        # Check for specific dialect mentions
        dialect_patterns = {
            'bukusu': 'Bukusu',
            'maragoli': 'Maragoli',
            'luwanga': 'Luwanga',
            'tsotso': 'Tsotso',
            'marachi': 'Marachi'
        }
        
        for pattern, dialect in dialect_patterns.items():
            if pattern in query_lower:
                intent_data['target_dialect'] = dialect
                break
        
        # Enhanced translation patterns with better extraction
        translation_patterns = [
            (r'how do you say ["\']([^"\']+)["\'] in (?:(\w+) )?luhya', 'translation_request'),
            (r'what is ["\']([^"\']+)["\'] in (?:(\w+) )?luhya', 'translation_request'),
            (r'how to say ["\']([^"\']+)["\'] in (?:(\w+) )?luhya', 'translation_request'),
            (r'say ["\']([^"\']+)["\'] in (?:(\w+) )?luhya', 'translation_request'),
            (r'translate ["\']([^"\']+)["\'] to (?:(\w+) )?luhya', 'translation_request'),
            (r'["\']([^"\']+)["\'] in (?:(\w+) )?luhya', 'translation_request'),
            
            # Without quotes
            (r'how do you say ([^?]+?) in (?:(\w+) )?luhya', 'translation_request'),
            (r'what is ([^?]+?) in (?:(\w+) )?luhya', 'translation_request'),
            (r'how to say ([^?]+?) in (?:(\w+) )?luhya', 'translation_request'),
            (r'say ([^?]+?) in (?:(\w+) )?luhya', 'translation_request'),
            (r'translate ([^?]+?) to (?:(\w+) )?luhya', 'translation_request'),
        ]
        
        # Dictionary/meaning patterns
        meaning_patterns = [
            (r'what does ([^?]+?) mean', 'dictionary_lookup'),
            (r'meaning of ([^?]+)', 'dictionary_lookup'),
            (r'define ([^?]+)', 'dictionary_lookup'),
            (r'what is ([a-zA-Z]+)', 'dictionary_lookup'),  # For Luhya words
        ]
        
        # Check translation patterns first
        for pattern, intent in translation_patterns:
            match = re.search(pattern, query_lower)
            if match:
                intent_data['primary_intent'] = intent
                intent_data['key_terms'] = [match.group(1).strip()]
                intent_data['query_type'] = 'translation'
                
                # Check if dialect was specified in the pattern
                if len(match.groups()) > 1 and match.group(2):
                    dialect_mentioned = match.group(2).lower()
                    if dialect_mentioned in dialect_patterns:
                        intent_data['target_dialect'] = dialect_patterns[dialect_mentioned]
                break
        
        # Check meaning patterns if no translation pattern matched
        if intent_data['primary_intent'] == 'general':
            for pattern, intent in meaning_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    intent_data['primary_intent'] = intent
                    intent_data['key_terms'] = [match.group(1).strip()]
                    intent_data['query_type'] = 'meaning'
                    break
        
        # Extract key terms if not found
        if not intent_data['key_terms']:
            stop_words = {'what', 'is', 'the', 'how', 'do', 'you', 'say', 'in', 'luhya', 'mean', 'means'}
            words = [w for w in query_lower.split() if w not in stop_words and len(w) > 2]
            intent_data['key_terms'] = words[:2]
        
        return intent_data
    
    def smart_search(self, query: str, intent_data: Dict, max_results: int = 10) -> List[Dict]:
        """Refined search with better scoring"""
        if not self.is_initialized:
            return []
        
        results = []
        key_terms = intent_data.get('key_terms', [])
        target_dialect = intent_data.get('target_dialect')
        query_type = intent_data.get('query_type', 'translation')
        
        for term in key_terms:
            if not term or len(term) < 2:
                continue
                
            term_lower = term.lower().strip()
            
            for i, metadata in enumerate(self.metadata):
                source = metadata['source_text'].lower()
                target = metadata['target_text'].lower()
                dialect = metadata['dialect']
                domain = metadata['domain']
                
                # Calculate base similarity score
                similarity = 0
                match_type = ""
                
                # Exact matches get highest priority
                if term_lower == source:
                    similarity = 1.0
                    match_type = "exact_source"
                elif term_lower == target and query_type == 'meaning':
                    similarity = 0.98
                    match_type = "exact_target"
                # Word boundary matches
                elif re.search(rf'\b{re.escape(term_lower)}\b', source):
                    similarity = 0.85
                    match_type = "word_boundary_source"
                elif re.search(rf'\b{re.escape(term_lower)}\b', target) and query_type == 'meaning':
                    similarity = 0.82
                    match_type = "word_boundary_target"
                # Contains matches (only for longer terms)
                elif len(term_lower) > 3 and term_lower in source:
                    similarity = 0.7
                    match_type = "contains_source"
                elif len(term_lower) > 3 and term_lower in target and query_type == 'meaning':
                    similarity = 0.67
                    match_type = "contains_target"
                
                if similarity > 0:
                    # Apply quality multipliers
                    final_score = similarity * metadata['length_score'] * metadata['quality_score']
                    
                    # Dialect boost
                    if target_dialect and dialect == target_dialect:
                        final_score *= 1.3
                        match_type += f"_dialect_boost_{target_dialect}"
                    
                    # Domain preference for basic queries
                    if domain in ['dictionary', 'translations', 'greetings', 'courtesy']:
                        final_score *= 1.2
                    elif domain == 'bible':
                        final_score *= 0.6  # Significantly reduce biblical entries
                    
                    results.append({
                        'metadata': metadata,
                        'similarity': similarity,
                        'final_score': final_score,
                        'match_type': match_type
                    })
        
        # Sort by final score and remove duplicates
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Remove duplicates based on source-target-dialect combination
        seen = set()
        unique_results = []
        
        for result in results:
            meta = result['metadata']
            key = (meta['source_text'].lower(), meta['target_text'].lower(), meta['dialect'])
            
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
                
                if len(unique_results) >= max_results:
                    break
        
        return unique_results
    
    def generate_response(self, query: str, results: List[Dict], intent_data: Dict) -> str:
        """Generate clean, focused responses"""
        if not results:
            return self.generate_no_results_response(query, intent_data)
        
        # Extract query term for response
        query_term = intent_data['key_terms'][0] if intent_data['key_terms'] else ""
        target_dialect = intent_data.get('target_dialect')
        query_type = intent_data.get('query_type', 'translation')
        
        response_parts = []
        
        # Add minimal starter (mostly empty for cleaner responses)
        starter = random.choice(self.conversation_patterns['greeting_starters'])
        if starter:
            response_parts.append(starter)
        
        # Generate response based on query type
        if query_type == 'translation':
            content = self.format_translation_response(query_term, results, target_dialect)
        else:
            content = self.format_meaning_response(query_term, results, target_dialect)
        
        response_parts.append(content)
        return "".join(response_parts)
    
    def format_translation_response(self, query_term: str, results: List[Dict], target_dialect: str = None) -> str:
        """Format translation responses in a natural, conversational way"""
        response_parts = []
        
        # Group by dialect for better organization
        dialect_groups = {}
        for result in results[:8]:  # Limit to best results
            meta = result['metadata']
            dialect = meta['dialect']
            
            if dialect not in dialect_groups:
                dialect_groups[dialect] = []
            dialect_groups[dialect].append(meta['target_text'])
        
        # Remove duplicates within each dialect
        for dialect in dialect_groups:
            dialect_groups[dialect] = list(dict.fromkeys(dialect_groups[dialect]))
        
        # Generate natural conversational response
        if target_dialect and target_dialect in dialect_groups:
            # User asked for specific dialect
            translations = dialect_groups[target_dialect][:3]
            response_parts.append(f'In {target_dialect} Luhya, *{query_term}* is **{translations[0]}**')
            
            if len(translations) > 1:
                response_parts.append(f' (you might also hear *{", ".join(translations[1:])}*)')
            response_parts.append('.')
        
        elif len(dialect_groups) == 1:
            # Single dialect found
            dialect = list(dialect_groups.keys())[0]
            translations = list(dialect_groups.values())[0][:3]
            
            if dialect == 'General':
                response_parts.append(f'In Luhya, *{query_term}* is **{translations[0]}**')
            else:
                response_parts.append(f'In Luhya (specifically {dialect}), *{query_term}* is **{translations[0]}**')
            
            if len(translations) > 1:
                response_parts.append(f' (variations include *{", ".join(translations[1:])}*)')
            response_parts.append('.')
            
        else:
            # Multiple dialects - show the variation
            primary_dialect = list(dialect_groups.keys())[0]
            primary_translation = dialect_groups[primary_dialect][0]
            
            response_parts.append(f'In Luhya, *{query_term}* is **{primary_translation}**, though the exact word varies by dialect:\n\n')
            
            for dialect, translations in list(dialect_groups.items())[:4]:  # Show up to 4 dialects
                unique_translations = translations[:2]  # Max 2 per dialect
                response_parts.append(f'• **{dialect}:** *{", ".join(unique_translations)}*\n')
            
            if len(dialect_groups) > 4:
                response_parts.append(f'\n*...and {len(dialect_groups) - 4} more dialect(s)*')
        
        # Add pronunciation tip for common words
        self.add_pronunciation_tip(query_term.lower(), response_parts)
        
        return "".join(response_parts).strip()
    
    def add_pronunciation_tip(self, word: str, response_parts: List[str]):
        """Add helpful pronunciation tips for common words"""
        pronunciation_tips = {
            'good morning': "\n\n*Tip: In most Luhya dialects, morning greetings are used until around 10 AM.*",
            'thank you': "\n\n*Note: Expressing gratitude is very important in Luhya culture, and the phrases often invoke blessings.*",
            'hello': "\n\n*Cultural note: Luhya greetings often inquire about one's wellbeing and peace.*",
            'water': "\n\n*This is an essential word to know, as asking for water is common courtesy when visiting.*"
        }
        
        if word in pronunciation_tips:
            response_parts.append(pronunciation_tips[word])
    
    def generate_response(self, query: str, results: List[Dict], intent_data: Dict) -> str:
        """Generate clean, focused responses with appropriate starters"""
        if not results:
            return self.generate_no_results_response(query, intent_data)
        
        # Extract query term for response
        query_term = intent_data['key_terms'][0] if intent_data['key_terms'] else ""
        target_dialect = intent_data.get('target_dialect')
        query_type = intent_data.get('query_type', 'translation')
        
        response_parts = []
        
        # Choose appropriate starter based on query type
        if query_type == 'meaning':
            starter = random.choice(self.conversation_patterns['meaning_starters'])
        else:
            starter = random.choice(self.conversation_patterns['greeting_starters'])
        
        if starter:
            response_parts.append(starter)
        
        # Generate response based on query type
        if query_type == 'translation':
            content = self.format_translation_response(query_term, results, target_dialect)
        else:
            content = self.format_meaning_response(query_term, results, target_dialect)
        
        response_parts.append(content)
        return "".join(response_parts)
    
    def format_meaning_response(self, query_term: str, results: List[Dict], target_dialect: str = None) -> str:
        """Format meaning/dictionary responses in a natural, conversational way"""
        if not results:
            return f'I couldn\'t find the meaning of *{query_term}* in my Luhya database.'
        
        response_parts = []
        
        # Group results by dialect and meaning
        dialect_meanings = {}
        translations = {}
        
        for result in results[:8]:
            meta = result['metadata']
            source = meta['source_text'].strip()
            target = meta['target_text'].strip()
            dialect = meta['dialect']
            
            # Skip overly long entries
            if len(source) > 80 or len(target) > 80:
                continue
            
            if dialect not in dialect_meanings:
                dialect_meanings[dialect] = []
            
            # Determine if this is a definition or translation
            if query_term.lower() == target.lower():
                # This is defining a Luhya word
                dialect_meanings[dialect].append({
                    'type': 'definition',
                    'luhya_word': target,
                    'meaning': source,
                    'explanation': self.extract_explanation(source)
                })
            elif query_term.lower() == source.lower():
                # This is translating from English
                translations[dialect] = translations.get(dialect, [])
                translations[dialect].append(target)
        
        # Generate natural response
        if translations:
            # English to Luhya translation
            main_dialect = list(translations.keys())[0]
            main_translation = translations[main_dialect][0]
            
            response_parts.append(f'In Luhya, *{query_term}* translates to **{main_translation}**')
            
            if len(translations) > 1:
                response_parts.append(f' (primarily in the {main_dialect} dialect)')
            
            response_parts.append('.\n\n')
            
            # Show variations across dialects
            if len(translations) > 1:
                response_parts.append('**Variations across dialects:**\n')
                for dialect, words in translations.items():
                    unique_words = list(dict.fromkeys(words))  # Remove duplicates while preserving order
                    response_parts.append(f'• **{dialect}:** *{", ".join(unique_words)}*\n')
        
        elif dialect_meanings:
            # Luhya to English definition
            main_dialect = list(dialect_meanings.keys())[0]
            main_meanings = dialect_meanings[main_dialect]
            
            if main_meanings:
                primary_meaning = main_meanings[0]
                
                response_parts.append(f'In Luhya')
                if len(dialect_meanings) == 1:
                    response_parts.append(f' (specifically the {main_dialect} dialect)')
                
                response_parts.append(f', *{query_term}* ')
                
                # Add context based on meaning
                explanation = primary_meaning['explanation']
                if 'greeting' in explanation.lower():
                    response_parts.append('is a common greeting. ')
                elif 'peace' in explanation.lower():
                    response_parts.append('means **"peace."** ')
                else:
                    response_parts.append(f'means **"{primary_meaning["meaning"]}."** ')
                
                # Add more detailed explanations
                if len(main_meanings) > 1:
                    response_parts.append('\n\n**Different uses:**\n')
                    for meaning in main_meanings[:3]:
                        if meaning['explanation']:
                            response_parts.append(f'• *{meaning["explanation"]}*\n')
                
                # Add dialect variations if present
                if len(dialect_meanings) > 1:
                    response_parts.append('\n**In other dialects:**\n')
                    for dialect, meanings in list(dialect_meanings.items())[1:3]:  # Show up to 2 more dialects
                        if meanings:
                            response_parts.append(f'• **{dialect}:** similar usage\n')
                
                # Add cultural context
                self.add_cultural_context(query_term.lower(), response_parts)
        
        return "".join(response_parts).strip()
    
    def extract_explanation(self, text: str) -> str:
        """Extract meaningful explanation from source text"""
        text = text.lower().strip()
        
        # Common patterns that indicate explanations
        if 'greeting' in text and 'peace' in text:
            return "greeting meaning 'peace'"
        elif 'lit.' in text:
            # Extract literal meaning
            match = re.search(r"lit\.\s*['\"]([^'\"]+)['\"]", text)
            if match:
                return f"literally '{match.group(1)}'"
        elif len(text) < 50 and not re.search(r'[.!?]{2,}', text):
            return text
        
        return ""
    
    def add_cultural_context(self, word: str, response_parts: List[str]):
        """Add cultural context for common Luhya words"""
        contexts = {
            'mulembe': "\n\nCulturally, *mulembe* is more than just a word—it's a way of greeting someone while wishing them peace and well-being.",
            'asante': "\n\nThis word shows the influence of Swahili on some Luhya dialects.",
            'nyasaye': "\n\nThis is the traditional Luhya name for God, widely used across different dialects.",
            'mama': "\n\nUsed respectfully to address mothers or elder women in the community.",
            'papa': "\n\nA respectful term for fathers or elder men."
        }
        
        if word in contexts:
            response_parts.append(contexts[word])
    
    def generate_no_results_response(self, query: str, intent_data: Dict) -> str:
        """Generate helpful no-results response"""
        query_term = intent_data['key_terms'][0] if intent_data['key_terms'] else "that"
        
        available_dialects = list(self.dialect_index.keys())[:5]  # Show first 5
        
        return f"""I couldn't find **"{query_term}"** in my Luhya database.

**Try asking about:**
• Common greetings: "good morning", "hello", "how are you"
• Basic courtesy: "thank you", "please", "excuse me"  
• Essential words: "water", "food", "house"

**Available dialects:** {', '.join(available_dialects)}

Try simpler terms or check your spelling!"""

def process_request(request_data):
    """Process the request and return response data"""
    try:
        method = request_data.get('httpMethod', '')
        body = request_data.get('body', '{}')
        
        # CORS headers
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        
        # Handle OPTIONS
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        # Only POST allowed
        if method != 'POST':
            return {
                'statusCode': 405,
                'headers': {**cors_headers, 'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        # Parse request
        try:
            body_data = json.loads(body)
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': {**cors_headers, 'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid JSON'})
            }
        
        message = body_data.get('message', '').strip()
        if not message:
            return {
                'statusCode': 400,
                'headers': {**cors_headers, 'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Message required'})
            }
        
        # Initialize system
        rag_system = RefinedLuhyaRAGSystem()
        if not rag_system.initialize():
            return {
                'statusCode': 500,
                'headers': {**cors_headers, 'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'System initialization failed',
                    'response': 'Translation system unavailable. Please try again.'
                })
            }
        
        # Process query
        intent_data = rag_system.detect_query_intent(message)
        results = rag_system.smart_search(message, intent_data, 10)
        response_text = rag_system.generate_response(message, results, intent_data)
        
        # Format sources
        sources = []
        for result in results[:3]:
            meta = result['metadata']
            sources.append({
                'text': f"{meta['source_text']} → {meta['target_text']}",
                'metadata': {
                    'dialect': meta['dialect'],
                    'domain': meta['domain'],
                    'confidence': round(result['final_score'], 2)
                }
            })
        
        return {
            'statusCode': 200,
            'headers': {**cors_headers, 'Content-Type': 'application/json'},
            'body': json.dumps({
                'response': response_text,
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
                'response': 'Something went wrong. Please try again.'
            })
        }

# WSGI application wrapper
@Request.application
def app(request):
    result = process_request({
        "httpMethod": request.method,
        "body": request.get_data(as_text=True)
    })

    return Response(
        response=result["body"],
        status=result["statusCode"],
        headers=result["headers"]
    )