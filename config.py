import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', 0))
    
    # Solana
    SOLANA_PRIVATE_KEY = os.getenv('SOLANA_PRIVATE_KEY')
    SOLANA_RPC_URL = os.getenv('SOLANA_RPC_URL')
    
    # Groq
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = "llama-3.3-70b-versatile"
    
    # Trading Parameters
    TAKE_PROFIT_PERCENT = 0.15  # 15%
    STOP_LOSS_PERCENT = 0.10    # 10%
    MAX_POSITION_SOL = 0.5      # Max 0.5 SOL per trade
    MIN_LIQUIDITY_USD = 50000
    MIN_VOLUME_1H_USD = 100000
    
    # API Endpoints
    DEXSCREENER_API = "https://api.dexscreener.com/latest/dex"
    JUPITER_API = "https://quote-api.jup.ag/v6"
    SOLSCAN_API = "https://public-api.solscan.io"
    
    # Cache TTL (seconds)
    CACHE_TTL = 10
    
    # Rate Limiting
    MAX_GROQ_CALLS_PER_MINUTE = 25
    MAX_TRADES_PER_HOUR = 10

config = Config()