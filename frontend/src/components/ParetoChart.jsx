// frontend/src/components/ParetoChart.jsx
import {
  ScatterChart, Scatter, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { COLORS } from '../lib/constants'

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div style={{
      background: COLORS.bg2,
      border: `1px solid ${COLORS.border}`,
      borderRadius: '6px',
      padding: '10px 14px',
      fontSize: '12px',
      color: COLORS.text,
      fontFamily: 'IBM Plex Sans, sans-serif',
    }}>
      <div style={{ fontWeight: 600, marginBottom: '6px', color: COLORS.text }}>{d.region}</div>
      <div style={{ color: COLORS.text2 }}>Custo: <b style={{ color: COLORS.text }}>${d.cost_usd_month?.toFixed(2)}/mês</b></div>
      <div style={{ color: COLORS.text2 }}>SCI: <b style={{ color: COLORS.text }}>{d.sci_score?.toFixed(4)} gCO₂/h</b></div>
      <div style={{ color: COLORS.text2 }}>Grid: <b style={{ color: COLORS.text }}>{d.carbon_intensity} gCO₂/kWh</b></div>
      {d.latency_ms != null && (
        <div style={{ color: COLORS.text2 }}>Latência: <b style={{ color: COLORS.text }}>{d.latency_ms} ms</b></div>
      )}
      <div style={{ marginTop: '6px', color: d.pareto_optimal ? COLORS.green : COLORS.text3, fontWeight: 500 }}>
        {d.pareto_optimal ? '● Pareto ótimo' : '○ Dominado'}
      </div>
    </div>
  )
}

const StarShape = (props) => {
  const { cx, cy } = props
  const size = 10
  const points = Array.from({ length: 5 }, (_, i) => {
    const outer = (Math.PI * 2 * i) / 5 - Math.PI / 2
    const inner = outer + Math.PI / 5
    return [
      cx + size * Math.cos(outer), cy + size * Math.sin(outer),
      cx + (size * 0.4) * Math.cos(inner), cy + (size * 0.4) * Math.sin(inner),
    ]
  }).flat()
  const d = points.reduce((acc, v, i) =>
    acc + (i % 2 === 0 ? (i === 0 ? `M${v}` : `L${v}`) : `,${v}`), '') + 'Z'
  return <path d={d} fill={COLORS.orange} stroke={COLORS.bg} strokeWidth={1} />
}

export default function ParetoChart({ scenarios, baseRegion }) {
  if (!scenarios?.length) return null

  const dominated = scenarios.filter(s => !s.pareto_optimal && s.region !== baseRegion)
  const pareto    = scenarios.filter(s => s.pareto_optimal && s.region !== baseRegion)
  const base      = scenarios.filter(s => s.region === baseRegion)

  const allX = scenarios.map(s => s.cost_usd_month)
  const allY = scenarios.map(s => s.sci_score)
  const padX = (Math.max(...allX) - Math.min(...allX)) * 0.1 || 10
  const padY = (Math.max(...allY) - Math.min(...allY)) * 0.1 || 1
  const domainX = [Math.max(0, Math.min(...allX) - padX), Math.max(...allX) + padX]
  const domainY = [Math.max(0, Math.min(...allY) - padY), Math.max(...allY) + padY]

  return (
    <div>
      <div style={{ fontSize: '11px', color: COLORS.text3, marginBottom: '12px' }}>
        Verde = Pareto ótimo · Cinza = Dominado · Estrela = região base
      </div>
      <ResponsiveContainer width="100%" height={360}>
        <ScatterChart margin={{ top: 20, right: 40, bottom: 60, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={COLORS.bg3} />
          <XAxis
            type="number"
            dataKey="cost_usd_month"
            domain={domainX}
            name="Custo/mês"
            tickFormatter={v => `$${v.toFixed(0)}`}
            tick={{ fill: COLORS.text3, fontSize: 11 }}
            label={{
              value: 'Custo mensal (USD)',
              position: 'insideBottom',
              offset: -15,
              fill: COLORS.text3,
              fontSize: 11,
            }}
          />
          <YAxis
            type="number"
            dataKey="sci_score"
            domain={domainY}
            name="SCI"
            tickFormatter={v => v.toFixed(1)}
            tick={{ fill: COLORS.text3, fontSize: 11 }}
            label={{
              value: 'SCI (gCO₂/h)',
              angle: -90,
              position: 'insideLeft',
              offset: 10,
              fill: COLORS.text3,
              fontSize: 11,
            }}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: COLORS.border }} />
          <Legend
            wrapperStyle={{ fontSize: '12px', color: COLORS.text2, paddingTop: '32px' }}
            iconSize={10}
            iconType="circle"
            formatter={(value) => (
              <span style={{ color: COLORS.text2, fontSize: '12px', marginRight: '20px' }}>{value}</span>
            )}
          />

          <Scatter name="Dominado"     data={dominated} fill={COLORS.text3} opacity={0.45} />
          <Scatter name="Pareto ótimo" data={pareto}    fill={COLORS.green}  opacity={0.95} />
          <Scatter
            name="Região base"
            data={base}
            shape={<StarShape />}
            opacity={1}
            legendType="star"
            fill={COLORS.orange}
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  )
}
