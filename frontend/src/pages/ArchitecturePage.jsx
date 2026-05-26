import { useState, useEffect } from 'react'
import { calculateArchitecture, getRegions, getBenchmarks } from '../lib/api'
import { DEFAULT_REGIONS, COLORS } from '../lib/constants'
import RegionSelector from '../components/RegionSelector'
import ParetoChart from '../components/ParetoChart'
import ResultTable from '../components/ResultTable'
import MetricCard from '../components/MetricCard'
import EfficiencyIndex from '../components/EfficiencyIndex'

const ALL_RDS = [
  'db.t3.micro','db.t3.small','db.t3.medium','db.t3.large',
  'db.m5.large','db.m5.xlarge','db.m5.2xlarge',
  'db.r5.large','db.r5.xlarge',
]

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
  width: '100%', padding: '7px 10px', background: COLORS.bg3,
  border: `1px solid ${COLORS.border}`, borderRadius: '6px',
  color: COLORS.text, fontSize: '13px',
}

export default function ArchitecturePage() {
  const [regions, setRegions] = useState([])
  const [benchmarks, setBenchmarks] = useState([])
  const [selectedRegions, setSelectedRegions] = useState(DEFAULT_REGIONS)
  const [baseRegion, setBaseRegion] = useState('us-east-1')
  const [components, setComponents] = useState([])
  const [archName, setArchName] = useState('Minha Arquitetura')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [newType, setNewType] = useState('EC2')
  const [newInst, setNewInst] = useState('m5.large')
  const [newRdsInst, setNewRdsInst] = useState('db.m5.large')
  const [newEngine, setNewEngine] = useState('MySQL')
  const [newMultiAz, setNewMultiAz] = useState(false)
  const [newInvocations, setNewInvocations] = useState(5)
  const [newDuration, setNewDuration] = useState(100)
  const [newMemory, setNewMemory] = useState(256)
  const [newCpu, setNewCpu] = useState(50)
  const [newHours, setNewHours] = useState(730)

  useEffect(() => {
    getRegions().then(r => setRegions(r.data.regions))
    getBenchmarks().then(r => setBenchmarks(r.data.benchmarks))
  }, [])

  const loadBenchmark = (bm) => {
    setArchName(bm.name)
    setBaseRegion(bm.base_region || 'us-east-1')
    setComponents(bm.components.map((c, i) => ({ ...c, id: i })))
    setResult(null)
  }

  const addComponent = () => {
    const id = Date.now()
    if (newType === 'EC2') {
      setComponents([...components, { id, type: 'ec2', instance: newInst, hours: newHours, cpu: newCpu / 100, os: 'Linux', label: `EC2 ${newInst} | ${newHours}h | ${newCpu}% CPU` }])
    } else if (newType === 'RDS') {
      setComponents([...components, { id, type: 'rds', instance: newRdsInst, engine: newEngine, multi_az: newMultiAz, hours: newHours, cpu: newCpu / 100, label: `RDS ${newRdsInst} | ${newEngine}` }])
    } else {
      setComponents([...components, { id, type: 'lambda', invocations: newInvocations * 1_000_000, duration_ms: newDuration, memory_mb: newMemory, label: `Lambda | ${newInvocations}M inv | ${newDuration}ms | ${newMemory}MB` }])
    }
  }

  const removeComponent = (id) => setComponents(components.filter(c => c.id !== id))

  const handleCalculate = async () => {
    if (!components.length) { setError('Adicione ao menos um componente.'); return }
    if (!selectedRegions.length) { setError('Selecione ao menos uma região.'); return }
    setLoading(true); setError(null)
    try {
      const r = await calculateArchitecture({
        name: archName, base_region: baseRegion,
        regions: selectedRegions,
        components: components.map(({ id, ...c }) => c),
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
        width: '300px', minWidth: '300px',
        background: COLORS.bg2, borderRight: `1px solid ${COLORS.border}`,
        padding: '24px 20px', overflowY: 'auto',
      }}>

        <SidebarSection label="Benchmarks">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {benchmarks.map(bm => (
              <button key={bm.id} onClick={() => loadBenchmark(bm)} style={{
                padding: '5px 10px', fontSize: '11px',
                background: COLORS.bg3, border: `1px solid ${COLORS.border}`,
                borderRadius: '4px', color: COLORS.text2, cursor: 'pointer',
                transition: 'border-color 0.15s',
              }}>
                {bm.name}
              </button>
            ))}
          </div>
        </SidebarSection>

        <SidebarSection label="Configuração">
          <label style={{ fontSize: '12px', color: COLORS.text3, display: 'block', marginBottom: '4px' }}>Nome</label>
          <input value={archName} onChange={e => setArchName(e.target.value)} style={{
            ...selectStyle, marginBottom: '10px', boxSizing: 'border-box',
          }} />
          <label style={{ fontSize: '12px', color: COLORS.text3, display: 'block', marginBottom: '4px' }}>Região base</label>
          <select value={baseRegion} onChange={e => setBaseRegion(e.target.value)} style={selectStyle}>
            {regions.map(r => <option key={r.id} value={r.id}>{r.id}</option>)}
          </select>
        </SidebarSection>

        <SidebarSection label="Componentes">
          {components.length === 0 && (
            <div style={{ fontSize: '12px', color: COLORS.text3, padding: '8px 0' }}>
              Nenhum componente adicionado
            </div>
          )}
          {components.map(c => (
            <div key={c.id} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              background: COLORS.bg3, border: `1px solid ${COLORS.border}`,
              borderRadius: '6px', padding: '8px 10px', marginBottom: '6px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
                <span style={{
                  fontSize: '9px', fontWeight: 700, color: COLORS.green,
                  background: 'rgba(61,186,111,0.12)', border: `1px solid rgba(61,186,111,0.25)`,
                  borderRadius: '3px', padding: '2px 5px', fontFamily: 'IBM Plex Mono, monospace',
                }}>
                  {c.type?.toUpperCase()}
                </span>
                <span style={{ color: COLORS.text2, fontSize: '11px', flex: 1 }}>{c.label || c.instance}</span>
              </div>
              <button onClick={() => removeComponent(c.id)} style={{
                background: 'none', border: 'none', color: COLORS.text3,
                cursor: 'pointer', fontSize: '16px', padding: '0 4px', lineHeight: 1,
              }}>×</button>
            </div>
          ))}

          <details style={{ marginTop: '8px' }}>
            <summary style={{
              fontSize: '12px', color: COLORS.green, cursor: 'pointer',
              padding: '8px 10px', background: 'rgba(61,186,111,0.06)',
              border: `1px solid rgba(61,186,111,0.2)`, borderRadius: '6px',
              listStyle: 'none', display: 'flex', alignItems: 'center', gap: '6px',
            }}>
              <span>+</span> Adicionar componente
            </summary>
            <div style={{ marginTop: '10px', fontSize: '12px', color: COLORS.text2 }}>
              <label style={{ display: 'block', marginBottom: '4px', color: COLORS.text3 }}>Tipo</label>
              <select value={newType} onChange={e => setNewType(e.target.value)} style={{ ...selectStyle, marginBottom: '8px' }}>
                <option>EC2</option><option>RDS</option><option>Lambda</option>
              </select>

              {newType === 'EC2' && <>
                <label style={{ display: 'block', marginBottom: '4px', color: COLORS.text3 }}>Instância</label>
                <input value={newInst} onChange={e => setNewInst(e.target.value)} style={{ ...selectStyle, marginBottom: '8px', boxSizing: 'border-box' }} />
              </>}

              {newType === 'RDS' && <>
                <label style={{ display: 'block', marginBottom: '4px', color: COLORS.text3 }}>Instância RDS</label>
                <select value={newRdsInst} onChange={e => setNewRdsInst(e.target.value)} style={{ ...selectStyle, marginBottom: '8px' }}>
                  {ALL_RDS.map(r => <option key={r}>{r}</option>)}
                </select>
                <label style={{ display: 'block', marginBottom: '4px', color: COLORS.text3 }}>Engine</label>
                <select value={newEngine} onChange={e => setNewEngine(e.target.value)} style={{ ...selectStyle, marginBottom: '8px' }}>
                  <option>MySQL</option><option>PostgreSQL</option><option>MariaDB</option>
                </select>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px', cursor: 'pointer', fontSize: '12px', color: COLORS.text2 }}>
                  <input type="checkbox" checked={newMultiAz} onChange={e => setNewMultiAz(e.target.checked)} style={{ accentColor: COLORS.green }} />
                  Multi-AZ
                </label>
              </>}

              {newType === 'Lambda' && <>
                <label style={{ display: 'block', marginBottom: '4px', color: COLORS.text3 }}>Invocações/mês (M)</label>
                <input type="number" value={newInvocations} onChange={e => setNewInvocations(Number(e.target.value))} style={{ ...selectStyle, marginBottom: '8px', boxSizing: 'border-box' }} />
                <label style={{ display: 'block', marginBottom: '4px', color: COLORS.text3 }}>Duração (ms)</label>
                <input type="number" value={newDuration} onChange={e => setNewDuration(Number(e.target.value))} style={{ ...selectStyle, marginBottom: '8px', boxSizing: 'border-box' }} />
                <label style={{ display: 'block', marginBottom: '4px', color: COLORS.text3 }}>Memória (MB)</label>
                <input type="number" value={newMemory} onChange={e => setNewMemory(Number(e.target.value))} style={{ ...selectStyle, marginBottom: '8px', boxSizing: 'border-box' }} />
              </>}

              {newType !== 'Lambda' && <>
                <label style={{ display: 'block', marginBottom: '4px', color: COLORS.text3 }}>CPU: {newCpu}%</label>
                <input type="range" min={1} max={100} value={newCpu} onChange={e => setNewCpu(Number(e.target.value))} className="ga-slider" style={{ marginBottom: '8px' }} />
                <label style={{ display: 'block', marginBottom: '4px', color: COLORS.text3 }}>Horas/mês: {newHours}h</label>
                <input type="range" min={1} max={730} value={newHours} onChange={e => setNewHours(Number(e.target.value))} className="ga-slider" style={{ marginBottom: '8px' }} />
              </>}

              <button onClick={addComponent} style={{
                width: '100%', padding: '8px', background: 'rgba(61,186,111,0.08)',
                border: `1px solid rgba(61,186,111,0.3)`, borderRadius: '5px',
                color: COLORS.green, cursor: 'pointer', fontSize: '12px', fontWeight: 500,
              }}>
                Adicionar
              </button>
            </div>
          </details>
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
          {loading ? 'Calculando...' : 'Calcular arquitetura'}
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
            }}>🏗️</div>
            <div style={{ fontSize: '16px', color: COLORS.text2, marginBottom: '6px' }}>Carregue um benchmark ou monte sua arquitetura</div>
            <div style={{ fontSize: '13px', color: COLORS.text3 }}>Os resultados aparecerão aqui</div>
          </div>
        )}

        {loading && (
          <div style={{ textAlign: 'center', marginTop: '120px' }}>
            <div style={{ fontSize: '16px', color: COLORS.text2 }}>Calculando arquitetura...</div>
            <div style={{ fontSize: '13px', color: COLORS.text3, marginTop: '6px' }}>Buscando dados de preço e carbono para cada região</div>
          </div>
        )}

        {result && (
          <>
            <div style={{ marginBottom: '24px', paddingBottom: '16px', borderBottom: `1px solid ${COLORS.border}` }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
                <h2 style={{ color: COLORS.text, fontSize: '22px', fontWeight: 600, margin: 0 }}>{archName}</h2>
                <span style={{ fontSize: '13px', color: COLORS.text3 }}>Resultados por região</span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '28px' }}>
              <MetricCard label="SCI da Região Base" value={base?.sci_score?.toFixed(4)} unit="gCO₂/h" sub={base?.region} />
              <MetricCard label="Menor SCI encontrado" value={s?.best_sci?.sci_score?.toFixed(4)} unit="gCO₂/h" sub={s?.best_sci?.region} />
              <MetricCard label="Redução de carbono" value={`${s?.sci_reduction_pct}%`} unit="vs. região base" />
              <MetricCard label="Soluções Pareto ótimo" value={s?.pareto_count} unit={`de ${s?.total_scenarios} regiões`} />
            </div>

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
                  Melhor região:{' '}
                  <b style={{ color: COLORS.green }}>{s.best_sci.region}</b>
                  <b style={{ color: COLORS.green }}>, {s.sci_reduction_pct}% menos carbono</b>
                  {s.best_sci.cost_usd_month < base?.cost_usd_month
                    ? ` e $${(base.cost_usd_month - s.best_sci.cost_usd_month).toFixed(2)}/mês mais barato`
                    : s.best_sci.cost_usd_month > base?.cost_usd_month
                    ? ` e $${(s.best_sci.cost_usd_month - base.cost_usd_month).toFixed(2)}/mês a mais`
                    : ' e mesmo custo'} vs. {baseRegion}.
                </span>
              </div>
            )}

            <div style={{ background: COLORS.bg2, border: `1px solid ${COLORS.border}`, borderRadius: '10px', padding: '24px', marginBottom: '20px' }}>
              <div style={{ fontSize: '11px', fontWeight: 700, color: COLORS.text3, textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '16px' }}>
                Pareto Front: Custo vs. Carbono
              </div>
              <ParetoChart scenarios={result.all_scenarios} baseRegion={baseRegion} />
            </div>

            <EfficiencyIndex scenarios={result.all_scenarios} baseRegion={baseRegion}>
              {(scored, resetSortRef) => (
                <div style={{ background: COLORS.bg2, border: `1px solid ${COLORS.border}`, borderRadius: '10px', padding: '24px', marginTop: '16px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: COLORS.text3, textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '16px' }}>
                    Todas as regiões calculadas
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
