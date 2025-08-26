"""
Stock Forecast Backend API
==========================

This FastAPI application provides a REST API for fetching stock market data.
It uses yfinance to retrieve real-time and historical stock data from Yahoo Finance,
and provides endpoints for both historical data and intraday trading data.

Key Features:
- Historical stock price data with customizable time periods
- Intraday trading data with various intervals (1m, 5m, 15m, etc.)
- CORS support for frontend integration
- Data validation and error handling
- Flexible period mapping for different chart views

Dependencies:
- FastAPI: Web framework for building APIs
- yfinance: Yahoo Finance data retrieval
- pandas: Data manipulation and processing
- uvicorn: ASGI server for running the application
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime
import pandas as pd
import yfinance as yf
import logging
from prediction import generate_price_prediction
from backtesting import PredictionBacktester

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI application with title
app = FastAPI(title="Stock API")

# Configure CORS (Cross-Origin Resource Sharing) middleware
# This allows the React frontend (running on localhost:5173) to communicate with this API
# The frontend can make requests to this backend without browser security restrictions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite default dev server ports
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["*"],     # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],     # Allow all headers
)

def load_prices(ticker: str, period: str = "2y") -> pd.DataFrame:
    """
    Load historical stock price data for a given ticker and time period.
    
    This function fetches stock data from Yahoo Finance and processes it to ensure
    consistent column names and data structure. It handles the complex column naming
    that yfinance sometimes returns (tuple-based column names).
    
    Args:
        ticker (str): Stock symbol (e.g., 'AAPL', 'MSFT')
        period (str): Time period for data retrieval. Options include:
            - "1d": 5 days of hourly data (shows intraday price movements)
            - "1w": 3 months of daily data (shows weekly detail)
            - "1mo": 6 months of daily data (shows monthly detail)
            - "1y": 1 year of daily data
            - "2y": 2 years of daily data (default)
            - "5y": 5 years of daily data
            - "10y": 10 years of daily data
            - "max": Maximum available data
    
    Returns:
        pd.DataFrame: Processed stock data with standardized column names
        
    Raises:
        ValueError: If no data is returned or required columns are missing
    """
    # Map our period names to yfinance period names and intervals
    # For "1d" period, we fetch hourly data to show intraday price movements
    if period == "1d":
        # For single day view, get hourly data for the last 5 days to ensure we have enough data
        yf_period = "5d"
        interval = "1h"  # Hourly intervals for intraday view
    else:
        # For other periods, use daily data with appropriate time ranges
        period_mapping = {
            "1w": "3mo",     # 3 months of daily data (shows weekly detail)
            "1mo": "6mo",    # 6 months of daily data (shows monthly detail)
            "1y": "1y",      # 1 year of daily data
            "2y": "2y",      # 2 years of daily data
            "5y": "5y",      # 5 years of daily data
            "10y": "10y",    # 10 years of daily data
            "max": "max"     # max of daily data
        }
        yf_period = period_mapping.get(period, period)
        interval = "1d"  # Daily intervals for historical view
    
    # Download stock data from Yahoo Finance
    # auto_adjust=True: Automatically adjusts for stock splits and dividends
    # progress=False: Suppresses download progress bar
    df = yf.download(ticker, period=yf_period, interval=interval, auto_adjust=True, progress=False)
    
    # Check if we received any data
    if df.empty:
        raise ValueError("No data returned. Check the ticker.")
    
    # Reset the index to make Date a regular column instead of index
    df_reset = df.reset_index()
    
    # yfinance sometimes returns tuple-based column names (e.g., ('Open', 'AAPL'))
    # We need to find the correct column names for each data type
    date_col = None
    open_col = None
    high_col = None
    low_col = None
    close_col = None
    volume_col = None
    
    # Iterate through columns to find the correct column names
    # Handle both tuple columns and regular string columns
    for col in df_reset.columns:
        if isinstance(col, tuple):
            # Handle tuple columns (e.g., ('Open', 'AAPL'))
            if col[0] in ['Date', 'Datetime']:
                date_col = col
            elif col[0] == 'Open':
                open_col = col
            elif col[0] == 'High':
                high_col = col
            elif col[0] == 'Low':
                low_col = col
            elif col[0] == 'Close':
                close_col = col
            elif col[0] == 'Volume':
                volume_col = col
        else:
            # Handle regular string columns
            if col in ['Date', 'Datetime']:
                date_col = col
            elif col == 'Open':
                open_col = col
            elif col == 'High':
                high_col = col
            elif col == 'Low':
                low_col = col
            elif col == 'Close':
                close_col = col
            elif col == 'Volume':
                volume_col = col
    
    # Ensure we have at least the essential columns
    if date_col is None or close_col is None:
        raise ValueError(f"Could not find Date/Datetime or Close columns. Available columns: {df_reset.columns.tolist()}")
    
    # Select all available columns, starting with required ones
    columns_to_select = [date_col, close_col]
    if open_col:
        columns_to_select.append(open_col)
    if high_col:
        columns_to_select.append(high_col)
    if low_col:
        columns_to_select.append(low_col)
    if volume_col:
        columns_to_select.append(volume_col)
    
    # Create a copy with only the selected columns
    result = df_reset[columns_to_select].copy()
    
    # Rename columns to standardized names for consistent API responses
    column_mapping = {date_col: "date", close_col: "close"}
    if open_col:
        column_mapping[open_col] = "open"
    if high_col:
        column_mapping[high_col] = "high"
    if low_col:
        column_mapping[low_col] = "low"
    if volume_col:
        column_mapping[volume_col] = "volume"
    
    # Apply the column renaming
    result.columns = [column_mapping.get(col, col) for col in result.columns]
    
    # Convert date column to datetime and set as index
    result['date'] = pd.to_datetime(result['date'])
    result = result.set_index('date')
    
    # For shorter time periods, ensure data quality
    if period in ["1d", "1w", "1mo"]:
        # Remove any rows with NaN (missing) values
        result = result.dropna()
        
        # Ensure we have at least some data points
        if len(result) == 0:
            print(f"No data points for {period}, this might indicate an issue with the interval")
    
    # Sort index to ensure data is in chronological order
    result = result.sort_index()
    
    return result

@app.get("/health")
def health():
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        dict: Simple status indicating the API is healthy
    """
    return {"ok": True}

