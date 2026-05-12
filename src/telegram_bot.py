"""
Telegram bot for sending ETF alerts
"""

import requests
import logging
from typing import Optional
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class TelegramBot:
    """Handle Telegram messaging"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.ist = pytz.timezone('Asia/Kolkata')
    
    def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """Send message to Telegram channel"""
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured")
            print(message)  # Print to console for debugging
            return False
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Message sent to Telegram successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def format_top_losers(self, losers_df, market_state: str = None) -> str:
        """Format top losers for Telegram message"""
        
        if losers_df.empty:
            return "📊 No ETFs with negative change found today.\n\nMarket might be closed or all ETFs are in the green! 🟢"
        
        current_time = datetime.now(self.ist)
        time_str = current_time.strftime('%I:%M %p')
        date_str = current_time.strftime('%d %b %Y')
        
        # Determine emoji based on market state
        market_emoji = "🟢" if market_state == "OPEN" else "🔴"
        
        message = f"📉 *TOP {len(losers_df)} LOSERS TODAY*\n"
        message += f"{market_emoji} {market_state if market_state else 'MARKET'}  |  🕐 {time_str}\n"
        message += f"📅 {date_str}\n"
        message += "─" * 30 + "\n\n"
        
        # Add ranking with severity indicators
        for idx, (_, row) in enumerate(losers_df.iterrows(), 1):
            # Determine severity emoji
            if row['pChange'] < -3:
                severity = "💀🔴"  # Extreme loss
            elif row['pChange'] < -1.5:
                severity = "⚠️🟠"  # Significant loss
            else:
                severity = "📉🟡"   # Mild loss
            
            message += f"{severity} *{idx}. {row['symbol']}*\n"
            message += f"   📉 `{row['pChange']:+.2f}%`  |  💰 ₹{row['ltp']:,.2f}\n"
            message += f"   📊 Vol: {self._format_volume(row['volume'])}\n"
            
            # Add name if available and not too long
            if 'name' in row and len(row['name']) < 40:
                message += f"   📝 {row['name'][:35]}\n"
            
            message += "\n"
        
        # Add market summary
        if len(losers_df) > 0:
            avg_loss = losers_df['pChange'].mean()
            max_loss = losers_df['pChange'].min()
            worst_etf = losers_df.iloc[0]['symbol']
            
            message += "─" * 30 + "\n"
            message += f"📊 *Market Summary*\n"
            message += f"   💀 Worst: {worst_etf} ({max_loss:.2f}%)\n"
            message += f"   📉 Avg Loss: {avg_loss:.2f}%\n"
        
        return message
    
    def _format_volume(self, volume: int) -> str:
        """Format volume with K/M/B suffixes"""
        if volume >= 1_000_000:
            return f"{volume/1_000_000:.1f}M"
        elif volume >= 1_000:
            return f"{volume/1_000:.1f}K"
        else:
            return str(volume)
