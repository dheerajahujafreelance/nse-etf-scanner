"""
Main ETF scanner module
"""

import logging
import pandas as pd
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import pytz

from .yahoo_fetcher import YahooETFfetcher
from .telegram_bot import TelegramBot
from .utils import load_etf_symbols, save_log, setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class ETFScanner:
    """Main ETF scanner orchestrator"""
    
    def __init__(self, bot_token: str, chat_id: str, config: dict = None):
        self.bot = TelegramBot(bot_token, chat_id)
        self.fetcher = YahooETFfetcher()
        self.config = config or {}
        self.ist = pytz.timezone('Asia/Kolkata')
        
        # Load configuration
        self.top_n = self.config.get('TOP_N_ETF', 5)
        self.min_volume = self.config.get('MIN_VOLUME', 1000)
        self.data_dir = Path(self.config.get('DATA_DIR', 'data'))
        self.logs_dir = Path(self.config.get('LOGS_DIR', 'logs'))
        
        # Create directories
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    def run(self, custom_symbols: Optional[List[str]] = None):
        """Run the ETF scanner"""
        
        logger.info("="*50)
        logger.info("Starting ETF Scanner")
        logger.info(f"Time: {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info("="*50)
        
        try:
            # Load ETF symbols
            if custom_symbols:
                symbols = custom_symbols
                logger.info(f"Using {len(symbols)} custom symbols")
            else:
                symbols_file = self.data_dir / 'etf_symbols.csv'
                symbols = load_etf_symbols(symbols_file)
            
            if not symbols:
                error_msg = "No ETF symbols loaded. Please check your CSV file."
                logger.error(error_msg)
                self.bot.send_message(f"❌ *Error*\n\n{error_msg}")
                return
            
            # Fetch and analyze data
            top_losers = self.fetcher.get_top_losers(
                symbols, 
                top_n=self.top_n, 
                min_volume=self.min_volume
            )
            
            # Get market state
            market_state = self.fetcher._get_market_state() if hasattr(self.fetcher, '_get_market_state') else None
            
            # Format and send message
            if not top_losers.empty:
                message = self.bot.format_top_losers(top_losers, market_state)
                self.bot.send_message(message)
                
                # Save results to CSV
                self._save_results(top_losers)
            else:
                message = "📊 *ETF Scanner Update*\n\n"
                message += f"🕐 {datetime.now(self.ist).strftime('%I:%M %p')}\n"
                message += "No losing ETFs found at this time.\n"
                message += "All ETFs are either up or stable! 🟢"
                self.bot.send_message(message)
            
            # Save log
            save_log(self.logs_dir, "scanner_run", {
                'timestamp': datetime.now(self.ist).isoformat(),
                'symbols_checked': len(symbols),
                'losers_found': len(top_losers) if not top_losers.empty else 0,
                'top_n': self.top_n
            })
            
            logger.info("Scanner completed successfully")
            
        except Exception as e:
            error_msg = f"❌ *Scanner Error*\n\n```\n{str(e)}\n```"
            logger.error(f"Scanner failed: {e}", exc_info=True)
            self.bot.send_message(error_msg)
    
    def _save_results(self, results_df: pd.DataFrame):
        """Save scan results to CSV"""
        
        timestamp = datetime.now(self.ist).strftime('%Y%m%d_%H%M%S')
        output_file = self.data_dir / f'scan_results_{timestamp}.csv'
        
        results_df.to_csv(output_file, index=False)
        logger.info(f"Results saved to {output_file}")
