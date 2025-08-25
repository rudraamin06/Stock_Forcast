/**
 * Vite Configuration File
 * =======================
 * 
 * This file configures Vite, the build tool and development server for the frontend.
 * Vite provides fast development with hot module replacement (HMR) and optimized
 * production builds.
 * 
 * Key Features:
 * - React plugin for JSX/TSX support
 * - Fast development server with instant hot reload
 * - Optimized production builds
 * - TypeScript support out of the box
 */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite configuration object
// https://vite.dev/config/
export default defineConfig({
  // Plugins array - React plugin enables JSX/TSX compilation and Fast Refresh
  plugins: [react()],
  
  // Additional configuration options can be added here:
  // - server: Development server settings
  // - build: Production build options
  // - resolve: Module resolution settings
  // - css: CSS processing options
})
