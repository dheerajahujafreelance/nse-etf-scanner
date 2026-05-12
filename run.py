#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.etf_scanner import ETFScanner

def main():
    load_dotenv()
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Error: Missing Telegram credentials in .env file")
        sys.exit(1)
    
    config = {
        'TOP_N_ETF': int(os.getenv('TOP_N_ETF', 5)),
        'MIN_VOLUME': int(os.getenv('MIN_VOLUME', 1000))
    }
    
    scanner = ETFScanner(bot_token, chat_id, config)
    scanner.run()

if __name__ == "__main__":
    main()
