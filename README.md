```markdown
# 🚀 Solana Meme Coin AI Trading Bot

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://t.me/botfather)
[![Solana](https://img.shields.io/badge/Solana-Blockchain-purple.svg)](https://solana.com/)
[![Groq](https://img.shields.io/badge/Groq-AI-orange.svg)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> 🤖 **AI-Powered Automated Trading Bot for Solana Meme Coins**  
> Built with Groq LLM, Real-time Whale Detection, and Auto TP/SL

## 📊 Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Analysis** | Groq LLM (Llama 3.3 70B) for real-time token analysis |
| 🐋 **Whale Detection** | Monitors top holders for locked/unlocked status |
| 📈 **Auto Trading** | Automatic buy/sell based on AI confidence scores |
| 🎯 **Risk Management** | Take Profit: 15% \| Stop Loss: 10% |
| 💎 **Solana Native** | Jupiter DEX integration for fast, low-cost swaps |
| 📱 **Telegram UI** | Professional interface with inline keyboards |
| 🔄 **Real-time Monitoring** | Automatic position checking every 10 seconds |
| 📊 **Trade History** | Complete logging of all trades with PnL |

## 🎯 How It Works

```
1. Scanner fetches trending Solana tokens from Dexscreener
2. AI (Groq) analyzes each token for pump potential
3. Whale wallet activity is checked via Solscan
4. If AI confidence > 70% → Auto buy (if enabled)
5. Bot monitors price every 10 seconds
6. Auto sell at +15% profit or -10% loss
```

## 📸 Screenshots

<details>
<summary>Click to view UI</summary>

```
┌─────────────────────────────────────┐
│  🚀 Meme Coin AI Trading Bot         │
│  🤖 Powered by Groq LLM              │
│  📊 TP: 15% | SL: 10%                │
├─────────────────────────────────────┤
│  🔍 AI Scan & Trade                  │
│  📊 My Positions                     │
│  💰 Balance                          │
│  📈 Trade History                    │
│  ⚙️ Settings                         │
│  🛑 Stop All                         │
└─────────────────────────────────────┘
```

</details>

## 🛠️ Tech Stack

- **Python 3.9+** - Core language
- **python-telegram-bot** - Telegram Bot API
- **Solana Web3** - Blockchain interaction
- **Jupiter API** - DEX aggregation
- **Groq SDK** - LLM inference (<100ms latency)
- **SQLite** - Local database
- **Dexscreener API** - Token data

## 📋 Prerequisites

- Python 3.9 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Solana Wallet (with private key)
- Groq API Key (from [console.groq.com](https://console.groq.com))
- Minimum 0.5 SOL for trading (recommended)

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/solana-meme-trading-bot.git
cd solana-meme-trading-bot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```env
TELEGRAM_BOT_TOKEN=7123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxx
SOLANA_PRIVATE_KEY=2xQ9t8xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_CHAT_ID=123456789
```

### 4. Run Bot

```bash
python run.py
```

## 📁 Project Structure

```
solana-meme-trading-bot/
├── .env                      # Environment variables
├── requirements.txt          # Python dependencies
├── config.py                 # Configuration management
├── database.py               # SQLite database operations
├── solana_client.py          # Solana/Jupiter integration
├── groq_analyzer.py          # Groq AI analysis
├── scanner.py                # Token scanning & whale detection
├── trader.py                 # Trading logic & position management
├── main.py                   # Telegram bot UI
├── run.py                    # Entry point
└── trading_bot.db            # SQLite database (auto-created)
```

## ⚙️ Configuration Options

Edit `config.py` to customize:

```python
TAKE_PROFIT_PERCENT = 0.15    # 15% take profit
STOP_LOSS_PERCENT = 0.10      # 10% stop loss
MAX_POSITION_SOL = 0.5        # Max 0.5 SOL per trade
MIN_LIQUIDITY_USD = 50000     # Minimum liquidity filter
MIN_VOLUME_1H_USD = 100000    # Minimum volume filter
```

## 🤖 Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Show main menu |
| `🔍 AI Scan & Trade` | Scan and analyze meme coins |
| `📊 My Positions` | View active trades |
| `💰 Balance` | Check wallet balance |
| `📈 Trade History` | View past trades |
| `⚙️ Settings` | Configure auto-trade, TP/SL |
| `🛑 Stop All` | Emergency sell all positions |

## 📊 AI Analysis Output

```
🤖 AI Scan Results (3 found)

1. $BONKAI
   💰 Price: $0.00000123
   🎯 Confidence: 87%
   📊 Risk: MEDIUM
   💡 Whale wallets holding + volume up 340%

2. $WIFCAT
   💰 Price: $0.0000456
   🎯 Confidence: 72%
   📊 Risk: HIGH
   💡 New pair with high momentum
```

## ⚠️ Risk Warning

> **CRYPTO TRADING INVOLVES SUBSTANTIAL RISK OF LOSS**  
> Meme coins are extremely volatile. This bot is for educational purposes.  
> Never trade more than you can afford to lose. Start with small amounts.

**Recommended starting capital:** 0.5-1 SOL for testing

## 🔒 Security Best Practices

1. ✅ Use a **dedicated trading wallet** (not your main wallet)
2. ✅ Store `.env` file securely - never commit to GitHub
3. ✅ Start with **small amounts** to test
4. ✅ Monitor bot activity regularly
5. ✅ Use **read-only RPC** when possible
6. ✅ Keep private keys **offline** when not in use

## 🐛 Troubleshooting

### Bot not responding?
```bash
# Check if bot is running
ps aux | grep python

# Restart bot
pkill -f run.py
python run.py
```

### Swap failures?
- Ensure sufficient SOL for fees (0.05 SOL minimum)
- Check token liquidity on Dexscreener
- Verify RPC endpoint is working

### Groq API errors?
```bash
# Check rate limits (25/min free tier)
# Implemented auto-retry with fallback
```

## 📈 Performance Expectations

| Metric | Expected |
|--------|----------|
| Scan time | 15-30 seconds |
| Trade execution | 2-5 seconds |
| Position monitoring | Every 10 seconds |
| AI response | <200ms (Groq) |
| Success rate (simulated) | ~40-60% (depends on market) |

## 🔄 Roadmap

- [ ] Add trailing stop loss
- [ ] Multi-wallet support
- [ ] Web dashboard (FastAPI)
- [ ] Twitter sentiment analysis
- [ ] Discord alerts
- [ ] Backtesting framework
- [ ] Support for Raydium new pairs
- [ ] MEV protection

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

Distributed under MIT License. See `LICENSE` for more information.

## 🙏 Acknowledgments

- [Jupiter DEX](https://jup.ag) - Best Solana DEX aggregator
- [Groq](https://groq.com) - Blazing fast LLM inference
- [Dexscreener](https://dexscreener.com) - Token data API
- [Solana Web3](https://solana.com/docs) - Blockchain SDK

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/solana-meme-trading-bot/issues)
- **Discord**: [Join our Discord](https://discord.gg/yourinvite)
- **Twitter**: [@YourHandle](https://twitter.com/yourhandle)

## ⭐ Star History

If this bot helps you, please give it a star! ⭐

---

**Disclaimer:** This software is for educational purposes only. The authors are not responsible for any financial losses incurred while using this bot. Always do your own research before trading.

**Built with ❤️ for the Solana ecosystem**
```

---

## 📝 Additional Files to Create

### `LICENSE` (MIT License)

```txt
MIT License

Copyright (c) 2024 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
