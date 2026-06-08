import './assets/main.css'

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { ErrorBoundary } from './components/ErrorBoundary'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <div className="h-screen w-screen overflow-hidden">
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </div>
  </StrictMode>
)
