"""
Price Prediction Module
======================

Simple momentum-based price prediction module using recent price changes
and basic moving averages. Focuses on momentum over the last 20 days
and trend from 50-day moving average.
"""

import numpy as np
from scipy import stats
from datetime import datetime, timedelta
import pandas as pd
from backtesting import PredictionBacktester

def get_historical_accuracy(df: pd.DataFrame, days_ahead: int) -> dict:
    """
    Calculate historical prediction accuracy metrics.
    
    Args:
        df: DataFrame with historical price data
        days_ahead: Number of days to predict ahead
        
    Returns:
        Dict containing accuracy metrics
    """
    print(f"\nAnalyzing historical accuracy with {len(df) if df is not None else 0} data points")
    
    if df is None or df.empty:
        raise ValueError("No historical data provided")
    
    print(f"Data range: {df.index[0]} to {df.index[-1]}")
    print(f"Available columns: {list(df.columns)}")
    
    # Ensure we have the required columns
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Check for NaN values
    nan_cols = df.columns[df.isna().any()].tolist()
    if nan_cols:
        print(f"Warning: NaN values found in columns: {nan_cols}")
    
    # Convert index to datetime if not already
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # We need at least 30 days of data plus the prediction horizon for basic backtesting
    min_required_days = 60 + days_ahead
    if len(df) < min_required_days:
        raise ValueError(
            f"Insufficient historical data for backtesting.\n"
            f"Got {len(df)} days, need at least {min_required_days}.\n"
            f"Current date range: {df.index[0]} to {df.index[-1]}"
        )
    
    # Initialize backtester with historical data
    backtester = PredictionBacktester(df)
    
    # Calculate prediction accuracy for the last 60 days
    end_date = df.index[-1]
    start_date = df.index[-min_required_days]
    
    # Format dates as strings in YYYY-MM-DD format
    end_date_str = end_date.strftime('%Y-%m-%d')
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    return backtester.backtest_prediction(
        start_date=start_date_str,
        end_date=end_date_str,
        prediction_horizon=days_ahead
    )

