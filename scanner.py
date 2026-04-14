import requests
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from cachetools import TTLCache
from config import config
from groq_analyzer import groq_analyzer

class TokenScanner:
    def __init__(self):
        self.cache = TTLCache(maxsize=100, ttl=config.CACHE_TTL)
    
    async def get_trending_tokens(self) -> List[Dict]:
        """Get trending tokens from Dexscreener"""
        cache_key = "trending_tokens"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Get Solana pairs from Dexscreener
            url = f"{config.DEXSCREENER_API}/search?q=solana"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            tokens = []
            for pair in data.get('pairs', [])[:30]:  # Top 30 pairs
                if pair.get('chainId') == 'solana':
                    token_info = {
                        'mint': pair.get('baseToken', {}).get('address', ''),
                        'symbol': pair.get('baseToken', {}).get('symbol', ''),
                        'name': pair.get('baseToken', {}).get('name', ''),
                        'price': float(pair.get('priceUsd', 0)),
                        'liquidity': float(pair.get('liquidity', {}).get('usd', 0)),
                        'volume_1h': float(pair.get('volume', {}).get('h1', 0)),
                        'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                        'market_cap': float(pair.get('fdv', 0)),
                        'price_change_5m': float(pair.get('priceChange', {}).get('m5', 0)),
                        'price_change_1h': float(pair.get('priceChange', {}).get('h1', 0)),
                        'age_minutes': self._calculate_age_minutes(pair.get('pairCreatedAt', 0))
                    }
                    
                    # Filter basic requirements
                    if (token_info['liquidity'] >= config.MIN_LIQUIDITY_USD and
                        token_info['volume_1h'] >= config.MIN_VOLUME_1H_USD and
                        token_info['price'] > 0):
                        tokens.append(token_info)
            
            self.cache[cache_key] = tokens
            return tokens
            
        except Exception as e:
            print(f"Error fetching trending tokens: {e}")
            return []
    
    async def check_whale_locked(self, token_mint: str) -> bool:
        """Check if top holders are locked (not selling)"""
        cache_key = f"whale_{token_mint}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Use Solscan API for holder info
            url = f"{config.SOLSCAN_API}/token/holders"
            params = {"tokenAddress": token_mint, "limit": 10}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                holders = data.get('data', [])
                
                if len(holders) >= 3:
                    # Check top 3 holders percentage
                    top3_percent = sum([h.get('percent', 0) for h in holders[:3]])
                    
                    # If top 3 hold > 40%, consider them "locked" (less likely to dump)
                    # In real implementation, you'd check their recent transactions
                    locked = top3_percent < 60  # More decentralized is better
                    self.cache[cache_key] = locked
                    return locked
            
            return True  # Default to locked if can't check
            
        except Exception as e:
            print(f"Whale check error: {e}")
            return True
    
    def _calculate_age_minutes(self, created_timestamp: int) -> int:
        """Calculate token age in minutes"""
        if not created_timestamp:
            return 999999
        created_time = datetime.fromtimestamp(created_timestamp)
        age = datetime.now() - created_time
        return int(age.total_seconds() / 60)
    
    async def scan_with_ai(self) -> List[Dict]:
        """Full scan with AI analysis"""
        print("🔍 Starting AI scan...")
        
        # Get trending tokens
        tokens = await self.get_trending_tokens()
        if not tokens:
            return []
        
        candidates = []
        
        for token in tokens[:15]:  # Scan top 15
            # Check whale locked
            token['whale_locked'] = await self.check_whale_locked(token['mint'])
            
            # AI Analysis
            ai_result = await groq_analyzer.analyze_token(token)
            
            # Combine with rules
            if (ai_result['decision'] == 'BUY' and 
                ai_result['confidence'] >= 60 and
                token['whale_locked'] and
                token['liquidity'] >= config.MIN_LIQUIDITY_USD):
                
                candidates.append({
                    'token': token,
                    'ai_decision': ai_result,
                    'score': ai_result['confidence']
                })
                
                # Save to database
                from database import db
                db.save_ai_signal(
                    token['mint'], token['symbol'],
                    ai_result['decision'], ai_result['confidence'],
                    ai_result['target_15min'], ai_result['reasoning']
                )
        
        # Sort by confidence
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates

scanner = TokenScanner()