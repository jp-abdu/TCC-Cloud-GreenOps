import { useState, useEffect } from 'react'
import { calculateInstance, getRegions, getInstances } from '../lib/api'
import { DEFAULT_REGIONS, DEFAULT_INSTANCE, COLORS } from '../lib/constants'
import RegionSelector from '../components/RegionSelector'
import ParetoChart from '../components/ParetoChart'
import ResultTable from '../components/ResultTable'
import MetricCard from '../components/MetricCard'
import EfficiencyIndex from '../components/EfficiencyIndex'

const SidebarSection = ({ label, children }) => (
  <div style={{ marginBottom: '20px' }}>
    <div style={{
      fontSize: '10px', fontWeight: 700, color: COLORS.text3,
      textTransform: 'uppercase', letterSpacing: '1.5px',
      marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px',
    }}>
      <span style={{ width: '12px', height: '1px', background: COLORS.border }} />
      {label}
    </div>
    {children}
  </div>
)

const selectStyle = {
  width: '100%', padding: '8px 10px', background: COLORS.bg3,
  border: `1px solid ${COLORS.border}`, borderRadius: '6px',
  color: COLORS.text, fontSize: '13px',
}

export default function InstancePage() {
  const [regions, setRegions] = useState([])
  const [instances, setInstances] = useState([])
  const [selectedRegions, setSelectedRegions] = useState(DEFAULT_REGIONS)
  const [instance, setInstance] = useState(DEFAULT_INSTANCE)
  const [baseRegion, setBaseRegion] = useState('us-east-1')
  const [cpu, setCpu] = useState(50)
  const [hours, setHours] = useState(730)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    getRegions().then(r => setRegions(r.data.regions))
    getInstances().then(r => setInstances(r.data.instances))
  }, [])

  const handleCalculate = async () => {
    if (selectedRegions.length === 0) { setError('Selecione ao menos uma região.'); return }
    setLoading(true); setError(null)
    try {
      const r = await calculateInstance({
        instance_type: instance,
        base_region: baseRegion,
        regions: selectedRegions,
        cpu_utilization: cpu / 100,
        hours_per_month: hours,
      })
      setResult(r.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao calcular.')
    } finally {
      setLoading(false)
    }
  }

  const s = result?.summary
  const base = result?.base

  return (
    <div style={{ display: 'flex', minHeight: 'calc(100vh - 112px)' }}>

      {/* Sidebar */}
      <aside style={{
        width: '280px', minWidth: '280px',
        background: COLORS.bg2,
        borderRight: `1px solid ${COLORS.border}`,
        padding: '24px 20px',
        overflowY: 'auto',
      }}>

        <SidebarSection label="Instância">
          <label style={{ fontSize: '12px', color: COLORS.text3, display: 'block', marginBottom: '5px' }}>Instância base</label>
          <select value={instance} onChange={e => setInstance(e.target.value)} style={selectStyle}>
            {instances.map(i => <option key={i} value={i}>{i}</option>)}
          </select>
          <label style={{ fontSize: '12px', color: COLORS.text3, display: 'block', marginTop: '10px', marginBottom: '5px' }}>Região base</label>
          <select value={baseRegion} onChange={e => setBaseRegion(e.target.value)} style={selectStyle}>
            {regions.map(r => <option key={r.id} value={r.id}>{r.id}</option>)}
          </select>
        </SidebarSection>

        <SidebarSection label="Parâmetros de uso">
          <div style={{
            background: COLORS.bg3, border: `1px solid ${COLORS.border}`,
            borderRadius: '6px', padding: '10px 12px', marginBottom: '12px',
            fontSize: '11px', color: COLORS.text3, lineHeight: 1.7,
          }}>
            <b style={{ color: COLORS.text2 }}>CPU:</b> 50% = baseline CCF para workloads gerais. Afeta o SCI.<br />
            <b style={{ color: COLORS.text2 }}>Horas:</b> 730h = operação 24/7. Afeta o custo mensal.
          </div>
          <label style={{ fontSize: '12px', color: COLORS.text3, display: 'block', marginBottom: '4px' }}>
            Utilização de CPU: <b style={{ color: COLORS.text }}>{cpu}%</b>
          </label>
          <input type="range" min={1} max={100} value={cpu}
            onChange={e => setCpu(Number(e.target.value))}
            className="ga-slider" style={{ marginBottom: '12px' }} />
          <label style={{ fontSize: '12px', color: COLORS.text3, display: 'block', marginBottom: '4px' }}>
            Horas por mês: <b style={{ color: COLORS.text }}>{hours}h</b>
          </label>
          <input type="range" min={1} max={730} value={hours}
            onChange={e => setHours(Number(e.target.value))}
            className="ga-slider" />
        </SidebarSection>

        <SidebarSection label="Regiões">
          <RegionSelector regions={regions} selected={selectedRegions} onChange={setSelectedRegions} />
        </SidebarSection>

        <button onClick={handleCalculate} disabled={loading} style={{
          width: '100%', padding: '12px',
          background: loading ? COLORS.bg3 : COLORS.green,
          color: loading ? COLORS.text3 : '#000',
          border: 'none', borderRadius: '6px', fontSize: '14px',
          fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
          letterSpacing: '0.3px',
        }}>
          {loading ? 'Calculando...' : 'Calcular'}
        </button>

        {error && (
          <div style={{ marginTop: '10px', fontSize: '12px', color: COLORS.red,
            background: 'rgba(224,82,82,0.08)', border: `1px solid rgba(224,82,82,0.3)`,
            borderRadius: '5px', padding: '8px 10px' }}>
            {error}
          </div>
        )}
      </aside>

      {/* Main */}
      <main style={{ flex: 1, padding: '32px 40px', overflowY: 'auto', background: COLORS.bg }}>
        {!result && !loading && (
          <div style={{ textAlign: 'center', marginTop: '120px' }}>
            <div style={{
              width: '64px', height: '64px', borderRadius: '16px',
              background: 'rgba(61,186,111,0.1)', border: `1px solid rgba(61,186,111,0.2)`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '28px', margin: '0 auto 20px',
            }}>🌿</div>
            <div style={{ fontSize: '16px', color: COLORS.text2, marginBottom: '6px' }}>Configure os parâmetros e clique em Calcular</div>
            <div style={{ fontSize: '13px', color: COLORS.text3 }}>Os resultados aparecerão aqui</div>
          </div>
        )}

        {loading && (
          <div style={{ textAlign: 'center', marginTop: '120px' }}>
            <div style={{ fontSize: '16px', color: COLORS.text2 }}>Calculando cenários...</div>
            <div style={{ fontSize: '13px', color: COLORS.text3, marginTop: '6px' }}>Buscando dados de preço e carbono</div>
          </div>
        )}

        {result && (
          <>
            {/* Título */}
            <div style={{ marginBottom: '24px', paddingBottom: '16px', borderBottom: `1px solid ${COLORS.border}` }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
                <h2 style={{ color: COLORS.text, fontSize: '22px', fontWeight: 600, margin: 0, fontFamily: 'IBM Plex Mono, monospace' }}>
                  {instance}
                </h2>
                <span style={{ fontSize: '13px', color: COLORS.text3 }}>
                  Resultados da análise de cenários
                </span>
              </div>
            </div>

            {/* Métricas */}
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '28px' }}>
              <MetricCard label="SCI do Cenário Base" value={base?.sci_score?.toFixed(4)} unit="gCO₂/h" sub={`$${base?.cost_usd_month?.toFixed(2)}/mês`} />
              <MetricCard label="Menor SCI encontrado" value={s?.best_sci?.sci_score?.toFixed(4)} unit="gCO₂/h" sub={s?.best_sci?.region} />
              <MetricCard label="Redução de carbono" value={`${s?.sci_reduction_pct}%`} unit="vs. cenário base" />
              <MetricCard label="Soluções Pareto ótimo" value={s?.pareto_count} unit={`de ${s?.total_scenarios} cenários`} />
            </div>

            {/* Banner */}
            {s?.best_sci && s.best_sci.region !== baseRegion && (
              <div style={{
                background: 'rgba(61,186,111,0.06)',
                border: `1px solid rgba(61,186,111,0.3)`,
                borderLeft: `3px solid ${COLORS.green}`,
                borderRadius: '8px', padding: '14px 18px',
                marginBottom: '28px', fontSize: '13px', color: COLORS.text2,
                display: 'flex', alignItems: 'center', gap: '10px',
              }}>
                <span style={{ color: COLORS.green, fontSize: '16px', flexShrink: 0 }}>↗</span>
                <span>
                  Melhor alternativa Pareto:{' '}
                  <b style={{ color: COLORS.green }}>{s.best_sci.region}</b>
                  {' '}—{' '}
                  <b style={{ color: COLORS.green }}>{s.sci_reduction_pct}% menos carbono</b>
                  {' '}e {s.best_sci.cost_usd_month < base?.cost_usd_month
                    ? `$${(base.cost_usd_month - s.best_sci.cost_usd_month).toFixed(2)}/mês mais barato`
                    : s.best_sci.cost_usd_month > base?.cost_usd_month
                    ? `$${(s.best_sci.cost_usd_month - base.cost_usd_month).toFixed(2)}/mês a mais`
                    : 'mesmo custo'} vs. base.
                </span>
              </div>
            )}

            {/* Pareto chart */}
            <div style={{
              background: COLORS.bg2, border: `1px solid ${COLORS.border}`,
              borderRadius: '10px', padding: '24px', marginBottom: '20px',
            }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: COLORS.text3, textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '16px' }}>
                Pareto Front: Custo vs. Carbono
              </div>
              <ParetoChart scenarios={result.all_scenarios} baseRegion={baseRegion} />
            </div>

            {/* Índice + Tabela */}
            <EfficiencyIndex scenarios={result.all_scenarios} baseRegion={baseRegion}>
              {(scored, resetSortRef) => (
                <div style={{
                  background: COLORS.bg2, border: `1px solid ${COLORS.border}`,
                  borderRadius: '10px', padding: '24px', marginTop: '16px',
                }}>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: COLORS.text3, textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '16px' }}>
                    Todos os cenários calculados
                  </div>
                  <ResultTable scenarios={scored} baseRegion={baseRegion} presorted={true} onResetSort={resetSortRef} />
                </div>
              )}
            </EfficiencyIndex>
          </>
        )}
      </main>
    </div>
  )
}
