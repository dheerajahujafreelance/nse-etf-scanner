"""
Comprehensive tests for Yahoo Finance fetcher
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.yahoo_fetcher import YahooETFfetcher

class TestYahooFetcherDetailed(unittest.TestCase):
    """Detailed test cases for Yahoo Finance fetcher"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.fetcher = YahooETFfetcher(rate_limit_delay=0)
    
    @patch('yfinance.Ticker')
    def test_fetch_etf_data_multiple_symbols(self, mock_ticker):
        """Test fetching data for multiple ETFs"""
        # Create mock responses for multiple symbols
        mock_responses = {
            'ETF1.NS': {
                'info': {
                    'regularMarketPrice': 100,
                    'regularMarketPreviousClose': 98,
                    'regularMarketVolume': 10000,
                    'longName': 'ETF One'
                }
            },
            'ETF2.NS': {
                'info': {
                    'regularMarketPrice': 200,
                    'regularMarketPreviousClose': 195,
                    'regularMarketVolume': 5000,
                    'longName': 'ETF Two'
                }
            }
        }
        
        def mock_ticker_side_effect(symbol):
            mock = MagicMock()
            mock.info = mock_responses[symbol]['info']
            return mock
        
        mock_ticker.side_effect = mock_ticker_side_effect
        
        symbols = ['ETF1.NS', 'ETF2.NS']
        df = self.fetcher.fetch_etf_data(symbols)
        
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 2)
        self.assertIn('symbol', df.columns)
        self.assertIn('pChange', df.columns)
    
    @patch('yfinance.Ticker')
    def test_fetch_with_invalid_symbol(self, mock_ticker):
        """Test handling of invalid symbols"""
        # Mock an exception for invalid symbol
        mock_ticker.side_effect = Exception("Invalid symbol")
        
        symbols = ['INVALID.NS']
        df = self.fetcher.fetch_etf_data(symbols)
        
        # Should return empty DataFrame or skip invalid
        self.assertTrue(df.empty or len(df) == 0)
    
    def test_get_top_losers_sorting(self):
        """Test that top losers are sorted correctly (most negative first)"""
        # Create test data
        test_data = pd.DataFrame({
            'symbol': ['ETF1', 'ETF2', 'ETF3', 'ETF4', 'ETF5'],
            'pChange': [-1.0, -5.0, -2.0, -0.5, -3.0],
            'ltp': [100, 95, 98, 102, 97],
            'volume': [1000, 5000, 2000, 800, 3000],
            'name': ['ETF 1', 'ETF 2', 'ETF 3', 'ETF 4', 'ETF 5']
        })
        
        # Mock the fetch method
        with patch.object(self.fetcher, 'fetch_etf_data', return_value=test_data):
            result = self.fetcher.get_top_losers(['ETF1.NS', 'ETF2.NS', 'ETF3.NS', 'ETF4.NS', 'ETF5.NS'], top_n=3)
            
            # Should be sorted by pChange ascending (most negative first)
            expected_order = ['ETF2', 'ETF5', 'ETF3']
            actual_order = result['symbol'].tolist()
            
            self.assertEqual(actual_order, expected_order)
            self.assertEqual(result.iloc[0]['pChange'], -5.0)  # Most negative first
            self.assertEqual(result.iloc[2]['pChange'], -2.0)  # Third most negative
    
    def test_filter_by_min_volume(self):
        """Test volume filtering"""
        test_data = pd.DataFrame({
            'symbol': ['ETF1', 'ETF2', 'ETF3'],
            'pChange': [-1.0, -2.0, -3.0],
            'ltp': [100, 95, 90],
            'volume': [500, 5000, 10000],
            'name': ['ETF 1', 'ETF 2', 'ETF 3']
        })
        
        with patch.object(self.fetcher, 'fetch_etf_data', return_value=test_data):
            # Filter with min_volume=1000
            result = self.fetcher.get_top_losers(['ETF1.NS', 'ETF2.NS', 'ETF3.NS'], 
                                                 top_n=5, min_volume=1000)
            
            # Should exclude ETF1 (volume 500)
            self.assertEqual(len(result), 2)
            self.assertNotIn('ETF1', result['symbol'].tolist())
    
    @patch('yfinance.Ticker')
    def test_calculate_percentage_change(self, mock_ticker):
        """Test percentage change calculation"""
        mock_instance = Mock()
        mock_instance.info = {
            'regularMarketPrice': 105,
            'regularMarketPreviousClose': 100,
            'regularMarketVolume': 1000
        }
        mock_ticker.return_value = mock_instance
        
        result = self.fetcher._fetch_single_etf("TEST.NS")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['pChange'], 5.0)
    
    @patch('yfinance.Ticker')
    def test_handle_missing_previous_close(self, mock_ticker):
        """Test handling when previous close is missing"""
        mock_instance = Mock()
        mock_instance.info = {
            'regularMarketPrice': 105,
            'regularMarketPreviousClose': None,
            'regularMarketVolume': 1000
        }
        mock_ticker.return_value = mock_instance
        
        # Mock fast_info as fallback
        mock_instance.fast_info.last_price = 105
        mock_instance.fast_info.previous_close = 100
        
        result = self.fetcher._fetch_single_etf("TEST.NS")
        
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['pChange'], 5.0, places=1)
    
    def test_market_state_indicator(self):
        """Test market state detection logic"""
        # This test should work regardless of actual time
        state = self.fetcher._get_market_state()
        self.assertIsInstance(state, str)
        self.assertIn(state, ["OPEN", "CLOSED"])

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        self.fetcher = YahooETFfetcher()
    
    def test_empty_symbol_list(self):
        """Test with empty symbol list"""
        df = self.fetcher.fetch_etf_data([])
        self.assertTrue(df.empty)
    
    def test_none_symbol_list(self):
        """Test with None as symbol list"""
        with self.assertRaises(Exception):
            self.fetcher.fetch_etf_data(None)
    
    def test_rate_limit_delay(self):
        """Test rate limiting functionality"""
        fetcher = YahooETFfetcher(rate_limit_delay=0.5)
        self.assertEqual(fetcher.rate_limit_delay, 0.5)

if __name__ == '__main__':
    # Run with coverage report
    unittest.main(argv=[''], verbosity=2, exit=False)
