import asyncio
from datetime import datetime
from typing import Dict, Optional
from database import db
from solana_client import solana_client
from groq_analyzer import groq_analyzer
from config import config

class Trader:
    def __init__(self):
        self.active_monitor_task = None
        self.is_running = False
    
    async def execute_buy(self, chat_id: int, token_mint: str, token_symbol: str, 
                          price: float, reason: str) -> bool:
        """Execute buy order"""
        try:
            # Get user settings
            settings = db.get_user_settings(chat_id)
            max_sol = settings.get('max_position_sol', config.MAX_POSITION_SOL)
            
            # Check balance
            balance = solana_client.get_balance()
            if balance < max_sol + 0.05:  # Leave 0.05 SOL for fees
                return False
            
            # Execute swap
            tx_sig = await solana_client.swap_to_token(token_mint, max_sol)
            
            if tx_sig:
                # Calculate amount received (simplified)
                amount = max_sol / price  # Approximate
                
                # Save position
                db.add_position(chat_id, token_mint, token_symbol, 
                              price, amount, max_sol)
                
                # Send notification
                notification = await groq_analyzer.generate_notification(
                    "BUY", token_symbol, price, reason
                )
                
                return True, notification, tx_sig
            
            return False, "Swap failed", None
            
        except Exception as e:
            print(f"Buy error: {e}")
            return False, str(e), None
    
    async def execute_sell(self, position_id: int, reason: str) -> bool:
        """Execute sell order for a position"""
        try:
            positions = db.get_active_positions()
            position = None
            for pos in positions:
                if pos['id'] == position_id:
                    position = pos
                    break
            
            if not position:
                return False, "Position not found"
            
            # Get current price
            current_price = await solana_client.get_token_price(position['token_mint'])
            
            if current_price <= 0:
                return False, "Cannot get price"
            
            # Execute swap to SOL
            tx_sig = await solana_client.swap_to_sol(
                position['token_mint'], 
                position['amount']
            )
            
            if tx_sig:
                # Close position in DB
                pnl, pnl_percent = db.close_position(position_id, current_price, reason)
                
                notification = await groq_analyzer.generate_notification(
                    "SELL", position['token_symbol'], current_price, 
                    f"{reason} | PnL: {pnl_percent:.2f}%"
                )
                
                return True, notification, tx_sig, pnl, pnl_percent
            
            return False, "Swap failed", None, 0, 0
            
        except Exception as e:
            print(f"Sell error: {e}")
            return False, str(e), None, 0, 0
    
    async def monitor_positions(self, bot):
        """Background task to monitor all active positions"""
        self.is_running = True
        
        while self.is_running:
            try:
                positions = db.get_active_positions()
                
                for position in positions:
                    current_price = await solana_client.get_token_price(position['token_mint'])
                    
                    if current_price <= 0:
                        continue
                    
                    # Calculate PnL
                    pnl_percent = ((current_price - position['buy_price']) / position['buy_price']) * 100
                    
                    # Check take profit
                    if pnl_percent >= position['take_profit_percent']:
                        success, msg, tx, pnl, pnl_pct = await self.execute_sell(
                            position['id'], f"Take Profit ({pnl_percent:.2f}%)"
                        )
                        if success and bot:
                            await bot.send_message(position['chat_id'], msg)
                    
                    # Check stop loss
                    elif pnl_percent <= -position['stop_loss_percent']:
                        success, msg, tx, pnl, pnl_pct = await self.execute_sell(
                            position['id'], f"Stop Loss ({pnl_percent:.2f}%)"
                        )
                        if success and bot:
                            await bot.send_message(position['chat_id'], msg)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(5)
    
    def start_monitoring(self, bot):
        """Start background monitoring"""
        if self.active_monitor_task is None:
            self.active_monitor_task = asyncio.create_task(self.monitor_positions(bot))
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.is_running = False
        if self.active_monitor_task:
            self.active_monitor_task.cancel()

trader = Trader()