# api/chat.py - Vercel-compatible function
import json
import os
import re
import random
from typing import List, Dict

# Simple Luhya dataset (you can expand this with your processed data)
LUHYA_DATA = [
    {"source_text": "good morning", "target_text": "bulamasawa", "dialect": "Bukusu", "domain": "greetings"},
    {"source_text": "good morning", "target_text": "bushiangala", "dialect": "Maragoli", "domain": "greetings"},
    {"source_text": "thank you", "target_text": "nyasaye akurinde", "dialect": "Bukusu", "domain": "courtesy"},
    {"source_text": "thank you", "target_text": "nyasaye akurunde", "dialect": "Maragoli", "domain": "courtesy"},
    {"source_text": "thank you", "target_text": "nyasayene", "dialect": "Bukusu", "domain": "courtesy"},
    {"source_text": "how are you", "target_text": "oli otia", "dialect": "Bukusu", "domain": "greetings"},
    {"source_text": "how are you", "target_text": "uli wahi", "dialect": "Maragoli", "domain": "greetings"},
    {"source_text": "hello", "target_text": "muraho", "dialect": "General", "domain": "greetings"},
    {"source_text": "goodbye", "target_text": "leka busalaamu", "dialect": "Bukusu", "domain": "greetings"},
    {"source_text": "water", "target_text": "machi", "dialect": "General", "domain": "basic"},
    {"source_text": "food", "target_text": "shikulia", "dialect": "General", "domain": "basic"},
    {"source_text": "house", "target_text": "ingu", "dialect": "General", "domain": "basic"},
    {"source_text": "mother", "target_text": "mama", "dialect": "General", "domain": "family"},
    {"source_text": "father", "target_text": "papa", "dialect": "General", "domain": "family"},
    {"source_text": "child", "target_text": "omwana", "dialect": "General", "domain": "family"},
    {"source_text": "love", "target_text": "okhenda", "dialect": "General", "domain": "emotions"},
    {"source_text": "peace", "target_text": "amalembe", "dialect": "General", "domain": "abstract"},
    {"source_text": "yes", "target_text": "ee", "dialect": "General", "domain": "basic"},
    {"source_text": "no", "target_text": "sitini", "dialect": "General", "domain": "basic"},
    {"source_text": "please", "target_text": "nyiise", "dialect": "General", "domain": "courtesy"},
]

