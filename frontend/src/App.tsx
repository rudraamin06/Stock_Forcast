/**
 * Stock Forecast Frontend Application
 * ===================================
 * 
 * This React application provides a user interface for viewing stock market data.
 * It connects to the backend API to fetch real-time and historical stock prices,
 * displays interactive charts, and allows users to explore different time periods.
 * 
 * Key Features:
 * - Real-time stock data visualization
 * - Interactive line charts with tooltips
 * - Multiple timeframe selection (1D, 1W, 1M, 1Y, etc.)
 * - Stock performance color coding (green for gains, red for losses)
 * - Responsive design for different screen sizes
 * - Price predictions with confidence intervals
 * 
 * Dependencies:
 * - React: UI framework
 * - Recharts: Charting library for data visualization
 * - Axios: HTTP client for API communication
 * - date-fns: Date formatting utilities
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'
import SearchBar from './components/SearchBar'
import PredictionPanel from './components/PredictionPanel'
import './App.css'

/**
 * TypeScript interface defining the structure of stock data received from the API
 * This ensures type safety and provides IntelliSense for the data structure
 */
interface StockData {
  ticker: string          // Stock symbol (e.g., 'AAPL', 'MSFT')
  period: string          // Time period of the data (e.g., '1d', '1y')
  interval: string        // Data interval description (e.g., '1 day (1 month view)')
  points: Array<{         // Array of data points with OHLCV data
    date: string          // Date string for each data point
    close: number         // Closing price (required)
    open?: number         // Opening price (optional)
    high?: number         // Highest price (optional)
    low?: number          // Lowest price (optional)
    volume?: number       // Trading volume (optional)
  }>
}

/**
 * Available timeframes for stock data visualization
 * Each timeframe corresponds to a different period of historical data
 * The backend API maps these to appropriate data ranges
 */
const timeframes = [
  { value: '1d', label: '1D' },      // 1 day (shows 5 days of hourly data)
  { value: '1w', label: '1W' },      // 1 week (shows 3 months of data)
  { value: '1mo', label: '1M' },     // 1 month (shows 6 months of data)
  { value: '1y', label: '1Y' },      // 1 year
  { value: '2y', label: '2Y' },      // 2 years
  { value: '5y', label: '5Y' },      // 5 years
  { value: '10y', label: '10Y' },    // 10 years
  { value: 'max', label: 'MAX' }     // Maximum available data
]

/**
 * Main App component that renders the stock forecast application
 * Manages state for stock data, user inputs, and chart interactions
 */
