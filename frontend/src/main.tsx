import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './styles.css'

// 导入页面特定样式（使用命名空间隔离）
import './styles/home-page.css'
import './styles/ranking-management.css'
import './styles/guide-page.css'
import './styles/submission-review-page.css'
import './styles/historical-ranking-page.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
