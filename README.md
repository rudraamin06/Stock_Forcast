# Stock Forecast Application

A full-stack web application for real-time and historical stock market data visualization and analysis. Built with FastAPI (Python) for the backend and React + TypeScript + Vite for the frontend.

## Technologies Used

<p>
  <a href="https://fastapi.tiangolo.com/" target="_blank"><img src="https://img.shields.io/badge/FastAPI-005571?logo=fastapi&logoColor=white&style=for-the-badge" alt="FastAPI"></a>
  <a href="https://react.dev/" target="_blank"><img src="https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB&style=for-the-badge" alt="React"></a>
  <a href="https://www.typescriptlang.org/" target="_blank"><img src="https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white&style=for-the-badge" alt="TypeScript"></a>
  <a href="https://vitejs.dev/" target="_blank"><img src="https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=FFD62E&style=for-the-badge" alt="Vite"></a>
  <a href="https://yfinance.readthedocs.io/" target="_blank"><img src="https://img.shields.io/badge/yfinance-00A86B?logo=python&logoColor=white&style=for-the-badge" alt="yfinance"></a>
  <a href="https://pandas.pydata.org/" target="_blank"><img src="https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white&style=for-the-badge" alt="pandas"></a>
  <a href="https://axios-http.com/" target="_blank"><img src="https://img.shields.io/badge/Axios-5A29E4?logo=axios&logoColor=white&style=for-the-badge" alt="Axios"></a>
  <a href="https://recharts.org/" target="_blank"><img src="https://img.shields.io/badge/Recharts-FF7300?logo=recharts&logoColor=white&style=for-the-badge" alt="Recharts"></a>
  <a href="https://date-fns.org/" target="_blank"><img src="https://img.shields.io/badge/date--fns-007ACC?logo=date-fns&logoColor=white&style=for-the-badge" alt="date-fns"></a>
  <a href="https://eslint.org/" target="_blank"><img src="https://img.shields.io/badge/ESLint-4B32C3?logo=eslint&logoColor=white&style=for-the-badge" alt="ESLint"></a>
  <a href="https://uvicorn.org/" target="_blank"><img src="https://img.shields.io/badge/Uvicorn-000000?logo=python&logoColor=white&style=for-the-badge" alt="Uvicorn"></a>
</p>

## Features

- **Historical Stock Data:** View price history for major stocks across multiple timeframes (1D, 1W, 1M, 1Y, etc.).
- **Intraday Data:** Access minute-by-minute trading data for day trading and technical analysis.
- **Interactive Charts:** Responsive line charts with tooltips, color-coded performance, and timeframe selection.
- **Real-Time Updates:** Fetch the latest prices and volume data.
- **Modern UI:** Clean, responsive design for desktop and mobile.
- **Robust API:** FastAPI backend with CORS support, error handling, and flexible endpoints.

## Project Structure

```
Stock_Forcast/
├── backend/
│   ├── main.py              # FastAPI backend API
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/                 # React source code
│   ├── public/              # Static assets
│   ├── index.html           # HTML entry point
│   ├── package.json         # Frontend dependencies & scripts
│   └── ...                  # Config files (Vite, TypeScript, ESLint)
└── README.md                # Project documentation
```

## Getting Started

### Backend (FastAPI)

1. **Install Python dependencies:**
   ```sh
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the FastAPI server:**
   ```sh
   uvicorn main:app --reload --port 8000
   ```

   The API will be available at [http://localhost:8000](http://localhost:8000).

### Frontend (React + Vite)

1. **Install Node.js dependencies:**
   ```sh
   cd frontend
   npm install
   ```

2. **Start the development server:**
   ```sh
   npm run dev
   ```

   The app will be available at [http://localhost:5173](http://localhost:5173).

## API Endpoints

- `GET /health`  
  Health check endpoint.

- `GET /history?ticker=SYMBOL&period=PERIOD`  
  Fetch historical OHLCV data for a stock.  
  - `ticker`: Stock symbol (e.g., AAPL, MSFT)
  - `period`: 1d, 1w, 1mo, 1y, 2y, 5y, 10y, max

- `GET /intraday?ticker=SYMBOL&interval=INTERVAL`  
  Fetch intraday data with custom intervals.  
  - `interval`: 1m, 2m, 5m, 15m, 30m, 1h, 1d, etc.

## License

MIT License

##