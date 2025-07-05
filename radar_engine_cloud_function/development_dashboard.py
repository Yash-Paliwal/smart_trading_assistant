# development_dashboard.py

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import json
import os
from datetime import datetime
import pandas as pd

# Import our modules
import mock_data_generator
import historical_data_manager
import scanner_tester
import data_manager
import indicator_calculator
import trade_analyzer

class DevelopmentDashboard:
    """
    Interactive dashboard for developing and testing the radar scanner.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Radar Scanner Development Dashboard")
        self.root.geometry("1200x800")
        
        # Initialize components
        self.generator = mock_data_generator.MockDataGenerator()
        self.historical_manager = historical_data_manager.HistoricalDataManager()
        self.tester = scanner_tester.ScannerTester(use_real_data=True)
        self.is_simulation_running = False
        self.simulation_thread = None
        
        # Data storage
        self.current_data = {}
        self.alert_history = []
        self.test_results = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Sets up the user interface."""
        # Create main notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tab 1: Real-time Simulation
        self.setup_simulation_tab(notebook)
        
        # Tab 2: Testing Framework
        self.setup_testing_tab(notebook)
        
        # Tab 3: Data Generator
        self.setup_data_generator_tab(notebook)
        
        # Tab 4: Alert History
        self.setup_alert_history_tab(notebook)
        
        # Tab 5: Real Data Management
        self.setup_real_data_tab(notebook)
        
        # Tab 6: Performance Analytics
        self.setup_analytics_tab(notebook)
    
    def setup_simulation_tab(self, notebook):
        """Sets up the real-time simulation tab."""
        simulation_frame = ttk.Frame(notebook)
        notebook.add(simulation_frame, text="Real-time Simulation")
        
        # Control panel
        control_frame = ttk.LabelFrame(simulation_frame, text="Simulation Controls", padding=10)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Symbol selection
        ttk.Label(control_frame, text="Symbol:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.symbol_var = tk.StringVar(value="RELIANCE")
        symbol_combo = ttk.Combobox(control_frame, textvariable=self.symbol_var, 
                                   values=list(self.generator.base_prices.keys()))
        symbol_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Scenario selection
        ttk.Label(control_frame, text="Scenario:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.scenario_var = tk.StringVar(value="SIDEWAYS")
        scenario_combo = ttk.Combobox(control_frame, textvariable=self.scenario_var,
                                    values=['BULL_MARKET', 'BEAR_MARKET', 'SIDEWAYS', 'VOLATILE'])
        scenario_combo.grid(row=0, column=3, sticky='ew', padx=5, pady=5)
        
        # Speed control
        ttk.Label(control_frame, text="Speed (sec):").grid(row=0, column=4, sticky='w', padx=5, pady=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_spin = ttk.Spinbox(control_frame, from_=0.1, to=10.0, increment=0.1, 
                                textvariable=self.speed_var, width=10)
        speed_spin.grid(row=0, column=5, sticky='ew', padx=5, pady=5)
        
        # Start/Stop button
        self.sim_button = ttk.Button(control_frame, text="Start Simulation", 
                                   command=self.toggle_simulation)
        self.sim_button.grid(row=0, column=6, padx=10, pady=5)
        
        # Configure grid weights
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(3, weight=1)
        
        # Real-time display
        display_frame = ttk.LabelFrame(simulation_frame, text="Real-time Data", padding=10)
        display_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create treeview for current data
        columns = ('Symbol', 'Price', 'RSI', 'EMA50', 'EMA200', 'Volume', 'Status')
        self.data_tree = ttk.Treeview(display_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=100)
        
        self.data_tree.pack(fill='both', expand=True)
        
        # Alert log
        alert_frame = ttk.LabelFrame(simulation_frame, text="Alert Log", padding=10)
        alert_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.alert_text = scrolledtext.ScrolledText(alert_frame, height=8)
        self.alert_text.pack(fill='both', expand=True)
    
    def setup_testing_tab(self, notebook):
        """Sets up the testing framework tab."""
        testing_frame = ttk.Frame(notebook)
        notebook.add(testing_frame, text="Testing Framework")
        
        # Test controls
        test_control_frame = ttk.LabelFrame(testing_frame, text="Test Controls", padding=10)
        test_control_frame.pack(fill='x', padx=10, pady=5)
        
        # Test type selection
        ttk.Label(test_control_frame, text="Test Type:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.test_type_var = tk.StringVar(value="alert_scenarios")
        test_combo = ttk.Combobox(test_control_frame, textvariable=self.test_type_var,
                                 values=['alert_scenarios', 'strategy_performance', 'comprehensive'])
        test_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Run test button
        test_button = ttk.Button(test_control_frame, text="Run Test", command=self.run_test)
        test_button.grid(row=0, column=2, padx=10, pady=5)
        
        # Generate report button
        report_button = ttk.Button(test_control_frame, text="Generate Report", command=self.generate_report)
        report_button.grid(row=0, column=3, padx=10, pady=5)
        
        test_control_frame.columnconfigure(1, weight=1)
        
        # Test results
        results_frame = ttk.LabelFrame(testing_frame, text="Test Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.results_text = scrolledtext.ScrolledText(results_frame)
        self.results_text.pack(fill='both', expand=True)
    
    def setup_data_generator_tab(self, notebook):
        """Sets up the data generator tab."""
        generator_frame = ttk.Frame(notebook)
        notebook.add(generator_frame, text="Data Generator")
        
        # Generator controls
        gen_control_frame = ttk.LabelFrame(generator_frame, text="Data Generation", padding=10)
        gen_control_frame.pack(fill='x', padx=10, pady=5)
        
        # Symbol selection
        ttk.Label(gen_control_frame, text="Symbol:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.gen_symbol_var = tk.StringVar(value="RELIANCE")
        gen_symbol_combo = ttk.Combobox(gen_control_frame, textvariable=self.gen_symbol_var,
                                      values=list(self.generator.base_prices.keys()))
        gen_symbol_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        # Days
        ttk.Label(gen_control_frame, text="Days:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.days_var = tk.IntVar(value=100)
        days_spin = ttk.Spinbox(gen_control_frame, from_=10, to=500, textvariable=self.days_var, width=10)
        days_spin.grid(row=0, column=3, sticky='ew', padx=5, pady=5)
        
        # Scenario
        ttk.Label(gen_control_frame, text="Scenario:").grid(row=0, column=4, sticky='w', padx=5, pady=5)
        self.gen_scenario_var = tk.StringVar(value="SIDEWAYS")
        gen_scenario_combo = ttk.Combobox(gen_control_frame, textvariable=self.gen_scenario_var,
                                        values=['BULL_MARKET', 'BEAR_MARKET', 'SIDEWAYS', 'VOLATILE'])
        gen_scenario_combo.grid(row=0, column=5, sticky='ew', padx=5, pady=5)
        
        # Generate button
        gen_button = ttk.Button(gen_control_frame, text="Generate Data", command=self.generate_data)
        gen_button.grid(row=0, column=6, padx=10, pady=5)
        
        gen_control_frame.columnconfigure(1, weight=1)
        gen_control_frame.columnconfigure(5, weight=1)
        
        # Data preview
        preview_frame = ttk.LabelFrame(generator_frame, text="Data Preview", padding=10)
        preview_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame)
        self.preview_text.pack(fill='both', expand=True)
    
    def setup_real_data_tab(self, notebook):
        """Sets up the real data management tab."""
        real_data_frame = ttk.Frame(notebook)
        notebook.add(real_data_frame, text="Real Data Management")
        
        # Data fetch controls
        fetch_control_frame = ttk.LabelFrame(real_data_frame, text="Fetch Real Data", padding=10)
        fetch_control_frame.pack(fill='x', padx=10, pady=5)
        
        # Symbol list
        ttk.Label(fetch_control_frame, text="Symbols:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.symbols_text = tk.Text(fetch_control_frame, height=4, width=50)
        self.symbols_text.insert('1.0', "NSE_EQ|INE002A01018\nNSE_EQ|INE019A01038\nNSE_EQ|INE090A01021")
        self.symbols_text.grid(row=0, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
        
        # Days
        ttk.Label(fetch_control_frame, text="Days:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.real_days_var = tk.IntVar(value=100)
        real_days_spin = ttk.Spinbox(fetch_control_frame, from_=10, to=500, textvariable=self.real_days_var, width=10)
        real_days_spin.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        # Fetch button
        fetch_button = ttk.Button(fetch_control_frame, text="Fetch Data", command=self.fetch_real_data)
        fetch_button.grid(row=1, column=2, padx=10, pady=5)
        
        fetch_control_frame.columnconfigure(1, weight=1)
        
        # Data status
        status_frame = ttk.LabelFrame(real_data_frame, text="Data Status", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=6)
        self.status_text.pack(fill='both', expand=True)
        
        # Cache management
        cache_frame = ttk.LabelFrame(real_data_frame, text="Cache Management", padding=10)
        cache_frame.pack(fill='x', padx=10, pady=5)
        
        cache_button = ttk.Button(cache_frame, text="Clean Old Data", command=self.cleanup_cache)
        cache_button.pack(side='left', padx=5, pady=5)
        
        refresh_button = ttk.Button(cache_frame, text="Refresh Status", command=self.refresh_data_status)
        refresh_button.pack(side='left', padx=5, pady=5)
    
    def setup_alert_history_tab(self, notebook):
        """Sets up the alert history tab."""
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="Alert History")
        
        # Alert history treeview
        columns = ('Timestamp', 'Symbol', 'Alert Type', 'Price', 'Details')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=150)
        
        self.history_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Clear history button
        clear_button = ttk.Button(history_frame, text="Clear History", command=self.clear_history)
        clear_button.pack(pady=5)
    
    def setup_analytics_tab(self, notebook):
        """Sets up the performance analytics tab."""
        analytics_frame = ttk.Frame(notebook)
        notebook.add(analytics_frame, text="Performance Analytics")
        
        # Analytics controls
        analytics_control_frame = ttk.LabelFrame(analytics_frame, text="Analytics", padding=10)
        analytics_control_frame.pack(fill='x', padx=10, pady=5)
        
        # Metrics display
        metrics_frame = ttk.LabelFrame(analytics_frame, text="Performance Metrics", padding=10)
        metrics_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.metrics_text = scrolledtext.ScrolledText(metrics_frame)
        self.metrics_text.pack(fill='both', expand=True)
    
    def toggle_simulation(self):
        """Toggles the real-time simulation on/off."""
        if not self.is_simulation_running:
            self.start_simulation()
        else:
            self.stop_simulation()
    
    def start_simulation(self):
        """Starts the real-time simulation."""
        self.is_simulation_running = True
        self.sim_button.config(text="Stop Simulation")
        
        # Start simulation in a separate thread
        self.simulation_thread = threading.Thread(target=self.run_simulation)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
    
    def stop_simulation(self):
        """Stops the real-time simulation."""
        self.is_simulation_running = False
        self.sim_button.config(text="Start Simulation")
    
    def run_simulation(self):
        """Runs the real-time simulation loop."""
        symbol = self.symbol_var.get()
        scenario = self.scenario_var.get()
        speed = self.speed_var.get()
        
        # Generate initial data
        data = self.generator.generate_daily_candles(symbol, days=100, scenario=scenario)
        data_manager.initialize_history(symbol, data)
        
        # Start from day 50 to have enough history for indicators
        current_index = 50
        
        while self.is_simulation_running and current_index < len(data):
            # Get current data slice
            current_data = data.iloc[:current_index + 1]
            
            # Calculate indicators
            indicators = indicator_calculator.calculate_indicators(current_data)
            
            # Check for trade setups
            setup_found, details = trade_analyzer.analyze_for_trade_setup(
                symbol, indicators, current_data
            )
            
            # Update UI in main thread
            self.root.after(0, self.update_simulation_display, symbol, indicators, setup_found, details)
            
            if setup_found:
                alert = {
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'type': 'Trade Setup',
                    'price': current_data['close'].iloc[-1],
                    'details': details
                }
                self.alert_history.append(alert)
                self.root.after(0, self.add_alert_to_history, alert)
            
            current_index += 1
            time.sleep(speed)
    
    def update_simulation_display(self, symbol, indicators, setup_found, details):
        """Updates the simulation display with current data."""
        # Clear existing items
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        # Add current data
        status = "ALERT" if setup_found else "Normal"
        self.data_tree.insert('', 'end', values=(
            symbol,
            f"{indicators.get('Close', 0):.2f}",
            f"{indicators.get('RSI', 0):.2f}",
            f"{indicators.get('EMA50', 0):.2f}",
            f"{indicators.get('EMA200', 0):.2f}",
            f"{indicators.get('Volume', 0):,.0f}",
            status
        ))
        
        # Update alert log
        if setup_found:
            timestamp = datetime.now().strftime('%H:%M:%S')
            alert_msg = f"[{timestamp}] {symbol}: {' | '.join(details)}\n"
            self.alert_text.insert('end', alert_msg)
            self.alert_text.see('end')
    
    def add_alert_to_history(self, alert):
        """Adds an alert to the history treeview."""
        self.history_tree.insert('', 0, values=(
            alert['timestamp'].strftime('%H:%M:%S'),
            alert['symbol'],
            alert['type'],
            f"{alert['price']:.2f}",
            ' | '.join(alert['details'])
        ))
    
    def run_test(self):
        """Runs the selected test."""
        test_type = self.test_type_var.get()
        
        try:
            if test_type == 'alert_scenarios':
                results = self.tester.test_alert_scenarios()
            elif test_type == 'strategy_performance':
                results = self.tester.test_strategy_performance()
            elif test_type == 'comprehensive':
                results = self.tester.run_comprehensive_test()
            
            # Display results
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, json.dumps(results, indent=2, default=str))
            
        except Exception as e:
            messagebox.showerror("Test Error", f"Error running test: {str(e)}")
    
    def generate_report(self):
        """Generates a test report."""
        try:
            report = self.tester.generate_test_report()
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, report)
        except Exception as e:
            messagebox.showerror("Report Error", f"Error generating report: {str(e)}")
    
    def generate_data(self):
        """Generates mock data based on current settings."""
        try:
            symbol = self.gen_symbol_var.get()
            days = self.days_var.get()
            scenario = self.gen_scenario_var.get()
            
            data = self.generator.generate_daily_candles(symbol, days=days, scenario=scenario)
            
            # Display preview
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, f"Generated {len(data)} days of data for {symbol}\n\n")
            self.preview_text.insert(tk.END, data.tail(10).to_string())
        
        except Exception as e:
            messagebox.showerror("Generation Error", f"Error generating data: {str(e)}")
    
    def fetch_real_data(self):
        """Fetches real historical data from Upstox."""
        try:
            symbols_text = self.symbols_text.get('1.0', tk.END).strip()
            symbols = [s.strip() for s in symbols_text.split('\n') if s.strip()]
            days = self.real_days_var.get()
            
            self.status_text.delete('1.0', tk.END)
            self.status_text.insert('1.0', f"Fetching data for {len(symbols)} symbols ({days} days)...\n")
            self.status_text.see(tk.END)
            
            # Run in thread to avoid blocking UI
            def fetch_thread():
                try:
                    results = self.historical_manager.fetch_multiple_symbols(symbols, days)
                    
                    # Update UI in main thread
                    self.root.after(0, lambda: self.update_fetch_status(results))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.status_text.insert(tk.END, f"Error: {e}\n"))
            
            threading.Thread(target=fetch_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch data: {e}")
    
    def update_fetch_status(self, results):
        """Updates the status display with fetch results."""
        self.status_text.insert(tk.END, f"\n✅ Fetch completed!\n")
        self.status_text.insert(tk.END, f"Successfully fetched: {len(results)} symbols\n")
        
        for symbol, data in results.items():
            self.status_text.insert(tk.END, f"  {symbol}: {len(data)} data points\n")
        
        self.status_text.see(tk.END)
    
    def cleanup_cache(self):
        """Cleans up old cached data."""
        try:
            self.historical_manager.cleanup_old_data(days_old=30)
            self.status_text.insert(tk.END, "🧹 Cache cleanup completed\n")
            self.status_text.see(tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to cleanup cache: {e}")
    
    def refresh_data_status(self):
        """Refreshes the data status display."""
        try:
            cache_dir = self.historical_manager.cache_dir
            if os.path.exists(cache_dir):
                files = [f for f in os.listdir(cache_dir) if f.endswith('_historical.json')]
                
                self.status_text.delete('1.0', tk.END)
                self.status_text.insert(tk.END, f"📊 Data Status:\n")
                self.status_text.insert(tk.END, f"Total cached symbols: {len(files)}\n\n")
                
                for file in files[:10]:  # Show first 10
                    symbol = file.replace('_historical.json', '').replace('_', '|')
                    self.status_text.insert(tk.END, f"  {symbol}\n")
                
                if len(files) > 10:
                    self.status_text.insert(tk.END, f"  {len(files) - 10} more...\n")
            else:
                self.status_text.insert(tk.END, "No cached data found\n")
            
            self.status_text.see(tk.END)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh status: {e}")
    
    def clear_history(self):
        """Clears the alert history."""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        self.alert_history.clear()
    
    def run(self):
        """Runs the dashboard."""
        self.root.mainloop()


if __name__ == "__main__":
    dashboard = DevelopmentDashboard()
    dashboard.run() 