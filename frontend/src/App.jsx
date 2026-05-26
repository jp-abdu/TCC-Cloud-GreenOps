import { useState } from 'react'
import Header from './components/Header'
import OverviewPage from './pages/OverviewPage'
import InstancePage from './pages/InstancePage'
import ArchitecturePage from './pages/ArchitecturePage'
import { COLORS } from './lib/constants'

const TABS = [
  { id: 'overview', label: 'Visão Geral' },
  { id: 'instance', label: 'Instância' },
  { id: 'architecture', label: 'Arquitetura' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <div style={{
      minHeight: '100vh',
      background: COLORS.bg,
      color: COLORS.text,
      fontFamily: "'IBM Plex Sans', sans-serif",
    }}>
      <link
        href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap"
        rel="stylesheet"
      />

      <Header />

      {/* Tabs */}
      <div style={{
        background: COLORS.bg2,
        borderBottom: `1px solid ${COLORS.border}`,
        padding: '0 48px',
        display: 'flex',
        gap: '0',
      }}>
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '14px 24px',
              background: 'none',
              border: 'none',
              borderBottom: activeTab === tab.id
                ? `2px solid ${COLORS.green}`
                : '2px solid transparent',
              color: activeTab === tab.id ? COLORS.text : COLORS.text2,
              fontSize: '15px',
              cursor: 'pointer',
              fontFamily: "'IBM Plex Sans', sans-serif",
              fontWeight: activeTab === tab.id ? 500 : 400,
              transition: 'color 0.15s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div>
        {activeTab === 'overview' && <OverviewPage />}
        {activeTab === 'instance' && <InstancePage />}
        {activeTab === 'architecture' && <ArchitecturePage />}
      </div>
    </div>
  )
}