@app.get("/history")
def history(
    ticker: str = Query(..., min_length=1, max_length=10),
    period: str = Query("2y", pattern="^(1d|1w|1mo|1y|2y|5y|10y|max)$")
):
    """
    Get historical stock price data for a given ticker and time period.
    
    This is the main endpoint for retrieving historical stock data. It returns
    OHLCV (Open, High, Low, Close, Volume) data points that can be used to
    create charts and perform analysis.
    
    Args:
        ticker (str): Stock symbol (1-10 characters, required)
        period (str): Time period for data (default: "2y")
    
    Returns:
        dict: JSON response containing:
            - ticker: The stock symbol
            - period: The time period requested
            - points: Array of data points with date, close, open, high, low, volume
            - interval: Description of the data interval
    
    Raises:
        HTTPException: If data loading fails or invalid parameters provided
    """
    try:
        # Load the stock data using our helper function
        df = load_prices(ticker.upper(), period)
    except Exception as e:
        # Return a proper HTTP error if something goes wrong
        raise HTTPException(400, f"Failed to load data: {e}")
    
    # Convert DataFrame to list of dictionaries for JSON serialization
    points = []
    for index, row in df.iterrows():
        point = {"date": str(index)}
        
        # Add all available fields (some stocks might not have all data)
        if "close" in df.columns:
            point["close"] = float(row["close"])
        if "open" in df.columns:
            point["open"] = float(row["open"])
        if "high" in df.columns:
            point["high"] = float(row["high"])
        if "low" in df.columns:
            point["low"] = float(row["low"])
        if "volume" in df.columns:
            point["volume"] = int(row["volume"])
        
        points.append(point)
    
    # Return structured response with metadata
    return {
        "ticker": ticker.upper(),
        "period": period,
        "points": points,
        "interval": get_interval_for_period(period)
    }

