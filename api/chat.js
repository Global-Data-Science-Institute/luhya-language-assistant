// api/chat.js - Updated to use your Luhya dataset
let datasetCache = null;
let searchIndex = null;

// Simple TF-IDF implementation for Node.js
class SimpleTFIDF {
  constructor() {
    this.documents = [];
    this.vocabulary = new Map();
    this.idf = new Map();
    this.tfidf = [];
  }

  addDocument(text) {
    const words = this.tokenize(text.toLowerCase());
    this.documents.push(words);
    
    // Build vocabulary
    const uniqueWords = new Set(words);
    uniqueWords.forEach(word => {
      if (!this.vocabulary.has(word)) {
        this.vocabulary.set(word, this.vocabulary.size);
      }
    });
  }

  build() {
    // Calculate IDF
    const docCount = this.documents.length;
    this.vocabulary.forEach((index, word) => {
      const docsWithWord = this.documents.filter(doc => doc.includes(word)).length;
      this.idf.set(word, Math.log(docCount / (docsWithWord + 1)));
    });

    // Calculate TF-IDF for each document
    this.tfidf = this.documents.map(doc => {
      const tf = new Map();
      doc.forEach(word => {
        tf.set(word, (tf.get(word) || 0) + 1);
      });

      const vector = new Array(this.vocabulary.size).fill(0);
      tf.forEach((count, word) => {
        const tfScore = count / doc.length;
        const idfScore = this.idf.get(word) || 0;
        const index = this.vocabulary.get(word);
        vector[index] = tfScore * idfScore;
      });
      return vector;
    });
  }

  search(query, limit = 10) {
    const queryWords = this.tokenize(query.toLowerCase());
    const queryVector = new Array(this.vocabulary.size).fill(0);
    
    queryWords.forEach(word => {
      if (this.vocabulary.has(word)) {
        const index = this.vocabulary.get(word);
        queryVector[index] = 1;
      }
    });

    // Calculate cosine similarity
    const similarities = this.tfidf.map((docVector, docIndex) => {
      const similarity = this.cosineSimilarity(queryVector, docVector);
      return { docIndex, similarity };
    });

    return similarities
      .filter(item => item.similarity > 0.1)
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, limit);
  }

  tokenize(text) {
    return text
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 2);
  }

  cosineSimilarity(vecA, vecB) {
    const dotProduct = vecA.reduce((sum, a, i) => sum + a * vecB[i], 0);
    const magnitudeA = Math.sqrt(vecA.reduce((sum, a) => sum + a * a, 0));
    const magnitudeB = Math.sqrt(vecB.reduce((sum, b) => sum + b * b, 0));
    
    if (magnitudeA === 0 || magnitudeB === 0) return 0;
    return dotProduct / (magnitudeA * magnitudeB);
  }
}

