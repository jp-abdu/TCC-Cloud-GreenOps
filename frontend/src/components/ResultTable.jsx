// frontend/src/components/ResultTable.jsx
import { useState } from 'react'
import { COLORS } from '../lib/constants'
import { getLatencyLabel } from '../lib/pareto'

const COLUMNS = [
  { key: 'region',         label: 'Região',          sortKey: 'region' },
  { key: 'sci_score',      label: 'SCI (gCO₂/h)',    sortKey: 'sci_score' },
  { key: 'cost_usd_month', label: 'Custo/mês',       sortKey: 'cost_usd_month' },
  { key: 'latency_ms',     label: 'Latência',        sortKey: 'latency_ms' },
  { key: 'status',         label: 'Status',          sortKey: 'pareto_optimal' },
]

export default function ResultTable({ scenarios, baseRegion, presorted = false, onResetSort }) {
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState('asc')

  // Expõe função de reset para o pai (EfficiencyIndex)
  if (onResetSort) onResetSort.current = () => setSortKey(null)

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  // Se presorted=true e nenhuma coluna foi clicada, mantém a ordem recebida (do EfficiencyIndex)
  const sorted = (presorted && !sortKey)
    ? scenarios
    : [...scenarios].sort((a, b) => {
        const key = sortKey || 'sci_score'
        let va = a[key]
        let vb = b[key]
        if (key === 'pareto_optimal') { va = a.pareto_optimal ? 0 : 1; vb = b.pareto_optimal ? 0 : 1 }
        if (key === 'latency_ms')     { va = a.latency_ms ?? 9999; vb = b.latency_ms ?? 9999 }
        if (typeof va === 'string') return sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va)
        return sortDir === 'asc' ? va - vb : vb - va
      })

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{
        width: '100%', borderCollapse: 'collapse',
        fontSize: '13px', fontFamily: 'IBM Plex Sans, sans-serif',
      }}>
        <thead>
          <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
            {COLUMNS.map(col => (
              <th key={col.key} onClick={() => handleSort(col.sortKey)} style={{
                padding: '10px 12px', textAlign: 'left',
                color: sortKey === col.sortKey ? COLORS.green : COLORS.text3,
                fontWeight: 500, fontSize: '11px',
                textTransform: 'uppercase', letterSpacing: '0.6px',
                cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap',
              }}>
                {col.label}
                {sortKey === col.sortKey && (
                  <span style={{ marginLeft: '4px' }}>{sortDir === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((sc, i) => {
            const isPareto = sc.pareto_optimal
            const isBase   = sc.region === baseRegion
            const lat      = getLatencyLabel(sc.latency_ms)
            return (
              <tr key={sc.region} style={{
                background: i % 2 === 0 ? COLORS.bg2 : COLORS.bg,
                borderBottom: `1px solid ${COLORS.border}`,
              }}>
                <td style={{
                  padding: '10px 12px',
                  color: isPareto ? COLORS.green : COLORS.text,
                  fontWeight: isPareto ? 600 : 400,
                }}>
                  {sc.region}{isBase ? ' ★' : ''}
                </td>
                <td style={{ padding: '10px 12px', color: COLORS.text, fontFamily: 'IBM Plex Mono, monospace' }}>
                  {sc.sci_score?.toFixed(4)}
                </td>
                <td style={{ padding: '10px 12px', color: COLORS.text, fontFamily: 'IBM Plex Mono, monospace' }}>
                  ${sc.cost_usd_month?.toFixed(2)}
                </td>
                <td style={{ padding: '10px 12px' }}>{lat.label}</td>
                <td style={{
                  padding: '10px 12px',
                  color: isPareto ? COLORS.green : COLORS.text3,
                  fontWeight: isPareto ? 600 : 400,
                }}>
                  {isPareto ? 'Pareto ótimo' : 'Dominado'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
