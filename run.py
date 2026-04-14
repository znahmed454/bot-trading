#!/usr/bin/env python3
"""
Meme Coin AI Trading Bot - Solana
Run with: python run.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import TradingBot

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════╗
    ║   🚀 Meme Coin AI Trading Bot - Solana   ║
    ║   🤖 Powered by Groq LLM                 ║
    ║   📊 TP: 15% | SL: 10%                   ║
    ╚══════════════════════════════════════════╝
    """)
    
    bot = TradingBot()
    bot.run()