from groq import Groq
import json
import re
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from config import config

class GroqAnalyzer:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.last_call_time = 0
        self.call_count = 0
    
    async def _rate_limit(self):
        """Simple rate limiting"""
        self.call_count += 1
        if self.call_count >= config.MAX_GROQ_CALLS_PER_MINUTE:
            await asyncio.sleep(60)
            self.call_count = 0
    
    async def analyze_token(self, token_data: Dict) -> Dict:
        """Main analysis for a token"""
        await self._rate_limit()
        
        prompt = f"""Analyze this Solana meme coin for trading potential:

Token: {token_data.get('symbol', 'Unknown')}
Price: ${token_data.get('price', 0)}
Market Cap: ${token_data.get('market_cap', 0):,.0f}
Liquidity: ${token_data.get('liquidity', 0):,.0f}
Volume (1h): ${token_data.get('volume_1h', 0):,.0f}
Volume (24h): ${token_data.get('volume_24h', 0):,.0f}
Age: {token_data.get('age_minutes', 0)} minutes
Top 10 Holders: {token_data.get('top10_percent', 0)}%
Whale Locked: {'Yes' if token_data.get('whale_locked') else 'No'}
Price Change (5m): {token_data.get('price_change_5m', 0)}%
Price Change (1h): {token_data.get('price_change_1h', 0)}%

Return ONLY valid JSON:
{{
    "decision": "BUY" or "PASS",
    "confidence": 0-100,
    "target_15min": predicted price in USD,
    "risk_level": "LOW" or "MEDIUM" or "HIGH",
    "reasoning": "short explanation max 100 chars",
    "expected_pnl": "10-30"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            # Extract JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # Validate required fields
                required = ['decision', 'confidence', 'target_15min', 'risk_level', 'reasoning']
                for field in required:
                    if field not in result:
                        result[field] = "PASS" if field == 'decision' else 0
                return result
                
        except Exception as e:
            print(f"Groq analysis error: {e}")
        
        return {"decision": "PASS", "confidence": 0, "target_15min": 0, 
                "risk_level": "HIGH", "reasoning": "Analysis failed"}
    
    async def analyze_sentiment(self, messages: List[str]) -> Dict:
        """Analyze social media sentiment"""
        await self._rate_limit()
        
        if not messages:
            return {"sentiment": "neutral", "confidence": 50}
        
        prompt = f"""Analyze sentiment of these crypto messages:
{chr(10).join(messages[:10])}

Return JSON: {{"sentiment": "bullish/bearish/neutral", "confidence": 0-100, "key_triggers": []}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {"sentiment": "neutral", "confidence": 50, "key_triggers": []}
    
    async def generate_notification(self, action: str, token_symbol: str, 
                                     price: float, reason: str) -> str:
        """Generate human-readable notification"""
        await self._rate_limit()
        
        prompt = f"""Create a short, exciting Telegram notification for a crypto trade:
Action: {action}
Token: ${token_symbol}
Price: ${price}
Reason: {reason}

Make it professional, include emojis, max 200 chars."""
        
        try:
            response = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except:
            return f"{'🟢' if action == 'BUY' else '🔴'} {action} ${token_symbol} at ${price:.8f}"

groq_analyzer = GroqAnalyzer(config.GROQ_API_KEY)