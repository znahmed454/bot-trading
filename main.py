from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
from datetime import datetime
from config import config
from database import db
from scanner import scanner
from trader import trader
from solana_client import solana_client
from groq_analyzer import groq_analyzer

class TradingBot:
    def __init__(self):
        self.app = None
        self.scanning_active = False
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        keyboard = [
            [InlineKeyboardButton("🔍 AI Scan & Trade", callback_data='scan_trade')],
            [InlineKeyboardButton("📊 My Positions", callback_data='my_positions')],
            [InlineKeyboardButton("💰 Balance", callback_data='balance')],
            [InlineKeyboardButton("📈 Trade History", callback_data='history')],
            [InlineKeyboardButton("⚙️ Settings", callback_data='settings')],
            [InlineKeyboardButton("🛑 Stop All", callback_data='stop_all')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_msg = (
            "🚀 *Meme Coin AI Trading Bot* (Solana)\n\n"
            "🤖 *Features:*\n"
            "• AI-powered meme coin scanning (Groq LLM)\n"
            "• Whale wallet detection\n"
            "• Auto TP 15% / SL 10%\n"
            "• Real-time position monitoring\n\n"
            "⚠️ *Risk Warning:* Meme coins are highly volatile!\n"
            "Start with small amounts only."
        )
        
        await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def scan_trade_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle scan and trade"""
        query = update.callback_query
        await query.answer()
        
        chat_id = update.effective_chat.id
        
        # Send initial message
        msg = await query.edit_message_text(
            "🔍 *AI Scanning Meme Coins on Solana...*\n\n"
            "Analyzing with Groq AI + Whale Detection\n"
            "⏳ Please wait (15-30 seconds)",
            parse_mode='Markdown'
        )
        
        # Run scan
        candidates = await scanner.scan_with_ai()
        
        if not candidates:
            await msg.edit_text(
                "❌ *No promising tokens found*\n\n"
                "Try again in a few minutes.",
                parse_mode='Markdown'
            )
            return
        
        # Get user settings
        settings = db.get_user_settings(chat_id)
        auto_trade = settings.get('auto_trade', 0)
        
        # Display results
        result_text = f"🤖 *AI Scan Results* ({len(candidates)} found)\n\n"
        
        keyboard = []
        for i, candidate in enumerate(candidates[:5], 1):
            token = candidate['token']
            ai = candidate['ai_decision']
            
            result_text += f"{i}. *${token['symbol']}*\n"
            result_text += f"   💰 Price: ${token['price']:.10f}\n"
            result_text += f"   🎯 Confidence: {ai['confidence']}%\n"
            result_text += f"   📊 Risk: {ai['risk_level']}\n"
            result_text += f"   💡 {ai['reasoning']}\n\n"
            
            # Add buy button
            keyboard.append([InlineKeyboardButton(
                f"BUY ${token['symbol']} (Conf: {ai['confidence']}%)",
                callback_data=f"buy_{token['mint']}_{token['symbol']}"
            )])
        
        # Add auto trade toggle
        status = "✅ ON" if auto_trade else "❌ OFF"
        keyboard.append([InlineKeyboardButton(
            f"🤖 Auto Trade {status}", callback_data="toggle_auto"
        )])
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="scan_trade")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.edit_text(result_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Auto trade if enabled
        if auto_trade and candidates:
            best = candidates[0]
            if best['ai_decision']['confidence'] >= 70:
                await self.auto_buy(chat_id, best, context)
    
    async def auto_buy(self, chat_id: int, candidate: dict, context: ContextTypes.DEFAULT_TYPE):
        """Auto buy based on AI signal"""
        token = candidate['token']
        ai = candidate['ai_decision']
        
        # Check if already have position
        positions = db.get_active_positions(chat_id)
        if len(positions) >= 5:  # Max 5 concurrent positions
            return
        
        # Execute buy
        success, msg, tx = await trader.execute_buy(
            chat_id, token['mint'], token['symbol'],
            token['price'], ai['reasoning']
        )
        
        if success and context.bot:
            await context.bot.send_message(
                chat_id,
                f"🤖 *AUTO TRADE EXECUTED*\n\n{msg}\n\n"
                f"🔗 TX: `{tx[:20]}...`\n"
                f"🎯 TP: +15% | SL: -10%",
                parse_mode='Markdown'
            )
    
    async def buy_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle manual buy"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        parts = data.split('_')
        if len(parts) >= 3:
            token_mint = parts[1]
            token_symbol = parts[2]
            
            # Get token price
            price = await solana_client.get_token_price(token_mint)
            
            if price <= 0:
                await query.edit_message_text("❌ Cannot get token price. Try again.")
                return
            
            # Confirm buy
            keyboard = [
                [InlineKeyboardButton("✅ Confirm Buy", callback_data=f"confirm_{token_mint}_{token_symbol}_{price}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📝 *Confirm Purchase*\n\n"
                f"Token: ${token_symbol}\n"
                f"Price: ${price:.10f}\n"
                f"Max Buy: {config.MAX_POSITION_SOL} SOL\n"
                f"TP: +15% | SL: -10%\n\n"
                f"Confirm to execute?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    async def confirm_buy_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute confirmed buy"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        parts = data.split('_')
        if len(parts) >= 4:
            token_mint = parts[1]
            token_symbol = parts[2]
            price = float(parts[3])
            
            await query.edit_message_text("🔄 Executing buy order...")
            
            success, msg, tx = await trader.execute_buy(
                update.effective_chat.id, token_mint, token_symbol,
                price, "Manual buy"
            )
            
            if success:
                await query.edit_message_text(
                    f"✅ *BUY ORDER EXECUTED*\n\n{msg}\n\n"
                    f"🔗 TX: `{tx[:30]}...`\n"
                    f"📊 Will auto-sell at +15% or -10%",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(f"❌ Buy failed: {msg}")
    
    async def my_positions_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show active positions"""
        query = update.callback_query
        await query.answer()
        
        positions = db.get_active_positions(update.effective_chat.id)
        
        if not positions:
            await query.edit_message_text("📭 *No active positions*", parse_mode='Markdown')
            return
        
        text = "📊 *Active Positions*\n\n"
        keyboard = []
        
        for pos in positions:
            current_price = await solana_client.get_token_price(pos['token_mint'])
            pnl_percent = ((current_price - pos['buy_price']) / pos['buy_price']) * 100
            pnl_color = "🟢" if pnl_percent >= 0 else "🔴"
            
            text += f"{pnl_color} *${pos['token_symbol']}*\n"
            text += f"   Buy: ${pos['buy_price']:.10f}\n"
            text += f"   Current: ${current_price:.10f}\n"
            text += f"   PnL: {pnl_percent:.2f}%\n"
            text += f"   TP: +{pos['take_profit_percent']}% | SL: -{pos['stop_loss_percent']}%\n\n"
            
            keyboard.append([InlineKeyboardButton(
                f"Sell ${pos['token_symbol']} ({pnl_percent:.1f}%)",
                callback_data=f"sell_{pos['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="my_positions")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def sell_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sell position"""
        query = update.callback_query
        await query.answer()
        
        position_id = int(query.data.split('_')[1])
        
        await query.edit_message_text("🔄 Selling position...")
        
        success, msg, tx, pnl, pnl_pct = await trader.execute_sell(position_id, "Manual sell")
        
        if success:
            await query.edit_message_text(
                f"✅ *SOLD*\n\n{msg}\n\n"
                f"PnL: {pnl_pct:+.2f}% | ${pnl:+.4f}\n"
                f"🔗 TX: `{tx[:30]}...`",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(f"❌ Sell failed: {msg}")
    
    async def balance_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show wallet balance"""
        query = update.callback_query
        await query.answer()
        
        balance = solana_client.get_balance()
        sol_price = await solana_client.get_sol_price()
        
        text = (
            f"💰 *Wallet Balance*\n\n"
            f"SOL: {balance:.4f} SOL\n"
            f"USD: ${balance * sol_price:.2f}\n\n"
            f"📊 *Active Positions:* {len(db.get_active_positions(update.effective_chat.id))}\n"
            f"⚙️ Max per trade: {config.MAX_POSITION_SOL} SOL"
        )
        
        await query.edit_message_text(text, parse_mode='Markdown')
    
    async def history_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show trade history"""
        query = update.callback_query
        await query.answer()
        
        # Get history from DB
        db.cursor.execute('''
            SELECT token_symbol, buy_price, sell_price, pnl_percent, sell_time, reason
            FROM trade_history 
            WHERE chat_id = ? 
            ORDER BY sell_time DESC 
            LIMIT 10
        ''', (update.effective_chat.id,))
        
        rows = db.cursor.fetchall()
        
        if not rows:
            await query.edit_message_text("📭 *No trade history*", parse_mode='Markdown')
            return
        
        text = "📜 *Trade History* (Last 10)\n\n"
        
        for row in rows:
            symbol, buy_price, sell_price, pnl_pct, sell_time, reason = row
            emoji = "🟢" if pnl_pct >= 0 else "🔴"
            text += f"{emoji} *${symbol}*: {pnl_pct:+.2f}%\n"
            text += f"   {reason[:50]}\n\n"
        
        await query.edit_message_text(text, parse_mode='Markdown')
    
    async def settings_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show settings"""
        query = update.callback_query
        await query.answer()
        
        chat_id = update.effective_chat.id
        settings = db.get_user_settings(chat_id)
        
        keyboard = [
            [InlineKeyboardButton(
                f"🤖 Auto Trade: {'ON' if settings['auto_trade'] else 'OFF'}",
                callback_data="toggle_auto"
            )],
            [InlineKeyboardButton(
                f"💰 Max per trade: {settings['max_position_sol']} SOL",
                callback_data="set_max"
            )],
            [InlineKeyboardButton(
                f"🎯 TP: {settings['take_profit_percent']}% / SL: {settings['stop_loss_percent']}%",
                callback_data="set_tp_sl"
            )],
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ *Settings*\n\nAdjust your trading parameters:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def toggle_auto_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle auto trading"""
        query = update.callback_query
        await query.answer()
        
        chat_id = update.effective_chat.id
        settings = db.get_user_settings(chat_id)
        new_status = 0 if settings['auto_trade'] else 1
        
        db.update_user_settings(chat_id, auto_trade=new_status)
        
        status_text = "ON" if new_status else "OFF"
        await query.edit_message_text(
            f"🤖 Auto trade turned {status_text}\n\n"
            f"When ON, bot will automatically buy top AI signals.",
            parse_mode='Markdown'
        )
        
        # Go back to settings
        await asyncio.sleep(1)
        await self.settings_callback(update, context)
    
    async def stop_all_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop all active positions"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("✅ YES, SELL ALL", callback_data="confirm_stop_all")],
            [InlineKeyboardButton("❌ NO", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚠️ *WARNING*\n\n"
            "This will sell ALL active positions at current market price.\n\n"
            "Are you sure?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def confirm_stop_all_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Execute sell all"""
        query = update.callback_query
        await query.answer()
        
        positions = db.get_active_positions(update.effective_chat.id)
        
        if not positions:
            await query.edit_message_text("No active positions to sell.")
            return
        
        await query.edit_message_text(f"🔄 Selling {len(positions)} positions...")
        
        sold = 0
        for pos in positions:
            success, msg, tx, pnl, pnl_pct = await trader.execute_sell(pos['id'], "Manual stop all")
            if success:
                sold += 1
                await context.bot.send_message(update.effective_chat.id, msg)
            await asyncio.sleep(0.5)
        
        await query.edit_message_text(f"✅ Sold {sold}/{len(positions)} positions")
    
    async def cancel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel action"""
        await self.start_command(update, context)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        print(f"Error: {context.error}")
        if update and update.effective_chat:
            await context.bot.send_message(
                update.effective_chat.id,
                "❌ An error occurred. Please try again."
            )
    
    def run(self):
        """Run the bot"""
        # Create application
        self.app = Application.builder().token(config.TELEGRAM_TOKEN).build()
        
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        
        # Callback handlers
        self.app.add_handler(CallbackQueryHandler(self.scan_trade_callback, pattern='^scan_trade$'))
        self.app.add_handler(CallbackQueryHandler(self.my_positions_callback, pattern='^my_positions$'))
        self.app.add_handler(CallbackQueryHandler(self.balance_callback, pattern='^balance$'))
        self.app.add_handler(CallbackQueryHandler(self.history_callback, pattern='^history$'))
        self.app.add_handler(CallbackQueryHandler(self.settings_callback, pattern='^settings$'))
        self.app.add_handler(CallbackQueryHandler(self.stop_all_callback, pattern='^stop_all$'))
        self.app.add_handler(CallbackQueryHandler(self.toggle_auto_callback, pattern='^toggle_auto$'))
        self.app.add_handler(CallbackQueryHandler(self.buy_callback, pattern='^buy_'))
        self.app.add_handler(CallbackQueryHandler(self.confirm_buy_callback, pattern='^confirm_'))
        self.app.add_handler(CallbackQueryHandler(self.sell_callback, pattern='^sell_'))
        self.app.add_handler(CallbackQueryHandler(self.confirm_stop_all_callback, pattern='^confirm_stop_all$'))
        self.app.add_handler(CallbackQueryHandler(self.cancel_callback, pattern='^cancel$'))
        self.app.add_handler(CallbackQueryHandler(self.start_command, pattern='^start$'))
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
        
        # Start position monitoring
        trader.start_monitoring(self.app.bot)
        
        # Run bot
        print("🤖 Bot started...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    bot = TradingBot()
    bot.run()