function App() {
  // State management for the application
  const [stockData, setStockData] = useState<StockData | null>(null)  // Current stock data from API
  const [ticker, setTicker] = useState<string | null>(null)           // Current stock symbol (null by default)
  const [period, setPeriod] = useState('1d')                          // Current time period (default: 1 day)
  const [loading, setLoading] = useState(false)                       // Loading state for API calls
  const [error, setError] = useState('')                              // Error message if API call fails
  const [hoveredPrice, setHoveredPrice] = useState<number | null>(null) // Price shown on hover
  
  // Ref for managing hover timeout to prevent excessive state updates
  const hoverTimeoutRef = useRef<number | null>(null)

  /**
   * Fetches stock data from the backend API
   * Called whenever the ticker or period changes
   * Updates the application state with new data or error messages
   */
  const fetchStockData = async () => {
    if (!ticker) return;  // Don't fetch if no ticker is selected
    
    setLoading(true)        // Show loading state
    setError('')            // Clear any previous errors
    try {
      // Make HTTP GET request to backend API
      const response = await axios.get(`http://localhost:8000/history?ticker=${ticker}&period=${period}`)
      setStockData(response.data)                    // Update stock data state
      setHoveredPrice(null)                         // Reset hovered price for new data
    } catch (err) {
      // Handle API errors gracefully
      setError('Failed to fetch stock data. Please check if the backend server is running.')
      console.error('Error fetching stock data:', err)
    } finally {
      setLoading(false)     // Hide loading state
    }
  }

  /**
   * Effect hook that automatically fetches new data when ticker or period changes
   * This ensures the chart updates whenever the user changes the stock or timeframe
   */
  useEffect(() => {
    fetchStockData()
  }, [ticker, period])

  /**
   * Formats dates for display based on the selected time period
   * Shorter periods show more detailed time information
   * 
   * @param dateString - ISO date string from the API
   * @returns Formatted date string for display
   */
  const formatFullDate = (dateString: string) => {
    // For shorter periods, show more detailed time info
    if (period === '1d') {
      return format(new Date(dateString), 'MMM dd, yyyy HH:mm')  // Include time for hourly view
    } else if (period === '1w') {
      return format(new Date(dateString), 'MMM dd, yyyy')        // Date only for weekly view
    } else {
      return format(new Date(dateString), 'MMM dd, yyyy')        // Standard date format
    }
  }

  /**
   * Formats price values for display with dollar sign and 2 decimal places
   * 
   * @param price - Raw price number
   * @returns Formatted price string (e.g., "$150.25")
   */
  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`
  }

  /**
   * Formats volume numbers for better readability
   * Converts large numbers to abbreviated format (K, M, B)
   * 
   * @param volume - Raw volume number
   * @returns Formatted volume string (e.g., "1.5M", "2.3B")
   */
  const formatVolume = (volume: number) => {
    if (volume >= 1e9) {
      return `${(volume / 1e9).toFixed(1)}B`      // Billions
    } else if (volume >= 1e6) {
      return `${(volume / 1e6).toFixed(1)}M`      // Millions
    } else if (volume >= 1e3) {
      return `${(volume / 1e3).toFixed(1)}K`      // Thousands
    }
    return volume.toString()                        // Small numbers as-is
  }

  /**
   * Determines if the stock is showing a gain or loss based on current vs first price
   * Used for color coding the chart line (green for gains, red for losses)
   * 
   * @param currentPrice - The current price to evaluate
   * @returns 'gain', 'loss', or 'neutral'
   */
  const getStockPerformance = useCallback((currentPrice: number) => {
    if (!stockData || stockData.points.length < 2) return 'neutral'
    
    const firstPrice = stockData.points[0].close  // First price in the dataset
    
    if (currentPrice > firstPrice) return 'gain'   // Price increased
    if (currentPrice < firstPrice) return 'loss'   // Price decreased
    return 'neutral'                                // No change
  }, [stockData])

  // Determine which price to display (hovered price or current price)
  const displayPrice = hoveredPrice !== null ? hoveredPrice : (stockData?.points[stockData.points.length - 1]?.close || 0)
  
  // Get performance status for color coding
  const stockPerformance = getStockPerformance(displayPrice)
  
  // Set line color based on performance (green for gains, red for losses, gray for neutral)
  const lineColor = stockPerformance === 'gain' ? '#00c805' : stockPerformance === 'loss' ? '#ff3b30' : '#8e8e93'

  /**
   * Debounced function to update hovered price
   * Prevents excessive state updates when hovering over the chart
   * 
   * @param price - The price to display on hover
   */
  const updateHoveredPrice = useCallback((price: number) => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current)  // Clear existing timeout
    }
    
    // Set new timeout to update price after 50ms delay
    hoverTimeoutRef.current = setTimeout(() => {
      setHoveredPrice(price)
    }, 50) // 50ms debounce
  }, [])

  /**
   * Custom tooltip component for the chart
   * Displays detailed information when hovering over data points
   * Updates the hovered price state for real-time price display
   */
  const CustomTooltip = useCallback(({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      updateHoveredPrice(data.close)  // Update hovered price with debouncing
      
      return (
        <div className="custom-tooltip">
          <div className="tooltip-date">{formatFullDate(label)}</div>
          <div className="tooltip-price">Close: {formatPrice(data.close)}</div>
          {data.open && <div className="tooltip-data">Open: {formatPrice(data.open)}</div>}
          {data.high && <div className="tooltip-data">High: {formatPrice(data.high)}</div>}
          {data.low && <div className="tooltip-data">Low: {formatPrice(data.low)}</div>}
          {data.volume && <div className="tooltip-data">Volume: {formatVolume(data.volume)}</div>}
        </div>
      )
    }
    return null
  }, [updateHoveredPrice, formatFullDate, formatPrice, formatVolume])

  /**
   * Handles mouse leave events from the chart area
   * Resets the hovered price to show the current price instead
   */
  const handleChartMouseLeave = useCallback(() => {
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current)  // Clear any pending hover updates
    }
    setHoveredPrice(null)  // Reset to show current price
  }, [])

  /**
   * Cleanup effect to clear any pending timeouts when component unmounts
   * Prevents memory leaks and errors from updating state on unmounted component
   */
  useEffect(() => {
    return () => {
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current)
      }
    }
  }, [])

  /**
   * Main render function for the application
   * Returns the complete UI including header, controls, chart, and timeframe buttons
   */
  return (
    <div className="app">
      {/* Application header with title and description */}
      <header className="header">
        <h1>📈 Stock Forecast</h1>
        <p>Real-time stock price data and analysis</p>
      </header>

      {/* SearchBar component for stock selection */}
      <SearchBar onSelect={setTicker} />

      {/* Error display area */}
      {error && (
        <div className="error">
          {error}
        </div>
      )}

      {/* No data message when no ticker is selected */}
      {!ticker && (
        <div className="no-data-message">
          <p>Enter a stock ticker above to view its data</p>
        </div>
      )}

      {/* Manual refresh button - only shown when a ticker is selected */}
      {ticker && (
        <button 
          onClick={fetchStockData} 
          disabled={loading}
          className="fetch-button"
        >
          {loading ? 'Loading...' : 'Refresh Data'}
        </button>
      )}

      {/* Main chart container - only shown when data is available */}
      {stockData && !loading && ticker && (
        <div className="chart-container">
          {/* Price header showing current price, ticker, and data info */}
          <div className="price-header">
            <div className="current-price" style={{ color: lineColor }}>
              {formatPrice(displayPrice)}
            </div>
            <div className="ticker-symbol">{stockData.ticker}</div>
            <div className="data-info">
              {stockData.points.length} data points • {stockData.interval}
            </div>
          </div>
          
          {/* Interactive chart area with mouse leave handling */}
          <div className="chart" onMouseLeave={handleChartMouseLeave}>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={stockData.points} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                {/* Chart grid lines for better readability */}
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" opacity={0.2} />
                
                {/* X-axis (hidden for cleaner look) */}
                <XAxis 
                  dataKey="date" 
                  hide={true}
                />
                
                {/* Y-axis with price formatting and styling */}
                <YAxis 
                  domain={['dataMin - (dataMax - dataMin) * 0.02', 'dataMax + (dataMax - dataMin) * 0.02']}
                  tickFormatter={formatPrice}
                  stroke="#7c7c7c"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#7c7c7c' }}
                  tickCount={6}
                />
                
                {/* Custom tooltip for data point information */}
                <Tooltip content={<CustomTooltip />} />
                
                {/* Main price line with performance-based coloring */}
                <Line 
                  type="linear" 
                  dataKey="close" 
                  stroke={lineColor}
                  strokeWidth={2.5}
                  dot={false}  // Hide individual data point dots
                  activeDot={{ r: 6, fill: lineColor, stroke: '#ffffff', strokeWidth: 2 }}
                  isAnimationActive={false}  // Disable animations for better performance
                  connectNulls={false}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          
          {/* Timeframe selection buttons */}
          <div className="timeframe-buttons">
            {timeframes.map((tf) => (
              <button
                key={tf.value}
                onClick={() => setPeriod(tf.value)}
                className={`timeframe-button ${period === tf.value ? 'active' : ''}`}
              >
                {tf.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Add PredictionPanel when a ticker is selected */}
      {ticker && <PredictionPanel ticker={ticker} />}
    </div>
  )
}

export default App
