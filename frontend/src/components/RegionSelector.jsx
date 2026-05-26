import { COLORS } from '../lib/constants'

export default function RegionSelector({ regions, selected, onChange }) {
  const grouped = {
    'North America': ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ca-central-1'],
    'Europe': ['eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1', 'eu-north-1', 'eu-south-1'],
    'South America': ['sa-east-1'],
    'Asia Pacific': ['ap-south-1', 'ap-northeast-1', 'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2'],
    'Middle East & Africa': ['me-south-1', 'af-south-1'],
  }

  const toggle = (reg) => {
    if (selected.includes(reg)) {
      onChange(selected.filter(r => r !== reg))
    } else {
      onChange([...selected, reg])
    }
  }

  const available = regions.map(r => r.id)

  return (
    <div>
      {Object.entries(grouped).map(([group, regs]) => {
        const groupRegs = regs.filter(r => available.includes(r))
        if (!groupRegs.length) return null
        return (
          <div key={group} style={{ marginBottom: '12px' }}>
            <div style={{
              fontSize: '10px',
              color: COLORS.text3,
              textTransform: 'uppercase',
              letterSpacing: '0.8px',
              marginBottom: '6px',
            }}>
              {group}
            </div>
            {groupRegs.map(reg => {
              const info = regions.find(r => r.id === reg)
              const isSelected = selected.includes(reg)
              return (
                <label key={reg} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '4px 0',
                  cursor: 'pointer',
                  fontSize: '13px',
                  color: isSelected ? COLORS.text : COLORS.text2,
                }}>
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggle(reg)}
                    style={{ accentColor: COLORS.green }}
                  />
                  {reg}
                  {info?.renewable && (
                    <span style={{ fontSize: '10px', color: COLORS.green }}>♻</span>
                  )}
                </label>
              )
            })}
          </div>
        )
      })}
    </div>
  )
}