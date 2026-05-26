import { COLORS } from '../lib/constants'

export default function Header() {
  return (
    <header style={{
      background: COLORS.bg2,
      borderBottom: `1px solid ${COLORS.border}`,
      padding: '0 48px',
      height: '72px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
        <span style={{
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: '28px',
          fontWeight: 500,
          color: COLORS.text,
          letterSpacing: '-1px',
        }}>
          Green<span style={{ color: COLORS.green }}>Arch</span>
        </span>
        <span style={{
          fontSize: '11px',
          color: COLORS.text3,
          letterSpacing: '1px',
          textTransform: 'uppercase',
        }}>
          Carbon & Cost Intelligence for AWS
        </span>
      </div>
      <span style={{
        fontSize: '11px',
        color: COLORS.green,
        border: `1px solid ${COLORS.green}`,
        borderRadius: '4px',
        padding: '3px 8px',
        letterSpacing: '0.5px',
      }}>
        ISO/IEC 21031:2024
      </span>
    </header>
  )
}