def get_interval_for_period(period: str) -> str:
    """
    Get a human-readable description of the data interval for a given period.
    
    This function provides context about what the data represents, which is useful
    for frontend display and user understanding.
    
    Args:
        period (str): The time period identifier
    
    Returns:
        str: Human-readable description of the interval
    """
    interval_mapping = {
        "1d": "1 hour (5 days view)",
        "1w": "1 day (3 months view)", 
        "1mo": "1 day (6 months view)",
        "1y": "1 day",
        "2y": "1 day",
        "5y": "1 day",
        "10y": "1 day",
        "max": "1 day"
    }
    return interval_mapping.get(period, "1 day")

@app.get("/predict")
def predict_price(
    ticker: str = Query(..., min_length=1, max_length=10),
    target_date: str = Query(..., regex="^\d{4}-\d{2}-\d{2}$")
):
    """
    Predict stock price for a given date using enhanced backtested strategy.
    
    Args:
        ticker (str): Stock symbol (e.g., 'AAPL', 'MSFT')
        target_date (str): Target date for prediction (YYYY-MM-DD format)
        
    Returns:
        dict: Prediction results including:
            - Current price
            - Median prediction
            - Confidence intervals
            - Historical accuracy metrics
    """
    try:
        logger.info(f"Receiving prediction request for {ticker} on {target_date}")
        
        # Convert target_date string to datetime
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        
        # Ensure target date is in the future
        if target_dt <= datetime.now():
            raise HTTPException(400, "Target date must be in the future")
        
        # Get 6 months of historical data for prediction
        logger.debug(f"Fetching historical data for {ticker}")
        historical_data = load_prices(ticker.upper(), "6mo")
        
        if historical_data.empty:
            raise HTTPException(400, f"No historical data available for {ticker}")
        
        logger.debug(f"Retrieved {len(historical_data)} days of data from {historical_data.index[0]} to {historical_data.index[-1]}")
        logger.debug(f"Available columns: {list(historical_data.columns)}")
        
        # Get the current (latest) price
        current_price = historical_data['close'].iloc[-1]
        logger.debug(f"Current price for {ticker}: {current_price}")
        
        # Check for NaN values
        nan_cols = historical_data.columns[historical_data.isna().any()].tolist()
        if nan_cols:
            logger.warning(f"NaN values found in columns: {nan_cols}")
        
        # Initialize backtester to calculate technical indicators
        logger.debug("Initializing backtester and calculating technical indicators")
        backtester = PredictionBacktester(historical_data)
        processed_data = backtester.data
        
        # Generate prediction using the processed data
        logger.debug("Generating prediction using backtested model")
        prediction = generate_price_prediction(processed_data, target_dt, current_price)
        logger.debug(f"Raw prediction generated: {prediction}")
        
        if not isinstance(prediction, dict):
            raise ValueError("Prediction must return a dictionary")
        logger.info(f"Prediction generated successfully for {ticker}")
        
        return {
            "ticker": ticker.upper(),
            "prediction": prediction
        }
        
    except ValueError as e:
        logger.error(f"ValueError in prediction: {str(e)}")
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        raise HTTPException(500, f"Prediction failed: {str(e)}")

@app.get("/advanced_prediction/{ticker}")
async def get_advanced_prediction(ticker: str, target_date: str):
    """
    Get advanced stock price prediction including:
    - Median prediction
    - Confidence intervals (80% and 95%)
    - Probability estimates
    """
    try:
        # Convert target_date string to datetime
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        
        # Ensure target date is in the future
        if target_dt <= datetime.now():
            raise HTTPException(400, "Target date must be in the future")
            
        # Load 6 months of historical data for prediction
        df = load_prices(ticker.upper(), "6mo")
        
        # Get the current (latest) price
        current_price = df['close'].iloc[-1]
        
        # Generate prediction
        prediction = generate_price_prediction(df, target_dt, current_price)
        
        return {
            "ticker": ticker.upper(),
            "prediction": prediction
        }
        
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Prediction failed: {str(e)}")

