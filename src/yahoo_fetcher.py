"""
Yahoo Finance data fetcher for ETFs
"""

import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import logging
from typing import List, Dict, Optional
import pytz

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YahooETFfetcher:
    """Fetch ETF data from Yahoo Finance"""
    
    def __init__(self, rate_limit_delay: float = 0.1):
        self.rate_limit_delay = rate_limit_delay
        self.ist = pytz.timezone('Asia/Kolkata')
    
    def fetch_etf_data(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetch live data for multiple ETFs
        
        Args:
            symbols: List of ETF symbols with .NS suffix
            
        Returns:
            DataFrame with ETF data
        """
        results = []
        
        logger.info(f"Fetching data for {len(symbols)} symbols...")
        
        for symbol in symbols:
            try:
                data = self._fetch_single_etf(symbol)
                if data:
                    results.append(data)
                time.sleep(self.rate_limit_delay)
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                continue
        
        df = pd.DataFrame(results)
        if not df.empty:
            logger.info(f"Successfully fetched {len(df)} symbols")
        
        return df
    
    def _fetch_single_etf(self, symbol: str) -> Optional[Dict]:
        """Fetch data for a single ETF"""
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Try to get current info
            info = ticker.info
            
            # Get current price
            current_price = info.get('regularMarketPrice', 
                                    info.get('currentPrice', 
                                    info.get('navPrice', None)))
            
            # Get previous close
            previous_close = info.get('regularMarketPreviousClose',
                                     info.get('previousClose', None))
            
            # Calculate percentage change
            if current_price and previous_close and previous_close > 0:
                pct_change = ((current_price - previous_close) / previous_close) * 100
            else:
                # Try fast_info as fallback
                try:
                    fast_info = ticker.fast_info
                    current_price = fast_info.last_price
                    previous_close = fast_info.previous_close
                    pct_change = ((current_price - previous_close) / previous_close) * 100 if previous_close else 0
                except:
                    pct_change = 0
            
            # Get additional data
            volume = info.get('regularMarketVolume', 0)
            name = info.get('longName', info.get('shortName', symbol))
            
            # Get market state
            market_state = self._get_market_state()
            
            return {
                'symbol': symbol.replace('.NS', ''),
                'name': name[:50] if name else symbol,
                'ltp': round(current_price, 2) if current_price else 0,
                'pChange': round(pct_change, 2),
                'volume': volume,
                'timestamp': datetime.now(self.ist),
                'market_state': market_state
            }
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
            return None
    
    def _get_market_state(self) -> str:
        """Determine market state based on time"""
        now = datetime.now(self.ist)
        current_time = now.time()
        
        # Indian market hours: 9:15 AM to 3:30 PM IST
        market_open = current_time.hour >= 9 and current_time.minute >= 15
        market_close = current_time.hour < 15 or (current_time.hour == 15 and current_time.minute <= 30)
        
        if market_open and market_close:
            return "OPEN"
        else:
            return "CLOSED"
    
    def get_top_losers(self, symbols: List[str], top_n: int = 5, min_volume: int = 0) -> pd.DataFrame:
        """
        Get top losing ETFs sorted from highest loss to lowest
        
        Args:
            symbols: List of ETF symbols
            top_n: Number of top losers to return
            min_volume: Minimum volume filter
            
        Returns:
            DataFrame with top losers
        """
        df = self.fetch_etf_data(symbols)
        
        if df.empty:
            return pd.DataFrame()
        
        # Filter valid data
        df_valid = df[(df['ltp'] > 0) & (df['volume'] >= min_volume)]
        
        if df_valid.empty:
            logger.warning("No valid data after filtering")
            return pd.DataFrame()
        
        # Filter negative movers
        losers = df_valid[df_valid['pChange'] < 0].copy()
        
        if losers.empty:
            logger.info("No losing ETFs found today")
            return pd.DataFrame()
        
        # Sort from highest loss to lowest loss (most negative to least negative)
        losers_sorted = losers.sort_values(by='pChange', ascending=True)
        
        # Return top N losers
        return losers_sorted.head(top_n)
