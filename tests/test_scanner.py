"""
Unit tests for ETF Scanner
"""

import unittest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.etf_scanner import ETFScanner
from src.telegram_bot import TelegramBot
from src.yahoo_fetcher import YahooETFfetcher

class TestETFScanner(unittest.TestCase):
    """Test cases for ETF Scanner"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot_token = "test_token"
        self.chat_id = "test_chat_id"
        self.config = {
            'TOP_N_ETF': 3,
            'MIN_VOLUME': 1000,
            'DATA_DIR': 'test_data',
            'LOGS_DIR': 'test_logs'
        }
        
    def test_scanner_initialization(self):
        """Test scanner initialization"""
        scanner = ETFScanner(self.bot_token, self.chat_id, self.config)
        self.assertIsNotNone(scanner)
        self.assertEqual(scanner.top_n, 3)
        self.assertEqual(scanner.min_volume, 1000)
    
    @patch('src.etf_scanner.YahooETFfetcher')
    @patch('src.etf_scanner.TelegramBot')
    def test_run_with_no_losers(self, mock_bot, mock_fetcher):
        """Test run when no losers found"""
        # Mock empty DataFrame
        mock_fetcher.return_value.get_top_losers.return_value = pd.DataFrame()
        
        scanner = ETFScanner(self.bot_token, self.chat_id, self.config)
        scanner.run(custom_symbols=["TEST.NS"])
        
        # Verify send_message was called
        mock_bot.return_value.send_message.assert_called_once()
    
    @patch('src.etf_scanner.YahooETFfetcher')
    @patch('src.etf_scanner.TelegramBot')
    def test_run_with_losers(self, mock_bot, mock_fetcher):
        """Test run when losers are found"""
        # Mock DataFrame with losers
        losers_df = pd.DataFrame({
            'symbol': ['TEST1', 'TEST2'],
            'pChange': [-5.0, -3.0],
            'ltp': [100, 200],
            'volume': [10000, 5000],
            'name': ['Test ETF 1', 'Test ETF 2']
        })
        mock_fetcher.return_value.get_top_losers.return_value = losers_df
        
        scanner = ETFScanner(self.bot_token, self.chat_id, self.config)
        scanner.run(custom_symbols=["TEST1.NS", "TEST2.NS"])
        
        # Verify send_message was called
        mock_bot.return_value.send_message.assert_called_once()
    
    def test_format_volume(self):
        """Test volume formatting"""
        bot = TelegramBot("test", "test")
        
        # Test thousands
        self.assertEqual(bot._format_volume(1500), "1.5K")
        
        # Test millions
        self.assertEqual(bot._format_volume(2500000), "2.5M")
        
        # Test regular numbers
        self.assertEqual(bot._format_volume(500), "500")

class TestTelegramBot(unittest.TestCase):
    """Test cases for Telegram Bot"""
    
    def setUp(self):
        self.bot = TelegramBot("test_token", "test_chat_id")
    
    def test_format_top_losers_empty(self):
        """Test formatting with empty DataFrame"""
        empty_df = pd.DataFrame()
        message = self.bot.format_top_losers(empty_df)
        self.assertIn("No ETFs", message)
    
    def test_format_top_losers_with_data(self):
        """Test formatting with data"""
        losers_df = pd.DataFrame({
            'symbol': ['TEST1'],
            'pChange': [-5.0],
            'ltp': [100],
            'volume': [10000],
            'name': ['Test ETF']
        })
        message = self.bot.format_top_losers(losers_df)
        self.assertIn("TEST1", message)
        self.assertIn("-5.00%", message)

class TestYahooFetcher(unittest.TestCase):
    """Test cases for Yahoo Finance fetcher"""
    
    def setUp(self):
        self.fetcher = YahooETFfetcher(rate_limit_delay=0)
    
    @patch('yfinance.Ticker')
    def test_fetch_single_etf_success(self, mock_ticker):
        """Test successful ETF data fetch"""
        # Mock the ticker response
        mock_instance = Mock()
        mock_instance.info = {
            'regularMarketPrice': 100,
            'regularMarketPreviousClose': 95,
            'regularMarketVolume': 5000,
            'longName': 'Test ETF'
        }
        mock_ticker.return_value = mock_instance
        
        result = self.fetcher._fetch_single_etf("TEST.NS")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['symbol'], 'TEST')
        self.assertAlmostEqual(result['pChange'], 5.26, places=1)
    
    @patch('yfinance.Ticker')
    def test_fetch_single_etf_failure(self, mock_ticker):
        """Test failed ETF data fetch"""
        mock_ticker.side_effect = Exception("API Error")
        
        result = self.fetcher._fetch_single_etf("TEST.NS")
        self.assertIsNone(result)
    
    def test_get_market_state(self):
        """Test market state detection"""
        # This test might need adjustment based on current time
        state = self.fetcher._get_market_state()
        self.assertIn(state, ["OPEN", "CLOSED"])

if __name__ == '__main__':
    unittest.main()
