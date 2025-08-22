export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }
  
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'Luhya RAG Chatbot',
    version: '1.0.0',
    cost: '$0.00',
    search_method: 'Simple Demo Search',
    features: [
      'Intent Detection',
      'Multi-Dialect Support',
      'Conversational Responses'
    ]
  });
}