def detect_query_intent(query: str) -> Dict:
    """Detect user intent from query"""
    query_lower = query.lower().strip()
    
    intent_data = {
        'primary_intent': 'general',
        'key_terms': [],
        'response_style': 'conversational',
        'target_dialect': None
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

def search_translations(query: str, intent_data: Dict, max_results: int = 10) -> List[Dict]:
    """Search for translations"""
    results = []
    
    for term in intent_data['key_terms']:
        term_lower = term.lower().strip()
        if len(term_lower) < 2:
            continue
        
        for entry in LUHYA_DATA:
            source_text = entry['source_text'].lower()
            target_text = entry['target_text'].lower()
            
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
            elif any(word in source_text for word in term_lower.split()):
                score = 0.6
            elif any(word in target_text for word in term_lower.split()):
                score = 0.55
            
            # Boost score for dialect preference
            if intent_data.get('target_dialect') and entry.get('dialect') == intent_data['target_dialect']:
                score *= 1.2
            
            if score > 0:
                result_entry = entry.copy()
                result_entry['similarity'] = score
                result_entry['match_reason'] = f'Match for "{term}"'
                results.append(result_entry)
    
    # Remove duplicates and sort by score
    seen_ids = set()
    unique_results = []
    
    for result in sorted(results, key=lambda x: x.get('similarity', 0), reverse=True):
        result_id = f"{result['source_text']}_{result['target_text']}_{result['dialect']}"
        if result_id not in seen_ids:
            seen_ids.add(result_id)
            unique_results.append(result)
        
        if len(unique_results) >= max_results:
            break
    
    return unique_results

def generate_response(query: str, results: List[Dict], intent_data: Dict) -> str:
    """Generate human-like response"""
    if not results:
        return generate_no_results_response(query, intent_data)
    
    response_parts = []
    
    # Add conversational starter
    starters = ["Here's what I found: ", "Great question! ", "I can help with that! ", ""]
    starter = random.choice(starters)
    if starter:
        response_parts.append(starter)
    
    # Generate main content based on intent
    if intent_data['primary_intent'] in ['translation_request', 'dictionary_lookup']:
        main_content = format_translation_response(query, results, intent_data)
    else:
        main_content = format_general_response(query, results)
    
    response_parts.append(main_content)
    
    return "".join(response_parts)

def format_translation_response(query: str, results: List[Dict], intent_data: Dict) -> str:
    """Format translation response"""
    response_parts = []
    
    # Extract the term being asked about
    query_term = intent_data['key_terms'][0] if intent_data['key_terms'] else ""
    
    # Group results by dialect
    dialect_groups = {}
    for result in results[:8]:
        dialect = result.get('dialect', 'General')
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
            for result in dialect_results[:3]:  # Max 3 per dialect
                target = result.get('target_text', '')
                if target and target not in seen_targets:
                    response_parts.append(f"• **{target}**\n")
                    seen_targets.add(target)
            
            if len(dialect_groups) > 1:
                response_parts.append("\n")
        
        # Add helpful context
        total_dialects = len(dialect_groups)
        if total_dialects > 1:
            response_parts.append(f"Found translations in {total_dialects} dialect(s).")
    
    else:
        response_parts.append(f'I couldn\'t find a translation for **"{query_term}"** in my current database.')
        response_parts.append('\n\nTry asking about common words like "thank you", "good morning", or "water".')
    
    return "".join(response_parts)

def format_general_response(query: str, results: List[Dict]) -> str:
    """Format general response"""
    response_parts = []
    
    response_parts.append("Here are relevant Luhya translations:\n\n")
    
    # Show top results
    for i, result in enumerate(results[:5]):
        source = result.get('source_text', '')
        target = result.get('target_text', '')
        dialect = result.get('dialect', 'General')
        
        response_parts.append(f"**{i+1}.** {source} → **{target}** ({dialect})\n")
    
    if len(results) > 5:
        response_parts.append(f"\n...and {len(results) - 5} more found.")
    
    return "".join(response_parts)

def generate_no_results_response(query: str, intent_data: Dict) -> str:
    """Generate helpful response when no results found"""
    return """I couldn't find specific information about that in my Luhya database.

**Try asking about:**
• **Greetings**: "How do you say 'good morning' in Luhya?"
• **Courtesy**: "What's 'thank you' in different Luhya dialects?"
• **Basic words**: "How to say 'water' or 'food' in Luhya?"
• **Family terms**: "What's 'mother' in Luhya?"

I have translations for common words and phrases across Bukusu, Maragoli, and other Luhya dialects."""

def handler(request):
    """Main Vercel serverless function handler"""
    
    # Handle CORS preflight
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
    
    # Only allow POST requests
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # Parse request body
        try:
            if hasattr(request, 'body'):
                body = json.loads(request.body)
            else:
                # Fallback for different request formats
                body = json.loads(request.get_json())
        except (json.JSONDecodeError, AttributeError, TypeError):
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
        
        # Get intent analysis
        intent_data = detect_query_intent(message)
        
        # Search for relevant content
        results = search_translations(message, intent_data, max_results)
        
        # Generate response
        response_text = generate_response(message, results, intent_data)
        
        # Format sources for frontend
        sources = []
        for result in results[:5]:
            sources.append({
                'text': f"{result.get('source_text', '')} → {result.get('target_text', '')}",
                'metadata': {
                    'type': result.get('domain', 'translation'),
                    'dialect': result.get('dialect', 'General'),
                    'confidence': result.get('similarity', 0.8)
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
                'response': 'Sorry, something went wrong. Please try again.'
            })
        }