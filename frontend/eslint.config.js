/**
 * ESLint Configuration
 * ====================
 * 
 * This file configures ESLint, a static code analysis tool that helps identify
 * and fix problems in JavaScript/TypeScript code. It enforces coding standards,
 * catches common errors, and ensures consistent code quality across the project.
 * 
 * Key Features:
 * - TypeScript support with type-aware linting
 * - React-specific rules for hooks and components
 * - Modern JavaScript features (ES2020)
 * - Browser environment globals
 * - Recommended rule sets for best practices
 */

import js from '@eslint/js'                    // Core ESLint JavaScript rules
import globals from 'globals'                  // Global variables for different environments
import reactHooks from 'eslint-plugin-react-hooks'      // React Hooks linting rules
import reactRefresh from 'eslint-plugin-react-refresh'  // React Fast Refresh rules
import tseslint from 'typescript-eslint'       // TypeScript ESLint integration
import { globalIgnores } from 'eslint/config'  // Global ignore patterns

// Export the ESLint configuration using the new flat config format
export default tseslint.config([
  // Ignore the dist/build directory globally
  globalIgnores(['dist']),
  
  // Configuration for TypeScript and TSX files
  {
    // Apply to all TypeScript and TSX files
    files: ['**/*.{ts,tsx}'],
    
    // Extend recommended configurations from various plugins
    extends: [
      js.configs.recommended,                    // ESLint recommended JavaScript rules
      tseslint.configs.recommended,              // TypeScript ESLint recommended rules
      reactHooks.configs['recommended-latest'],  // Latest React Hooks rules
      reactRefresh.configs.vite,                 // Vite-specific React Refresh rules
    ],
    
    // Language-specific options
    languageOptions: {
      ecmaVersion: 2020,                         // Support ES2020 features
      globals: globals.browser,                  // Include browser global variables
    },
  },
])
