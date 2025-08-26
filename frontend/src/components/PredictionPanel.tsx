/**
 * PredictionPanel Component
 * =======================
 * 
 * This component provides a user interface for getting stock price predictions.
 * It allows users to select a future date and displays prediction results with
 * confidence intervals and probability estimates.
 */

import React, { useState } from 'react';
import axios from 'axios';
import { format, addDays } from 'date-fns';
import './PredictionPanel.css';

/**
 * Interface defining the structure of prediction data received from the API
 * Includes current price, predictions, confidence intervals, and probabilities
 */
interface PredictionData {
  ticker: string;
  prediction: {
    current_price: number;      // Current stock price
    target_date: string;        // Target date for prediction
    median_prediction: number;   // Most likely predicted price
    confidence_intervals: {      // Price ranges with confidence levels
      '80': [number, number];   // 80% confidence interval [lower, upper]
      '95': [number, number];   // 95% confidence interval [lower, upper]
    };
    probability_within_5_percent: number;  // Probability of price within ±5% of median
  };
}

/**
 * Props interface for the PredictionPanel component
 */
interface PredictionPanelProps {
  ticker: string | null;  // Current stock ticker symbol
}

/**
 * PredictionPanel Component
 * Displays a form for selecting prediction date and shows prediction results
 * 
 * @param {PredictionPanelProps} props - Component props
 * @param {string | null} props.ticker - The stock ticker to predict
 */
export default function PredictionPanel({ ticker }: PredictionPanelProps) {
  // State for managing the target prediction date
  const [targetDate, setTargetDate] = useState('');
  
  // State for storing the prediction results from the API
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  
  // Loading state for API calls
  const [loading, setLoading] = useState(false);
  
  // Error state for handling API errors
  const [error, setError] = useState('');

  /**
   * Calculate the valid date range for predictions
   * - Minimum date is tomorrow (can't predict the past)
   * - Maximum date is one year from now (predictions become less reliable beyond that)
   */
  const minDate = format(addDays(new Date(), 1), 'yyyy-MM-dd');
  const maxDate = format(addDays(new Date(), 365), 'yyyy-MM-dd');

  /**
   * Fetch price prediction from the backend API
   * Makes a GET request to /predict endpoint with ticker and target date
   * Updates the prediction state with the response data
   */
  const fetchPrediction = async () => {
    // Don't fetch if we don't have required data
    if (!ticker || !targetDate) return;

    setLoading(true);
    setError('');
    try {
      // Make API request to get prediction
      const response = await axios.get<PredictionData>(
        `http://localhost:8000/predict?ticker=${ticker}&target_date=${targetDate}`
      );
      setPrediction(response.data);
    } catch (err) {
      // Handle any API errors
      setError('Failed to fetch prediction. Please try again.');
      console.error('Prediction error:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Format a price number as a currency string
   * @param {number} price - The price to format
   * @returns {string} Formatted price with dollar sign and 2 decimal places
   */
  const formatPrice = (price: number) => `$${price.toFixed(2)}`;

  // Don't render anything if no ticker is selected
  if (!ticker) return null;

  return (
    <div className="prediction-panel">
      <h2>Price Prediction</h2>
      
      {/* Date selection and prediction trigger section */}
      <div className="prediction-input">
        <label htmlFor="target-date">Target Date:</label>
        <input
          id="target-date"
          type="date"
          value={targetDate}
          onChange={(e) => setTargetDate(e.target.value)}
          min={minDate}    // Can't predict the past
          max={maxDate}    // Limit to 1 year in the future
        />
        <button 
          onClick={fetchPrediction}
          disabled={loading || !targetDate}
          className="predict-button"
        >
          {loading ? 'Predicting...' : 'Predict Price'}
        </button>
      </div>

      {/* Error message display */}
      {error && <div className="error">{error}</div>}

      {/* Prediction results section */}
      {prediction && (
        <div className="prediction-results">
          {/* Current price information */}
          <div className="current-price-info">
            <span>Current Price:</span>
            <span className="price">{formatPrice(prediction.prediction.current_price)}</span>
          </div>
          
          {/* Prediction details section */}
          <div className="prediction-info">
            <h3>Prediction for {prediction.prediction.target_date}</h3>
            
            {/* Median prediction (most likely price) */}
            <div className="median-prediction">
              <span>Median Prediction:</span>
              <span className="price">{formatPrice(prediction.prediction.median_prediction)}</span>
            </div>
            
            {/* Confidence intervals (price ranges) */}
            <div className="confidence-intervals">
              {/* 80% confidence interval - more likely range */}
              <div className="interval">
                <span>80% Confidence Interval:</span>
                <span className="range">
                  {formatPrice(prediction.prediction.confidence_intervals['80'][0])} - {formatPrice(prediction.prediction.confidence_intervals['80'][1])}
                </span>
              </div>
              {/* 95% confidence interval - wider range */}
              <div className="interval">
                <span>95% Confidence Interval:</span>
                <span className="range">
                  {formatPrice(prediction.prediction.confidence_intervals['95'][0])} - {formatPrice(prediction.prediction.confidence_intervals['95'][1])}
                </span>
              </div>
            </div>
            
            {/* Probability estimate */}
            <div className="probability">
              <span>Probability within ±5% of median:</span>
              <span className="percentage">{prediction.prediction.probability_within_5_percent}%</span>
            </div>

            {/* Visual representation of the prediction ranges */}
            <div className="prediction-visualization">
              <div className="price-range">
                {/* Main range container with CSS variables for dynamic positioning */}
                <div 
                  className="range-95"
                  style={{
                    // CSS variables for dynamic positioning of elements
                    '--min-price': prediction.prediction.confidence_intervals['95'][0],
                    '--max-price': prediction.prediction.confidence_intervals['95'][1],
                    '--current-price': prediction.prediction.current_price,
                    '--median-price': prediction.prediction.median_prediction
                  } as React.CSSProperties}
                >
                  {/* 80% confidence interval band */}
                  <div className="range-80"></div>
                  {/* Median prediction marker with label */}
                  <div className="median-line">
                    <span className="line-label">Predicted</span>
                  </div>
                  {/* Current price marker with label */}
                  <div className="current-line">
                    <span className="line-label">Current</span>
                  </div>
                </div>
              </div>
              {/* Price labels for the visualization */}
              <div className="range-labels">
                <span>{formatPrice(prediction.prediction.confidence_intervals['95'][0])}</span>
                <span>{formatPrice(prediction.prediction.median_prediction)}</span>
                <span>{formatPrice(prediction.prediction.confidence_intervals['95'][1])}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
