import { COLORS } from '../lib/constants'

export default function MetricCard({ label, value, unit, sub, accent }) {
  const color = accent || COLORS.green

  return (
    <div style={{
      background: COLORS.bg2,
      border: `1px solid ${COLORS.border}`,
      borderTop: `2px solid ${color}`,
      borderRadius: '8px',
      padding: '18px 20px',
      flex: 1,
      minWidth: '160px',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Glow sutil no canto */}
      <div style={{
        position: 'absolute', top: 0, right: 0,
        width: '80px', height: '80px',
        background: `radial-gradient(circle at top right, ${color}18, transparent 70%)`,
        pointerEvents: 'none',
      }} />

      <div style={{
        fontSize: '10px',
        color: COLORS.text3,
        textTransform: 'uppercase',
        letterSpacing: '1px',
        marginBottom: '10px',
        fontFamily: 'IBM Plex Sans, sans-serif',
        fontWeight: 600,
      }}>
        {label}
      </div>

      <div style={{
        fontSize: '28px',
        fontWeight: 600,
        color: COLORS.text,
        fontFamily: 'IBM Plex Mono, monospace',
        lineHeight: 1.1,
        marginBottom: '4px',
      }}>
        {value ?? '—'}
      </div>

      {unit && (
        <div style={{
          fontSize: '11px',
          color: COLORS.text3,
          marginTop: '4px',
          fontFamily: 'IBM Plex Mono, monospace',
        }}>
          {unit}
        </div>
      )}

      {sub && (
        <div style={{
          fontSize: '12px',
          color: color,
          marginTop: '6px',
          fontWeight: 500,
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
        }}>
          <span style={{ fontSize: '8px' }}>▲</span>
          {sub}
        </div>
      )}
    </div>
  )
}