async function loadDataset() {
  if (datasetCache) return datasetCache;

  try {
    console.log('Loading Luhya dataset from HuggingFace...');
    
    // Fetch dataset from HuggingFace Hub
    const response = await fetch('https://huggingface.co/datasets/mamakobe/luhya-multilingual-dataset/resolve/main/train.csv');
    
    if (!response.ok) {
      throw new Error(`Failed to fetch dataset: ${response.status}`);
    }
    
    const csvText = await response.text();
    const rows = csvText.split('\n').slice(1); // Skip header
    
    const dataset = [];
    
    for (const row of rows) {
      if (!row.trim()) continue;
      
      // Simple CSV parsing (assumes no commas in quoted fields for simplicity)
      const columns = row.split(',');
      
      if (columns.length >= 6) {
        const item = {
          source_text: columns[0]?.replace(/"/g, '').trim(),
          target_text: columns[1]?.replace(/"/g, '').trim(),
          source_lang: columns[2]?.replace(/"/g, '').trim(),
          target_lang: columns[3]?.replace(/"/g, '').trim(),
          dialect: columns[4]?.replace(/"/g, '').trim(),
          domain: columns[5]?.replace(/"/g, '').trim()
        };
        
        if (item.source_text && item.target_text) {
          dataset.push(item);
        }
      }
    }
    
    console.log(`Loaded ${dataset.length} translations`);
    datasetCache = dataset;
    
    // Build search index
    buildSearchIndex(dataset);
    
    return dataset;
    
  } catch (error) {
    console.error('Error loading dataset:', error);
    // Fallback to demo data
    return [
      { source_text: 'good morning', target_text: 'bwakhera', dialect: 'Bukusu', domain: 'greetings' },
      { source_text: 'hello', target_text: 'muraho', dialect: 'General', domain: 'greetings' },
      { source_text: 'thank you', target_text: 'webale', dialect: 'Wanga', domain: 'courtesy' },
      { source_text: 'water', target_text: 'amatsi', dialect: 'General', domain: 'nouns' },
      { source_text: 'goodbye', target_text: 'khwilindila', dialect: 'General', domain: 'greetings' }
    ];
  }
}

function buildSearchIndex(dataset) {
  console.log('Building search index...');
  
  searchIndex = {
    tfidf: new SimpleTFIDF(),
    documents: [],
    metadata: []
  };
  
  // Create documents for TF-IDF
  dataset.forEach((item, index) => {
    const document = `${item.source_text} ${item.target_text} ${item.dialect} ${item.domain}`;
    searchIndex.tfidf.addDocument(document);
    searchIndex.documents.push(document);
    searchIndex.metadata.push(item);
  });
  
  searchIndex.tfidf.build();
  console.log('Search index built successfully');
}

function detectIntent(query) {
  const queryLower = query.toLowerCase().trim();
  
  // Translation request patterns
  const translationPatterns = [
    /what (?:is|does|means?) (.+?) in luhya/,
    /how (?:do you say|to say) (.+?) in luhya/,
    /luhya (?:word|translation) for (.+?)$/,
    /translate (.+?) (?:to|into) luhya/,
    /say (.+?) in luhya/
  ];
  
  // Dictionary lookup patterns  
  const dictionaryPatterns = [
    /what (?:is|does|means?) ([a-zA-Z]+)$/,
    /(?:meaning of|define) (.+?)$/,
    /what does (.+?) mean/
  ];
  
  // Check translation patterns first
  for (const pattern of translationPatterns) {
    const match = queryLower.match(pattern);
    if (match) {
      return {
        type: 'translation_request',
        term: match[1].trim(),
        confidence: 0.9
      };
    }
  }
  
  // Check dictionary patterns
  for (const pattern of dictionaryPatterns) {
    const match = queryLower.match(pattern);
    if (match) {
      return {
        type: 'dictionary_lookup', 
        term: match[1].trim(),
        confidence: 0.8
      };
    }
  }
  
  return {
    type: 'general',
    term: queryLower,
    confidence: 0.5
  };
}

function searchDataset(query, intent, limit = 10) {
  if (!searchIndex) {
    console.log('Search index not ready, using simple search');
    return simpleSearch(query, intent, limit);
  }
  
  const results = [];
  
  // Direct term search (highest priority)
  const directResults = directTermSearch(query, intent.term);
  results.push(...directResults);
  
  // TF-IDF semantic search
  const semanticResults = searchIndex.tfidf.search(query, limit);
  semanticResults.forEach(result => {
    const metadata = searchIndex.metadata[result.docIndex];
    results.push({
      content: `${metadata.source_text} → ${metadata.target_text}`,
      metadata,
      similarity: result.similarity,
      strategy: 'semantic'
    });
  });
  
  // Remove duplicates and sort by relevance
  const uniqueResults = [];
  const seen = new Set();
  
  for (const result of results) {
    const key = `${result.metadata.source_text}-${result.metadata.target_text}`;
    if (!seen.has(key)) {
      seen.add(key);
      uniqueResults.push(result);
    }
  }
  
  return uniqueResults
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, limit);
}

function directTermSearch(query, term) {
  if (!datasetCache) return [];
  
  const results = [];
  const searchTerm = term.toLowerCase();
  
  datasetCache.forEach(item => {
    const sourceText = item.source_text.toLowerCase();
    const targetText = item.target_text.toLowerCase();
    
    let score = 0;
    
    // Exact matches get highest score
    if (sourceText === searchTerm || targetText === searchTerm) {
      score = 1.0;
    } else if (sourceText.includes(searchTerm) || targetText.includes(searchTerm)) {
      score = 0.8;
    } else if (sourceText.split(' ').some(word => word === searchTerm) || 
               targetText.split(' ').some(word => word === searchTerm)) {
      score = 0.6;
    }
    
    if (score > 0) {
      results.push({
        content: `${item.source_text} → ${item.target_text}`,
        metadata: item,
        similarity: score,
        strategy: 'direct'
      });
    }
  });
  
  return results;
}

function simpleSearch(query, intent, limit) {
  if (!datasetCache) return [];
  
  const queryLower = query.toLowerCase();
  const results = [];
  
  datasetCache.forEach(item => {
    const searchText = `${item.source_text} ${item.target_text}`.toLowerCase();
    if (searchText.includes(queryLower) || queryLower.includes(item.source_text.toLowerCase())) {
      results.push({
        content: `${item.source_text} → ${item.target_text}`,
        metadata: item,
        similarity: 0.7,
        strategy: 'simple'
      });
    }
  });
  
  return results.slice(0, limit);
}

function generateResponse(query, results, intent) {
  if (!results || results.length === 0) {
    return generateNoResultsResponse(query, intent);
  }
  
  if (intent.type === 'translation_request') {
    return formatTranslationResponse(query, results, intent);
  } else if (intent.type === 'dictionary_lookup') {
    return formatDictionaryResponse(query, results, intent);
  } else {
    return formatGeneralResponse(query, results);
  }
}

function formatTranslationResponse(query, results, intent) {
  const responseParts = [];
  
  if (intent.term) {
    responseParts.push(`To say "${intent.term}" in Luhya:\n`);
  }
  
  // Group by dialect
  const byDialect = {};
  results.slice(0, 5).forEach(result => {
    const dialect = result.metadata.dialect || 'General';
    if (!byDialect[dialect]) {
      byDialect[dialect] = [];
    }
    byDialect[dialect].push(result);
  });
  
  Object.entries(byDialect).forEach(([dialect, dialectResults]) => {
    dialectResults.forEach(result => {
      const meta = result.metadata;
      if (intent.type === 'translation_request') {
        // For "how to say X in Luhya", show the Luhya word
        if (meta.source_text.toLowerCase().includes(intent.term.toLowerCase())) {
          responseParts.push(`**${meta.target_text}** (${dialect} dialect)`);
        } else if (meta.target_text.toLowerCase().includes(intent.term.toLowerCase())) {
          responseParts.push(`**${meta.source_text}** (${dialect} dialect)`);
        }
      }
    });
  });
  
  if (responseParts.length === 1) { // Only the intro
    responseParts.push('I couldn\'t find a specific translation for that term.');
  }
  
  if (Object.keys(byDialect).length > 1) {
    responseParts.push(`\nFound translations in ${Object.keys(byDialect).length} dialects.`);
  }
  
  return responseParts.join('\n');
}

function formatDictionaryResponse(query, results, intent) {
  const responseParts = [];
  
  results.slice(0, 3).forEach((result, index) => {
    const meta = result.metadata;
    responseParts.push(`**${index + 1}.** ${meta.source_text} → ${meta.target_text} (${meta.dialect || 'General'} dialect)`);
  });
  
  return responseParts.join('\n');
}

function formatGeneralResponse(query, results) {
  const responseParts = [];
  
  results.slice(0, 5).forEach((result, index) => {
    const meta = result.metadata;
    responseParts.push(`**${meta.source_text}** → **${meta.target_text}** (${meta.dialect || 'General'})`);
  });
  
  return responseParts.join('\n');
}

function generateNoResultsResponse(query, intent) {
  return `I couldn't find "${intent.term || query}" in my Luhya database.

Try asking about common words like:
- "How do you say 'hello' in Luhya?"
- "What does 'muraho' mean?"
- "Luhya word for water"

Or search for greetings, family terms, or everyday phrases.`;
}

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }
  
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  try {
    const { message } = req.body;
    
    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }
    
    // Load dataset if not already loaded
    await loadDataset();
    
    // Detect intent
    const intent = detectIntent(message);
    
    // Search dataset
    const results = searchDataset(message, intent, 10);
    
    // Generate response
    const responseText = generateResponse(message, results, intent);
    
    // Format sources for frontend
    const sources = results.slice(0, 3).map(result => ({
      text: `${result.metadata.source_text} → ${result.metadata.target_text}`,
      metadata: {
        type: result.metadata.domain || 'translation',
        dialect: result.metadata.dialect || 'General',
        confidence: result.similarity || 0
      }
    }));
    
    res.status(200).json({
      response: responseText,
      sources
    });
    
  } catch (error) {
    console.error('Error in chat handler:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: error.message
    });
  }
}