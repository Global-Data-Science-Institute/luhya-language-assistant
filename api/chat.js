export default function handler(req, res) {
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
  
  const { message } = req.body;
  
  if (!message) {
    return res.status(400).json({ error: 'Message is required' });
  }
  
  // Simple demo responses
  const demoData = [
    { source: 'good morning', target: 'bwakhera', dialect: 'Bukusu' },
    { source: 'hello', target: 'muraho', dialect: 'General' },
    { source: 'thank you', target: 'webale', dialect: 'Wanga' },
    { source: 'water', target: 'amatsi', dialect: 'General' },
    { source: 'goodbye', target: 'khwilindila', dialect: 'General' }
  ];
  
  const query = message.toLowerCase();
  const results = demoData.filter(item => 
    query.includes(item.source) || query.includes(item.target)
  );
  
  let response;
  if (results.length > 0) {
    response = results.map(r => 
      `**${r.source}** → **${r.target}** (${r.dialect} dialect)`
    ).join('\n');
  } else {
    response = "I couldn't find that in my basic Luhya database. Try asking about 'good morning', 'hello', 'thank you', 'water', or 'goodbye'.";
  }
  
  const sources = results.map(r => ({
    text: `${r.source} → ${r.target}`,
    metadata: {
      type: 'translation',
      dialect: r.dialect,
      confidence: 0.9
    }
  }));
  
  res.status(200).json({
    response,
    sources
  });
}