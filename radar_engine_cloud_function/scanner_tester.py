# scanner_tester.py

import pandas as pd
import numpy as np
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Import our modules
import mock_data_generator
import historical_data_manager
import indicator_calculator
import trade_analyzer
import strategies
import data_manager

class ScannerTester:
    """
    Comprehensive testing framework for the radar scanner using mock data.
    """
    
    def __init__(self, use_real_data=True):
        self.generator = mock_data_generator.MockDataGenerator()
        self.historical_manager = historical_data_manager.HistoricalDataManager()
        self.use_real_data = use_real_data
        self.test_results = []
        self.alert_history = []
        
    def run_backtest(self, symbol: str, scenario: str = 'recent', days: int = 100) -> Dict:
        """
        Runs a complete backtest of the scanner on real or mock data.
        
        Args:
            symbol (str): Stock symbol to test
            scenario (str): Market scenario ('recent', 'BULL_MARKET', 'BEAR_MARKET', etc.)
            days (int): Number of days to simulate
            
        Returns:
            Dict: Backtest results with metrics and alerts
        """
        print(f"\n=== Running Backtest: {symbol} - {scenario} ===")
        
        # Get data based on preference
        if self.use_real_data and scenario == 'recent':
            print("📊 Using real historical data from Upstox...")
            historical_data = self.historical_manager.get_test_data(symbol, scenario, days)
        else:
            print("🎲 Using mock data for scenario testing...")
            historical_data = self.generator.generate_daily_candles(symbol, days=days, scenario=scenario)
        
        if historical_data.empty:
            return {"error": "Failed to generate mock data"}
        
        # Initialize data manager
        data_manager.initialize_history(symbol, historical_data)
        
        # Track alerts and performance
        alerts = []
        daily_returns = []
        
        # Simulate real-time scanning
        for i in range(50, len(historical_data)):  # Start from day 50 to have enough history
            current_data = historical_data.iloc[:i+1]
            
            # Calculate indicators
            indicators = indicator_calculator.calculate_indicators(current_data)
            
            # Check for trade setups
            setup_found, details = trade_analyzer.analyze_for_trade_setup(
                symbol, indicators, current_data
            )
            
            if setup_found:
                alert = {
                    'date': current_data.index[-1],
                    'symbol': symbol,
                    'indicators': indicators.copy(),
                    'details': details,
                    'price': current_data['close'].iloc[-1]
                }
                alerts.append(alert)
                print(f"ALERT: {symbol} on {alert['date'].strftime('%Y-%m-%d')} - {details}")
            
            # Calculate daily return for performance tracking
            if i > 0:
                daily_return = (current_data['close'].iloc[-1] / current_data['close'].iloc[-2]) - 1
                daily_returns.append(daily_return)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(daily_returns, alerts)
        
        result = {
            'symbol': symbol,
            'scenario': scenario,
            'total_days': len(historical_data),
            'alerts_generated': len(alerts),
            'performance_metrics': performance_metrics,
            'alerts': alerts
        }
        
        self.test_results.append(result)
        return result
    
    def test_alert_scenarios(self) -> Dict:
        """
        Tests specific alert scenarios to ensure the scanner can detect them.
        
        Returns:
            Dict: Results of alert scenario tests
        """
        print("\n=== Testing Alert Scenarios ===")
        
        alert_scenarios = {
            'RSI_OVERSOLD': {
                'symbol': 'RELIANCE',
                'expected_alert': 'RSI oversold condition'
            },
            'GOLDEN_CROSS': {
                'symbol': 'TCS',
                'expected_alert': 'Golden cross (EMA50 > EMA200)'
            },
            'VOLUME_SPIKE': {
                'symbol': 'HDFCBANK',
                'expected_alert': 'Volume spike detected'
            }
        }
        
        scenario_results = {}
        
        for scenario_name, config in alert_scenarios.items():
            print(f"\nTesting {scenario_name}...")
            
            # Generate alert-specific data
            alert_data = self.generator.generate_alert_scenario(
                config['symbol'], scenario_name
            )
            
            if alert_data.empty:
                scenario_results[scenario_name] = {'error': 'Failed to generate data'}
                continue
            
            # Initialize and test
            data_manager.initialize_history(config['symbol'], alert_data)
            
            # Get the last few days for testing
            test_data = alert_data.tail(10)
            alerts_found = []
            
            for i, (date, row) in enumerate(test_data.iterrows()):
                current_data = alert_data.iloc[:len(alert_data)-len(test_data)+i+1]
                indicators = indicator_calculator.calculate_indicators(current_data)
                
                setup_found, details = trade_analyzer.analyze_for_trade_setup(
                    config['symbol'], indicators, current_data
                )
                
                if setup_found:
                    alerts_found.append({
                        'date': date,
                        'details': details,
                        'indicators': indicators
                    })
            
            # Check if expected alert was found
            expected_found = any(
                config['expected_alert'].lower() in ' '.join(alert['details']).lower()
                for alert in alerts_found
            )
            
            scenario_results[scenario_name] = {
                'expected_alert': config['expected_alert'],
                'alerts_found': len(alerts_found),
                'expected_found': expected_found,
                'alert_details': alerts_found
            }
            
            print(f"  Expected alert found: {expected_found}")
            print(f"  Total alerts generated: {len(alerts_found)}")
        
        return scenario_results
    
    def fetch_real_data_for_testing(self, symbols: List[str], days: int = 100) -> Dict:
        """
        Fetches real historical data from Upstox for testing purposes.
        
        Args:
            symbols (List[str]): List of symbols to fetch data for
            days (int): Number of days to fetch
            
        Returns:
            Dict: Results of data fetching operation
        """
        print(f"\n=== Fetching Real Data for Testing ===")
        print(f"📊 Fetching {days} days of data for {len(symbols)} symbols...")
        
        results = self.historical_manager.fetch_multiple_symbols(symbols, days)
        
        summary = {
            'requested_symbols': len(symbols),
            'successful_fetches': len(results),
            'failed_fetches': len(symbols) - len(results),
            'symbols_with_data': list(results.keys()),
            'failed_symbols': [s for s in symbols if s not in results]
        }
        
        print(f"\n✅ Data Fetch Summary:")
        print(f"   Successfully fetched: {summary['successful_fetches']}/{summary['requested_symbols']}")
        print(f"   Failed: {summary['failed_fetches']}")
        
        if summary['failed_symbols']:
            print(f"   Failed symbols: {summary['failed_symbols']}")
        
        return summary
    
    def test_strategy_performance(self, symbols: List[str] = None) -> Dict:
        """
        Tests the performance of different strategies across various market conditions.
        
        Args:
            symbols (List[str]): List of symbols to test
            
        Returns:
            Dict: Strategy performance comparison
        """
        if symbols is None:
            symbols = ['RELIANCE', 'TCS', 'HDFCBANK']
        
        scenarios = ['BULL_MARKET', 'BEAR_MARKET', 'SIDEWAYS', 'VOLATILE']
        strategy_results = {}
        
        print("\n=== Testing Strategy Performance ===")
        
        for scenario in scenarios:
            print(f"\nTesting {scenario} scenario...")
            scenario_results = {}
            
            for symbol in symbols:
                result = self.run_backtest(symbol, scenario, days=100)
                scenario_results[symbol] = result
            
            strategy_results[scenario] = scenario_results
        
        return strategy_results
    
    def generate_test_report(self, output_file: str = None) -> str:
        """
        Generates a comprehensive test report.
        
        Args:
            output_file (str): Optional file to save the report
            
        Returns:
            str: Generated report
        """
        if not self.test_results:
            return "No test results available. Run tests first."
        
        report = []
        report.append("=" * 60)
        report.append("RADAR SCANNER TEST REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary statistics
        total_tests = len(self.test_results)
        total_alerts = sum(r['alerts_generated'] for r in self.test_results)
        
        report.append("SUMMARY STATISTICS:")
        report.append(f"  Total tests run: {total_tests}")
        report.append(f"  Total alerts generated: {total_alerts}")
        report.append(f"  Average alerts per test: {total_alerts/total_tests:.2f}")
        report.append("")
        
        # Detailed results
        report.append("DETAILED RESULTS:")
        report.append("-" * 40)
        
        for result in self.test_results:
            report.append(f"Symbol: {result['symbol']}")
            report.append(f"Scenario: {result['scenario']}")
            report.append(f"Alerts: {result['alerts_generated']}")
            
            if 'performance_metrics' in result:
                metrics = result['performance_metrics']
                report.append(f"  Total Return: {metrics.get('total_return', 0):.2%}")
                report.append(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
                report.append(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
            
            report.append("")
        
        # Alert analysis
        if self.alert_history:
            report.append("ALERT ANALYSIS:")
            report.append("-" * 40)
            
            alert_types = {}
            for alert in self.alert_history:
                alert_type = alert.get('type', 'Unknown')
                alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
            
            for alert_type, count in alert_types.items():
                report.append(f"  {alert_type}: {count}")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"Report saved to {output_file}")
        
        return report_text
    
    def _calculate_performance_metrics(self, daily_returns: List[float], alerts: List[Dict]) -> Dict:
        """
        Calculates performance metrics from daily returns and alerts.
        
        Args:
            daily_returns (List[float]): List of daily returns
            alerts (List[Dict]): List of alerts generated
            
        Returns:
            Dict: Performance metrics
        """
        if not daily_returns:
            return {}
        
        returns_array = np.array(daily_returns)
        
        metrics = {
            'total_return': (1 + returns_array).prod() - 1,
            'annualized_return': ((1 + returns_array).prod()) ** (252/len(returns_array)) - 1,
            'volatility': returns_array.std() * np.sqrt(252),
            'sharpe_ratio': (returns_array.mean() / returns_array.std()) * np.sqrt(252) if returns_array.std() > 0 else 0,
            'max_drawdown': self._calculate_max_drawdown(returns_array),
            'win_rate': (returns_array > 0).mean(),
            'alert_frequency': len(alerts) / len(returns_array) if returns_array.size > 0 else 0
        }
        
        return metrics
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """
        Calculates the maximum drawdown from a series of returns.
        
        Args:
            returns (np.ndarray): Array of returns
            
        Returns:
            float: Maximum drawdown as a percentage
        """
        cumulative = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def run_comprehensive_test(self, fetch_real_data=True) -> Dict:
        """
        Runs a comprehensive test suite including all test types.
        
        Args:
            fetch_real_data (bool): Whether to fetch real data for testing
            
        Returns:
            Dict: Complete test results
        """
        print("Starting comprehensive scanner test suite...")
        
        # Fetch real data if requested
        if fetch_real_data and self.use_real_data:
            print("\n📊 Fetching real historical data for testing...")
            real_symbols = [
                "NSE_EQ|INE002A01018",  # Reliance
                "NSE_EQ|INE019A01038",  # HDFC Bank
                "NSE_EQ|INE090A01021"   # ICICI Bank
            ]
            data_fetch_results = self.fetch_real_data_for_testing(real_symbols, days=100)
        else:
            data_fetch_results = None
        
        # Test alert scenarios
        alert_results = self.test_alert_scenarios()
        
        # Test strategy performance
        strategy_results = self.test_strategy_performance()
        
        # Generate report
        report = self.generate_test_report('test_reports/scanner_test_report.txt')
        
        comprehensive_results = {
            'data_fetch_results': data_fetch_results,
            'alert_scenarios': alert_results,
            'strategy_performance': strategy_results,
            'report': report,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save results to JSON
        os.makedirs('test_reports', exist_ok=True)
        with open('test_reports/comprehensive_results.json', 'w') as f:
            json.dump(comprehensive_results, f, indent=2, default=str)
        
        return comprehensive_results


# Example usage
if __name__ == "__main__":
    tester = ScannerTester()
    
    # Run comprehensive test
    results = tester.run_comprehensive_test()
    
    print("\nTest completed! Check test_reports/ directory for detailed results.")
    print(f"Alert scenario tests: {len(results['alert_scenarios'])} scenarios tested")
    print(f"Strategy performance tests: {len(results['strategy_performance'])} scenarios tested") 