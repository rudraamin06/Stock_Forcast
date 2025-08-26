"""
Simple Momentum-Based Stock Predictor
===================================

A straightforward momentum-based prediction strategy using recent price changes
and basic moving averages.
"""

import pandas as pd
import numpy as np
from typing import Dict

class PredictionBacktester:
    def __init__(self, historical_data: pd.DataFrame):
        """Initialize with historical price data."""
        self.data = historical_data.copy()
        
        # Ensure datetime index
        if not isinstance(self.data.index, pd.DatetimeIndex):
            if 'date' in self.data.columns:
                self.data.set_index('date', inplace=True)
            self.data.index = pd.to_datetime(self.data.index)
        
        self.data.sort_index(inplace=True)
        self._prepare_data()
        
    def _prepare_data(self):
        """Calculate basic price data and indicators."""
        # Calculate returns and moving average
        self.data['returns'] = self.data['close'].pct_change()
        self.data['MA50'] = self.data['close'].rolling(window=50).mean()
        
        # Calculate 20-day momentum
        self.data['momentum'] = self.data['close'].pct_change(periods=20)
        
        # Simple volatility measure
        self.data['volatility'] = self.data['returns'].rolling(window=20).std()
        
        # Clean up NaN values
        self.data.dropna(inplace=True)
        
    def _make_prediction(self, data: pd.DataFrame, horizon: int) -> float:
        """Make a price prediction based on momentum and moving average."""
        current_price = data['close'].iloc[-1]
        momentum = data['momentum'].iloc[-1]
        current_ma = data['MA50'].iloc[-1]
        volatility = data['volatility'].iloc[-1]
        
        # Print current conditions for debugging
        print(f"\nMaking prediction with {len(data)} days of data")
        print(f"Date range: {data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}")
        print(f"\nCurrent Market Conditions:")
        print(f"Current Price: ${current_price:.2f}")
        print(f"50-day MA: ${current_ma:.2f}")
        print(f"20-day Momentum: {momentum*100:.2f}%")
        print(f"20-day Volatility: {volatility*100:.2f}%")
        
        # Calculate prediction effects
        momentum_effect = momentum * np.sqrt(horizon/20)  # Scale with time
        ma_diff = (current_price - current_ma) / current_ma
        mean_reversion = -ma_diff * 0.1 * horizon  # Pull toward MA
        
        # Combine and adjust for volatility
        total_effect = (momentum_effect + mean_reversion) * (1 + volatility)
        predicted_price = current_price * (1 + total_effect)
        
        return predicted_price
        
    def backtest_prediction(self, start_date: str, end_date: str, prediction_horizon: int) -> Dict:
        """Run backtesting over a specified date range."""
        test_data = self.data[start_date:end_date]
        predictions = []
        actuals = []
        
        # Generate predictions
        for i in range(len(test_data) - prediction_horizon):
            current_data = self.data[:test_data.index[i]]
            pred = self._make_prediction(current_data, prediction_horizon)
            actual = test_data['close'].iloc[i + prediction_horizon]
            predictions.append(pred)
            actuals.append(actual)
        
        # Calculate metrics
        errors = np.array([(p - a)/a for p, a in zip(predictions, actuals)])
        mape = np.mean(np.abs(errors)) * 100
        rmse = np.sqrt(np.mean((np.array(predictions) - np.array(actuals))**2))
        
        # Calculate directional accuracy
        actual_moves = np.diff([test_data['close'].iloc[i] for i in range(len(predictions) + 1)])
        pred_moves = np.array(predictions) - test_data['close'].iloc[:-prediction_horizon]
        directional_accuracy = np.mean(np.sign(actual_moves) == np.sign(pred_moves)) * 100
        
        return {
            'mape': mape,
            'rmse': rmse,
            'directional_accuracy': directional_accuracy,
            'n_predictions': len(predictions),
            'date_range': f"{test_data.index[0].strftime('%Y-%m-%d')} to {test_data.index[-1].strftime('%Y-%m-%d')}"
        }
