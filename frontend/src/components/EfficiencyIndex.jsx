// frontend/src/components/EfficiencyIndex.jsx
import { useState, useMemo, useRef, useCallback } from 'react'
import { COLORS } from '../lib/constants'

const sliderStyle = document.createElement('style')
sliderStyle.textContent = `
  .ga-slider {
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    height: 4px;
    border-radius: 2px;
    background: linear-gradient(90deg, #E8963A, #252825 50%, #3DBA6F);
    outline: none;
    cursor: pointer;
  }
  .ga-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #E8EDE9;
    border: 2px solid #3DBA6F;
    box-shadow: 0 0 0 3px rgba(61,186,111,0.15);
    cursor: pointer;
    transition: box-shadow 0.15s, transform 0.15s;
  }
  .ga-slider::-webkit-slider-thumb:hover {
    box-shadow: 0 0 0 5px rgba(61,186,111,0.2);
    transform: scale(1.1);
  }
  .ga-slider::-moz-range-thumb {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #E8EDE9;
    border: 2px solid #3DBA6F;
    cursor: pointer;
  }
`
if (!document.head.querySelector('[data-ga-slider]')) {
  sliderStyle.setAttribute('data-ga-slider', '1')
  document.head.appendChild(sliderStyle)
}

export default function EfficiencyIndex({ scenarios, baseRegion, children }) {
  const [weight, setWeight] = useState(50)
  const resetSortRef = useRef(null)

  const handleWeight = useCallback((val) => {
    setWeight(val)
    if (resetSortRef.current) resetSortRef.current()
  }, [])

  const scored = useMemo(() => {
    if (!scenarios?.length) return []

    const scis  = scenarios.map(s => s.sci_score)
    const costs = scenarios.map(s => s.cost_usd_month)
    const minSci  = Math.min(...scis),  maxSci  = Math.max(...scis)
    const minCost = Math.min(...costs), maxCost = Math.max(...costs)

    return [...scenarios]
      .map(s => {
        const sciN  = maxSci  === minSci  ? 0 : (s.sci_score - minSci)       / (maxSci  - minSci)
        const costN = maxCost === minCost ? 0 : (s.cost_usd_month - minCost) / (maxCost - minCost)
        const score = -(sciN * (weight / 100) + costN * (1 - weight / 100)) * 100
        return { ...s, score: Math.round(score * 10) / 10 }
      })
      .sort((a, b) => b.score - a.score)
  }, [scenarios, weight])

  if (!scenarios?.length) return null

  // Posição do label acompanhando o thumb (thumb tem 18px, trilha começa/termina a 9px das bordas)
  const thumbOffset = weight / 100
  const labelLeft = `calc(${thumbOffset * 100}% - ${thumbOffset * 40}px + 4px)`

  return (
    <div style={{
      background: COLORS.bg2,
      border: `1px solid ${COLORS.border}`,
      borderRadius: '10px',
      padding: '20px 24px',
      marginBottom: '20px',
    }}>
      <div style={{ marginBottom: '14px' }}>
        <div style={{
          fontSize: '11px', fontWeight: 700, color: COLORS.text3,
          textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '4px',
        }}>
          Índice de Eficiência
        </div>
        <div style={{ fontSize: '12px', color: COLORS.text3 }}>
          Ajuste o peso para priorizar carbono ou custo. A tabela reordena automaticamente.
        </div>
      </div>

      {/* Slider */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '12px', color: COLORS.text3 }}>Prioridade: Custo</span>
          <span style={{ fontSize: '12px', color: COLORS.text3 }}>Carbono</span>
        </div>

        {/* Label flutuante */}
        <div style={{ position: 'relative', marginBottom: '6px' }}>
          <div style={{
            position: 'absolute',
            left: labelLeft,
            top: '-22px',
            transform: 'translateX(-50%)',
            fontSize: '11px', fontWeight: 700,
            color: COLORS.green,
            fontFamily: 'IBM Plex Mono, monospace',
            background: COLORS.bg3,
            border: `1px solid rgba(61,186,111,0.3)`,
            borderRadius: '4px',
            padding: '1px 6px',
            whiteSpace: 'nowrap',
            pointerEvents: 'none',
          }}>
            {weight}%
          </div>

          <input
            className="ga-slider"
            type="range" min={0} max={100} step={10} value={weight}
            onChange={e => handleWeight(Number(e.target.value))}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '10px', color: COLORS.text3 }}>0%</span>
          <span style={{ fontSize: '10px', color: COLORS.text3 }}>100%</span>
        </div>
      </div>

      {children && children(scored, resetSortRef)}
    </div>
  )
}
