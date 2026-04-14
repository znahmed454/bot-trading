import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class Database:
    def __init__(self, db_path="trading_bot.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_tables()
    
    def _init_tables(self):
        # Active positions
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                token_mint TEXT,
                token_symbol TEXT,
                buy_price REAL,
                amount REAL,
                sol_spent REAL,
                buy_time TIMESTAMP,
                take_profit REAL,
                stop_loss REAL,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Trade history
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                token_mint TEXT,
                token_symbol TEXT,
                buy_price REAL,
                sell_price REAL,
                amount REAL,
                pnl REAL,
                pnl_percent REAL,
                buy_time TIMESTAMP,
                sell_time TIMESTAMP,
                reason TEXT
            )
        ''')
        
        # AI signals
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_mint TEXT,
                token_symbol TEXT,
                decision TEXT,
                confidence REAL,
                target_price REAL,
                reason TEXT,
                timestamp TIMESTAMP
            )
        ''')
        
        # User settings
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                chat_id INTEGER PRIMARY KEY,
                auto_trade INTEGER DEFAULT 0,
                max_position_sol REAL DEFAULT 0.5,
                take_profit_percent REAL DEFAULT 15,
                stop_loss_percent REAL DEFAULT 10
            )
        ''')
        
        self.conn.commit()
    
    def add_position(self, chat_id: int, token_mint: str, token_symbol: str, 
                     buy_price: float, amount: float, sol_spent: float):
        take_profit = buy_price * (1 + config.TAKE_PROFIT_PERCENT)
        stop_loss = buy_price * (1 - config.STOP_LOSS_PERCENT)
        
        self.cursor.execute('''
            INSERT INTO active_positions 
            (chat_id, token_mint, token_symbol, buy_price, amount, sol_spent, 
             buy_time, take_profit, stop_loss)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (chat_id, token_mint, token_symbol, buy_price, amount, sol_spent,
              datetime.now(), take_profit, stop_loss))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_active_positions(self, chat_id: int = None) -> List[Dict]:
        if chat_id:
            self.cursor.execute('SELECT * FROM active_positions WHERE chat_id = ? AND status = "active"', (chat_id,))
        else:
            self.cursor.execute('SELECT * FROM active_positions WHERE status = "active"')
        
        rows = self.cursor.fetchall()
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    
    def close_position(self, position_id: int, sell_price: float, reason: str):
        # Get position details
        self.cursor.execute('SELECT * FROM active_positions WHERE id = ?', (position_id,))
        pos = self.cursor.fetchone()
        if not pos:
            return
        
        columns = [desc[0] for desc in self.cursor.description]
        pos_dict = dict(zip(columns, pos))
        
        # Calculate PnL
        pnl = (sell_price - pos_dict['buy_price']) * pos_dict['amount']
        pnl_percent = ((sell_price - pos_dict['buy_price']) / pos_dict['buy_price']) * 100
        
        # Move to history
        self.cursor.execute('''
            INSERT INTO trade_history 
            (chat_id, token_mint, token_symbol, buy_price, sell_price, amount, 
             pnl, pnl_percent, buy_time, sell_time, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (pos_dict['chat_id'], pos_dict['token_mint'], pos_dict['token_symbol'],
              pos_dict['buy_price'], sell_price, pos_dict['amount'],
              pnl, pnl_percent, pos_dict['buy_time'], datetime.now(), reason))
        
        # Delete from active
        self.cursor.execute('UPDATE active_positions SET status = "closed" WHERE id = ?', (position_id,))
        self.conn.commit()
        
        return pnl, pnl_percent
    
    def save_ai_signal(self, token_mint: str, token_symbol: str, decision: str,
                       confidence: float, target_price: float, reason: str):
        self.cursor.execute('''
            INSERT INTO ai_signals (token_mint, token_symbol, decision, confidence, 
                                    target_price, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (token_mint, token_symbol, decision, confidence, target_price, reason, datetime.now()))
        self.conn.commit()
    
    def get_user_settings(self, chat_id: int):
        self.cursor.execute('SELECT * FROM user_settings WHERE chat_id = ?', (chat_id,))
        row = self.cursor.fetchone()
        if not row:
            # Default settings
            self.cursor.execute('''
                INSERT INTO user_settings (chat_id, auto_trade, max_position_sol, 
                                          take_profit_percent, stop_loss_percent)
                VALUES (?, 0, 0.5, 15, 10)
            ''', (chat_id,))
            self.conn.commit()
            return {'auto_trade': 0, 'max_position_sol': 0.5, 
                    'take_profit_percent': 15, 'stop_loss_percent': 10}
        
        columns = [desc[0] for desc in self.cursor.description]
        return dict(zip(columns, row))
    
    def update_user_settings(self, chat_id: int, **kwargs):
        for key, value in kwargs.items():
            self.cursor.execute(f'UPDATE user_settings SET {key} = ? WHERE chat_id = ?', (value, chat_id))
        self.conn.commit()
    
    def close(self):
        self.conn.close()

from config import config
db = Database()