@app.get("/intraday")
def intraday(
    ticker: str = Query(..., min_length=1, max_length=10),
    interval: str = Query("1m", pattern="^(1m|2m|5m|15m|30m|60m|90m|1h|1d|5d|1wk|1mo|3mo)$")
):
    """
    Get detailed intraday trading data with custom intervals.
    
    This endpoint provides high-frequency trading data for intraday analysis.
    It's useful for day trading, technical analysis, and real-time monitoring.
    
    Args:
        ticker (str): Stock symbol (1-10 characters, required)
        interval (str): Data interval. Options include:
            - "1m", "2m", "5m", "15m", "30m": Minute-level data
            - "60m", "90m": Hour-level data
            - "1h": 1 hour intervals
            - "1d", "5d": Daily data
            - "1wk", "1mo", "3mo": Weekly/monthly data
    
    Returns:
        dict: JSON response containing:
            - ticker: The stock symbol
            - interval: The data interval requested
            - points: Array of intraday data points
    
    Raises:
        HTTPException: If data loading fails or invalid parameters provided
    """
    try:
        # For intraday data, we'll use a shorter period to get more granular data
        # Very short intervals (1m-30m) need recent data, longer intervals can use more history
        period = "5d" if interval in ["1m", "2m", "5m", "15m", "30m"] else "1mo"
        
        # Download intraday data with the specified interval
        df = yf.download(ticker.upper(), period=period, interval=interval, auto_adjust=True, progress=False)
        
        if df.empty:
            raise ValueError("No data returned. Check the ticker.")
        
        # Process the data similar to load_prices function
        # Reset index to make Date a regular column
        df_reset = df.reset_index()
        
        # Find the correct column names (handle tuple columns from yfinance)
        date_col = None
        close_col = None
        open_col = None
        high_col = None
        low_col = None
        volume_col = None
        
        # Iterate through columns to find the correct column names
        for col in df_reset.columns:
            if isinstance(col, tuple):
                if col[0] == 'Date':
                    date_col = col
                elif col[0] == 'Open':
                    open_col = col
                elif col[0] == 'High':
                    high_col = col
                elif col[0] == 'Low':
                    low_col = col
                elif col[0] == 'Close':
                    close_col = col
                elif col[0] == 'Volume':
                    volume_col = col
            else:
                if col == 'Date':
                    date_col = col
                elif col == 'Open':
                    open_col = col
                elif col == 'High':
                    high_col = col
                elif col == 'Low':
                    low_col = col
                elif col == 'Close':
                    close_col = col
                elif col == 'Volume':
                    volume_col = col
        
        if date_col is None or close_col is None:
            raise ValueError("Could not find Date or Close columns")
        
        # Select all available columns
        columns_to_select = [date_col, close_col]
        if open_col:
            columns_to_select.append(open_col)
        if high_col:
            columns_to_select.append(high_col)
        if low_col:
            columns_to_select.append(low_col)
        if volume_col:
            columns_to_select.append(volume_col)
        
        result = df_reset[columns_to_select].copy()
        
        # Rename columns to standardized names
        column_mapping = {date_col: "date", close_col: "close"}
        if open_col:
            column_mapping[open_col] = "open"
        if high_col:
            column_mapping[high_col] = "high"
        if low_col:
            column_mapping[low_col] = "low"
        if volume_col:
            column_mapping[volume_col] = "volume"
        
        result.columns = [column_mapping.get(col, col) for col in result.columns]
        
        # Remove NaN values for clean intraday data
        result = result.dropna()
        
        # Convert to list of dictionaries for JSON response
        points = []
        for _, row in result.iterrows():
            point = {"date": str(row["date"])}
            
            # Add all available price and volume data
            if "close" in row:
                point["close"] = float(row["close"])
            if "open" in row:
                point["open"] = float(row["open"])
            if "high" in row:
                point["high"] = float(row["high"])
            if "low" in row:
                point["low"] = float(row["low"])
            if "volume" in row:
                point["volume"] = int(row["volume"])
            
            points.append(point)
        
        # Return structured intraday data
        return {
            "ticker": ticker.upper(),
            "interval": interval,
            "points": points
        }
        
    except Exception as e:
        # Return proper HTTP error if something goes wrong
        raise HTTPException(400, f"Failed to load intraday data: {e}")