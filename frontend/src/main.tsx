/**
 * Main Entry Point for Stock Forecast Application
 * ===============================================
 * 
 * This file is the entry point for the React application. It:
 * - Imports the main App component
 * - Sets up the React root for rendering
 * - Wraps the app in StrictMode for development debugging
 * - Renders the application into the DOM
 * 
 * The main.tsx file is the bridge between the HTML page and the React application.
 * It's responsible for mounting the React app into the DOM element with id 'root'.
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Create the React root and render the application
// createRoot is the modern React 18+ way to render React applications
// It provides better performance and concurrent features
createRoot(document.getElementById('root')!).render(
  // StrictMode helps identify potential problems during development
  // It runs effects twice and warns about deprecated lifecycle methods
  <StrictMode>
    <App />
  </StrictMode>,
)