def generate_price_prediction(
historical_data: pd.DataFrame,
target_date: datetime,
current_price: float
) -> dict:
    """
    Generate price predictions using momentum and moving average.
    
    Args:
        historical_data: DataFrame with historical price data
        target_date: Date for which to predict the price
        current_price: Most recent closing price
        
    Returns:
        dict containing prediction details and confidence intervals
    """
    print(f"\nGenerating prediction for target date: {target_date}")
    print(f"Current price: ${current_price:.2f}")
    print(f"Historical data points: {len(historical_data) if historical_data is not None else 0}")
    
    # Ensure target_date is a datetime object
    if not isinstance(target_date, datetime):
        raise ValueError("target_date must be a datetime object")
    
    # Calculate days until target
    current_date = datetime.now()
    days_until_target = (target_date - current_date).days
    
    if days_until_target <= 0:
        raise ValueError("Target date must be in the future")
    
    # Initialize backtester with historical data
    backtester = PredictionBacktester(historical_data)
    
    # Use a 50-day window for predictions
    window_size = min(50, len(historical_data) - 10)
    prediction_window = historical_data.iloc[-window_size:]
    
    # Get base prediction
    prediction = backtester._make_prediction(prediction_window, days_until_target)
    
    # Calculate confidence intervals based on volatility
    volatility = prediction_window['returns'].std() * np.sqrt(days_until_target)
    confidence_80 = volatility * 1.28  # 80% confidence interval
    confidence_95 = volatility * 1.96  # 95% confidence interval
    
    # Get accuracy metrics from recent history
    accuracy_metrics = get_historical_accuracy(historical_data, days_until_target)
    
    # Return prediction with confidence intervals
    return {
        'current_price': current_price,
        'target_date': target_date.strftime('%Y-%m-%d'),
        'median_prediction': prediction,
        'confidence_intervals': {
            '80': [
                prediction * (1 - confidence_80),
                prediction * (1 + confidence_80)
            ],
            '95': [
                prediction * (1 - confidence_95),
                prediction * (1 + confidence_95)
            ]
        },
        'probability_within_5_percent': min(95, 100 * (1 - volatility)),
        'historical_accuracy': accuracy_metrics
    }
    
    # Get historical accuracy metrics
    accuracy_metrics = get_historical_accuracy(historical_data, days_until_target)
    
    # Initialize backtester with historical data
    backtester = PredictionBacktester(historical_data)
    
    # Use the backtester's prediction model with dynamic window size
    window_size = min(50, len(historical_data) - 10)  # Ensure we have enough data
    prediction_window = historical_data.iloc[-window_size:]
    
    # Get current market conditions
    current_conditions = historical_data.iloc[-1]
    adx = current_conditions['ADX']
    rsi = current_conditions['RSI']
    atr = current_conditions['ATR']
    
    # Calculate base prediction with volatility adjustment
    volatility = historical_data['returns'].tail(20).std()
    trend = historical_data['returns'].tail(5).mean()
    
    # Get base prediction from backtester
    base_prediction = backtester._make_prediction(prediction_window, days_until_target)
    
    # Adjust prediction based on current market conditions
    if adx > 25:  # Strong trend
        if rsi < 30:  # Oversold
            adjustment = 1 + (volatility * np.sqrt(days_until_target))
        elif rsi > 70:  # Overbought
            adjustment = 1 - (volatility * np.sqrt(days_until_target))
        else:
            adjustment = 1 + (np.sign(trend) * volatility * np.sqrt(days_until_target))
    else:  # Weak trend
        adjustment = 1 + (trend * min(np.sqrt(days_until_target), 2.0))
        
    # Apply adjustment with ATR-based limits
    max_move = min(0.15, 2.0 * atr / current_price) * np.sqrt(days_until_target)  # Cap at 15% or 2x ATR
    adjustment = np.clip(adjustment, 1 - max_move, 1 + max_move)
    base_prediction *= adjustment
    
    # Dynamic movement limits based on market conditions
    base_daily_limit = 0.02  # Start with 2% base limit
    
    # Adjust limits based on trend strength (ADX)
    if adx > 30:  # Strong trend
        base_daily_limit *= (1 + (adx - 30) / 100)  # Increase limit in strong trends
    
    # Adjust based on volatility (ATR)
    volatility_factor = atr / current_price
    base_daily_limit = max(base_daily_limit, volatility_factor * 1.5)
    
    # Calculate maximum allowed move with time decay
    time_factor = np.sqrt(days_until_target)  # Square root to reduce time impact
    max_total_move = base_daily_limit * time_factor
    
    # Calculate bounds with asymmetric limits
    if base_prediction > current_price:  # Upward prediction
        max_price = current_price * (1 + max_total_move * 1.2)  # Allow more upside
        min_price = current_price * (1 - max_total_move * 0.8)  # Restrict downside
    else:  # Downward prediction
        max_price = current_price * (1 + max_total_move * 0.8)  # Restrict upside
        min_price = current_price * (1 - max_total_move * 1.2)  # Allow more downside
    
    # Apply bounds with consideration for extreme conditions
    if (rsi > 70 and base_prediction > current_price) or (rsi < 30 and base_prediction < current_price):
        # More restrictive in overbought/oversold conditions
        predicted_price = current_price + (base_prediction - current_price) * 0.7
    else:
        predicted_price = base_prediction
        
    # Final bounds check
    predicted_price = np.clip(predicted_price, min_price, max_price)
    
        # Calculate trend-based change
    trend_direction = 1 if latest_data['MACD'] > latest_data['Signal_Line'] else -1
    trend_strength = min(1.0, latest_data['ADX'] / 25.0)  # Normalize ADX
    
    # Calculate base predicted change
    days_scale = np.sqrt(days_until_target)  # Scale changes with square root of time
    base_change = (historical_data['close'].pct_change().mean() * days_scale)
    
    # Enhanced trend-based adjustment
    if trend_direction > 0 and latest_data['RSI'] < 70:  # Uptrend and not overbought
        trend_multiplier = 1.0 + (trend_strength * 0.5)  # Up to 50% stronger
    elif trend_direction < 0 and latest_data['RSI'] > 30:  # Downtrend and not oversold
        trend_multiplier = 1.0 + (trend_strength * 0.5)  # Up to 50% stronger
    else:
        trend_multiplier = 0.5  # Reduce effect when against RSI signals
    
    # Calculate predicted change
    predicted_change = base_change * trend_multiplier
    
    # Apply momentum factor based on recent performance
    recent_momentum = historical_data['returns'].tail(5).mean()
    momentum_factor = 1.0 + (np.sign(recent_momentum) * min(abs(recent_momentum) * 2, 0.1))
    
    # Calculate final price with all factors
    predicted_price = current_price * (1 + predicted_change * momentum_factor)
    
    # Dynamic maximum move based on volatility and time
    atr = latest_data['ATR']
    daily_volatility = atr / current_price
    max_daily_move = max(0.02, daily_volatility * 1.5)  # At least 2% or 1.5x ATR-based move
    max_total_move = max_daily_move * days_scale
    
    # Calculate price bounds
    max_price = current_price * (1 + max_total_move)
    min_price = current_price * (1 - max_total_move)
    
    # Apply bounds with momentum consideration
    if predicted_price > current_price and latest_data['RSI'] > 70:
        predicted_price = current_price + (predicted_price - current_price) * 0.5
    elif predicted_price < current_price and latest_data['RSI'] < 30:
        predicted_price = current_price - (current_price - predicted_price) * 0.5
    
    # Final bounds check
    predicted_price = np.clip(predicted_price, min_price, max_price)
    
    # Calculate confidence intervals based on historical accuracy
    mape = accuracy_metrics['mape']
    rmse = accuracy_metrics['rmse']
    
    # Adjust confidence based on technical signals agreement
    signal_agreement = abs(rsi_signal + macd_signal) / 2  # 0 to 1 scale
    confidence_factor = (1.0 - min(mape, 0.5)) * (0.8 + 0.2 * signal_agreement)
    
    # Calculate adjusted standard deviation for confidence intervals
    historical_std = rmse / current_price  # Normalized RMSE
    time_scaling = np.sqrt(days_until_target / 30)  # Scale uncertainty with time
    adjusted_std = predicted_price * historical_std * time_scaling
    
    # Calculate confidence intervals
    confidence_intervals = {
        '80': stats.norm.interval(0.80, loc=predicted_price, scale=adjusted_std),
        '95': stats.norm.interval(0.95, loc=predicted_price, scale=adjusted_std)
    }
    
    # Calculate probability estimates
    prob_within_5_percent = (
        stats.norm.cdf(predicted_price * 1.05, loc=predicted_price, scale=adjusted_std) -
        stats.norm.cdf(predicted_price * 0.95, loc=predicted_price, scale=adjusted_std)
    ) * confidence_factor
    
    # Format the target date
    target_date_str = target_date.strftime('%Y-%m-%d') if hasattr(target_date, 'strftime') else str(target_date)

    return {
        'current_price': current_price,
        'target_date': target_date_str,
        'median_prediction': round(predicted_price, 2),
        'confidence_intervals': {
            '80': [round(ci, 2) for ci in confidence_intervals['80']],
            '95': [round(ci, 2) for ci in confidence_intervals['95']]
        },
        'probability_within_5_percent': round(prob_within_5_percent * 100, 1),
        'historical_accuracy': {
            'mape': round(mape * 100, 2),  # Convert to percentage
            'rmse': round(rmse, 2),
            'confidence_factor': round(confidence_factor * 100, 2)  # Convert to percentage
        }
    }