import { COLORS } from '../lib/constants'

const styleEl = document.createElement('style')
styleEl.textContent = `
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50%       { opacity: 0.8; }
  }
  .fade-up { opacity: 0; animation: fadeUp 0.6s ease forwards; }
  .fade-up-1 { animation-delay: 0.05s; }
  .fade-up-2 { animation-delay: 0.15s; }
  .fade-up-3 { animation-delay: 0.25s; }
  .fade-up-4 { animation-delay: 0.35s; }
  .fade-up-5 { animation-delay: 0.45s; }
  .fade-up-6 { animation-delay: 0.55s; }
  .fade-up-7 { animation-delay: 0.65s; }
  .source-card:hover {
    border-color: #3DBA6F !important;
    transform: translateY(-2px);
    transition: all 0.2s ease;
  }
  .region-tag {
    display: inline-block;
    padding: 2px 8px; border-radius: 4px;
    font-size: 11px; font-family: 'IBM Plex Mono', monospace;
    margin: 2px 3px;
  }
  .when-card:hover {
    border-color: #3DBA6F44 !important;
    transition: border-color 0.2s;
  }
`
if (!document.head.querySelector('[data-ga-ov]')) {
  styleEl.setAttribute('data-ga-ov', '1')
  document.head.appendChild(styleEl)
}

const SectionLabel = ({ children }) => (
  <div style={{
    fontSize: '10px', fontWeight: 700, color: COLORS.green,
    textTransform: 'uppercase', letterSpacing: '2px',
    marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '10px',
  }}>
    <span style={{ display: 'inline-block', width: '20px', height: '1px', background: COLORS.green }} />
    {children}
  </div>
)

const Divider = () => (
  <div style={{ height: '1px', background: `linear-gradient(90deg, ${COLORS.green}44, transparent)`, margin: '40px 0' }} />
)

export default function OverviewPage() {
  return (
    <div style={{ background: COLORS.bg, minHeight: '100vh', paddingBottom: '80px' }}>

      {/* HERO */}
      <div style={{
        position: 'relative', overflow: 'hidden',
        padding: '72px 64px 56px',
        borderBottom: `1px solid ${COLORS.border}`,
      }}>
        <div style={{
          position: 'absolute', inset: 0, opacity: 0.04,
          backgroundImage: 'linear-gradient(#3DBA6F 1px, transparent 1px), linear-gradient(90deg, #3DBA6F 1px, transparent 1px)',
          backgroundSize: '40px 40px', pointerEvents: 'none',
        }} />
        <div style={{
          position: 'absolute', top: '-80px', right: '-80px',
          width: '400px', height: '400px',
          background: 'radial-gradient(circle, rgba(61,186,111,0.12) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />
        <div style={{ position: 'relative', maxWidth: '800px' }}>
          <div className="fade-up fade-up-1" style={{
            display: 'inline-flex', alignItems: 'center', gap: '8px',
            padding: '4px 12px', borderRadius: '20px',
            border: `1px solid rgba(61,186,111,0.3)`,
            background: 'rgba(61,186,111,0.06)',
            fontSize: '11px', color: COLORS.green, letterSpacing: '1px',
            marginBottom: '24px', fontFamily: 'IBM Plex Mono, monospace',
          }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: COLORS.green, animation: 'pulse 2s infinite' }} />
            ISO/IEC 21031:2024 · Software Carbon Intensity
          </div>
          <h1 className="fade-up fade-up-2" style={{
            fontSize: '46px', fontWeight: 600, lineHeight: 1.15,
            color: COLORS.text, marginBottom: '20px',
            fontFamily: 'IBM Plex Sans, sans-serif', letterSpacing: '-1px',
          }}>
            Decida onde hospedar<br />
            <span style={{ color: COLORS.green }}>antes de criar qualquer recurso.</span>
          </h1>
          <p className="fade-up fade-up-3" style={{
            fontSize: '16px', color: COLORS.text2, lineHeight: 1.8,
            maxWidth: '600px', marginBottom: '32px',
          }}>
            O GreenArch calcula o custo e o impacto de carbono de arquiteturas AWS
            usando dados públicos e gratuitos.
            Compara regiões e identifica soluções ótimas de forma acessível.
          </p>
          <div className="fade-up fade-up-4" style={{
            display: 'inline-block', padding: '14px 22px',
            background: 'rgba(61,186,111,0.08)',
            border: `1px solid rgba(61,186,111,0.4)`,
            borderLeft: `3px solid ${COLORS.green}`,
            borderRadius: '6px',
            fontSize: '15px', color: COLORS.text, fontStyle: 'italic', lineHeight: 1.6,
          }}>
            "Onde devo hospedar esta arquitetura para minimizar o carbono sem aumentar o custo?"
          </div>
        </div>
      </div>

      {/* CONTEÚDO — largura total */}
      <div style={{ padding: '48px 64px 0' }}>

        {/* SCI — largura total */}
        <div className="fade-up fade-up-2">
          <SectionLabel>O padrão SCI</SectionLabel>
          <div style={{
            background: COLORS.bg2, border: `1px solid ${COLORS.border}`,
            borderRadius: '12px', padding: '28px 32px', marginBottom: '8px',
          }}>
            <div style={{ display: 'flex', gap: '32px', alignItems: 'flex-start', flexWrap: 'wrap', marginBottom: '24px' }}>
              <p style={{ fontSize: '14px', color: COLORS.text2, lineHeight: 1.8, flex: '1', minWidth: '280px', margin: 0 }}>
                O <b style={{ color: COLORS.text }}>Software Carbon Intensity</b> é um padrão ISO (21031:2024) que mede a pegada
                de carbono de um software por unidade de uso. A unidade funcional aqui é{' '}
                <b style={{ color: COLORS.text }}>1 hora de uso da instância</b>.
              </p>
              <div style={{
                background: COLORS.bg3, borderRadius: '8px',
                padding: '16px 32px', border: `1px solid ${COLORS.border}`,
                textAlign: 'center', flexShrink: 0,
              }}>
                <div style={{
                  fontFamily: 'IBM Plex Mono, monospace',
                  fontSize: '26px', fontWeight: 700,
                  color: COLORS.green, letterSpacing: '2px', whiteSpace: 'nowrap',
                }}>
                  SCI = ( E × I + M ) / R
                </div>
              </div>
            </div>
            {/* 4 cards na mesma linha */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
              {[
                { letter: 'E', label: 'Energia consumida', unit: 'kWh/h', source: 'Cloud Carbon Footprint (ThoughtWorks)' },
                { letter: 'I', label: 'Intensidade de carbono do grid', unit: 'gCO₂/kWh', source: 'Electricity Maps, EPA eGRID, IEA' },
                { letter: 'M', label: 'Carbono embutido do hardware', unit: 'gCO₂/h', source: 'Boavizta dataset' },
                { letter: 'R', label: 'Unidade funcional', unit: '1h de uso', source: 'ISO/IEC 21031:2024' },
              ].map(v => (
                <div key={v.letter} style={{
                  background: COLORS.bg, borderRadius: '8px',
                  padding: '14px 16px', border: `1px solid ${COLORS.border}`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '6px' }}>
                    <span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '22px', fontWeight: 700, color: COLORS.green }}>{v.letter}</span>
                    <span style={{ fontSize: '11px', color: COLORS.text3, fontFamily: 'IBM Plex Mono, monospace' }}>{v.unit}</span>
                  </div>
                  <div style={{ fontSize: '12px', color: COLORS.text, marginBottom: '4px', fontWeight: 500 }}>{v.label}</div>
                  <div style={{ fontSize: '11px', color: COLORS.text3 }}>{v.source}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <Divider />

        {/* COMO USAR + PARETO — lado a lado */}
        <div className="fade-up fade-up-3" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', alignItems: 'start' }}>

          {/* COMO USAR */}
          <div>
            <SectionLabel>Como usar</SectionLabel>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { tab: 'Instância', steps: ['Selecione a instância e a região base', 'Ajuste CPU e horas de uso', 'Escolha as regiões para comparar', 'Clique em Calcular'], desc: 'Compare o SCI e o custo de uma instância EC2 entre regiões.' },
                { tab: 'Arquitetura', steps: ['Carregue um benchmark ou monte sua arquitetura', 'Adicione componentes EC2, RDS, Lambda', 'Selecione as regiões', 'Clique em Calcular arquitetura'], desc: 'Compare o SCI total de uma arquitetura entre regiões.' },
              ].map(card => (
                <div key={card.tab} style={{ background: COLORS.bg2, border: `1px solid ${COLORS.border}`, borderRadius: '12px', padding: '20px 22px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                    <div style={{ width: '28px', height: '28px', borderRadius: '7px', background: 'rgba(61,186,111,0.12)', border: `1px solid rgba(61,186,111,0.3)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', color: COLORS.green, flexShrink: 0 }}>⊞</div>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: COLORS.text }}>Aba {card.tab}</span>
                  </div>
                  <p style={{ fontSize: '12px', color: COLORS.text3, lineHeight: 1.6, marginBottom: '12px' }}>{card.desc}</p>
                  {card.steps.map((s, i) => (
                    <div key={i} style={{ display: 'flex', gap: '10px', padding: '4px 0', alignItems: 'flex-start' }}>
                      <span style={{ minWidth: '18px', height: '18px', borderRadius: '50%', background: 'rgba(61,186,111,0.15)', border: `1px solid rgba(61,186,111,0.3)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '9px', color: COLORS.green, fontWeight: 700, fontFamily: 'IBM Plex Mono, monospace', flexShrink: 0 }}>{i + 1}</span>
                      <span style={{ fontSize: '12px', color: COLORS.text2, lineHeight: 1.6 }}>{s}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* PARETO */}
          <div>
            <SectionLabel>O que é o Pareto-front?</SectionLabel>
            <div style={{ background: COLORS.bg2, border: `1px solid ${COLORS.border}`, borderRadius: '12px', padding: '20px 22px' }}>
              <p style={{ fontSize: '13px', color: COLORS.text2, lineHeight: 1.8, marginBottom: '16px' }}>
                O Pareto-front identifica todas as soluções onde{' '}
                <b style={{ color: COLORS.text }}>não existe outra opção simultaneamente mais barata e com menos carbono</b>.
                Escolher qualquer solução Pareto ótima garante que não há alternativa melhor nas duas dimensões.
              </p>
              {/* Exemplo */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px' }}>
                {[
                  { region: 'us-east-1', sci: '40.6', cost: '$496/mês', status: 'dominada', color: COLORS.text3, bg: COLORS.bg3 },
                  { region: 'us-west-2', sci: '26.8', cost: '$496/mês', status: 'Pareto ótimo', color: COLORS.green, bg: 'rgba(61,186,111,0.06)' },
                  { region: 'eu-north-1', sci: '23.0', cost: '$531/mês', status: 'Pareto ótimo', color: COLORS.green, bg: 'rgba(61,186,111,0.06)' },
                ].map(r => (
                  <div key={r.region} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: r.bg, border: `1px solid ${r.color}33`, borderRadius: '8px', padding: '10px 14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: r.color, flexShrink: 0 }} />
                      <span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '12px', color: COLORS.text }}>{r.region}</span>
                    </div>
                    <div style={{ fontSize: '11px', color: COLORS.text3, textAlign: 'right' }}>
                      {r.sci} gCO₂/h · {r.cost}
                    </div>
                    <span style={{ fontSize: '11px', color: r.color, fontWeight: 600, minWidth: '80px', textAlign: 'right' }}>{r.status}</span>
                  </div>
                ))}
              </div>
              <p style={{ fontSize: '11px', color: COLORS.text3 }}>
                No gráfico: círculos verdes = Pareto ótimo · cinza = dominado · estrela = região base
              </p>
            </div>
          </div>
        </div>

        <Divider />

        {/* QUANDO FAZ SENTIDO — horizontal */}
        <div className="fade-up fade-up-5">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '40px', flexWrap: 'wrap', marginBottom: '16px' }}>
            <div style={{ flex: '0 0 320px' }}>
              <SectionLabel>Quando faz sentido?</SectionLabel>
              <p style={{ fontSize: '14px', color: COLORS.text2, lineHeight: 1.8 }}>
                Migrar para <b style={{ color: COLORS.text }}>eu-north-1</b> reduz o SCI em até 43% —
                mas introduz latência que pode ser incompatível com algumas aplicações.
                O GreenArch exibe latência junto com SCI e custo para uma decisão informada.
              </p>
              <p style={{ fontSize: '11px', color: COLORS.text3, marginTop: '12px' }}>
                A seção Latência de Rede nas abas de análise mostra valores RTT P50 do CloudPing.co.
              </p>
            </div>
            <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
              {[
                { title: 'Menor restrição', accent: COLORS.green, bg: 'rgba(61,186,111,0.06)', border: 'rgba(61,186,111,0.25)', items: ['Processamento batch', 'Treinamento de ML', 'Jobs noturnos e ETL', 'Backup de longo prazo'] },
                { title: 'Maior restrição', accent: COLORS.text, bg: COLORS.bg2, border: COLORS.border, items: ['APIs com usuários na mesma região', 'Bancos síncronos', 'Sistemas de tempo real', 'Apps com SLA de latência'] },
                { title: 'Arquiteturas híbridas', accent: COLORS.text, bg: COLORS.bg2, border: COLORS.border, items: ['Frontend próximo ao usuário', 'Backend em região verde', 'Separar camadas por latência'] },
              ].map(card => (
                <div key={card.title} className="when-card" style={{ background: card.bg, border: `1px solid ${card.border}`, borderRadius: '10px', padding: '16px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: card.accent, marginBottom: '10px' }}>{card.title}</div>
                  {card.items.map((item, i) => (
                    <div key={i} style={{ fontSize: '12px', color: COLORS.text2, padding: '3px 0', lineHeight: 1.6, display: 'flex', gap: '6px' }}>
                      <span style={{ color: card.accent, flexShrink: 0 }}>·</span>{item}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>

        <Divider />

        {/* ENERGIA RENOVÁVEL + FONTES — lado a lado */}
        <div className="fade-up fade-up-6" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '32px', alignItems: 'start' }}>

          {/* ENERGIA */}
          <div>
            <SectionLabel>Certificação de energia renovável</SectionLabel>
            <div style={{ background: COLORS.bg2, border: `1px solid ${COLORS.border}`, borderRadius: '12px', padding: '20px 22px' }}>
              <p style={{ fontSize: '13px', color: COLORS.text2, lineHeight: 1.8, marginBottom: '10px' }}>
                A Amazon reportou a compensação de <b style={{ color: COLORS.text }}>100% da eletricidade</b> consumida
                globalmente com fontes renováveis em 2023 e 2024.
              </p>
              <p style={{ fontSize: '13px', color: COLORS.text2, lineHeight: 1.8, marginBottom: '10px' }}>
                Esse resultado usa o <b style={{ color: COLORS.text }}>método market-based</b>: a Amazon adquire
                certificados de energia renovável, os RECs (Renewable Energy Certificates), equivalentes ao volume
                de eletricidade consumido. Esses certificados funcionam como uma compensação contábil: a empresa paga
                para que energia renovável seja gerada em algum ponto da rede elétrica, mas a eletricidade que chega
                fisicamente aos data centers pode vir de qualquer fonte disponível no grid local, incluindo gás natural,
                carvão ou nuclear.
              </p>
              <p style={{ fontSize: '13px', color: COLORS.text2, lineHeight: 1.8, marginBottom: '16px' }}>
                O GreenArch usa o <b style={{ color: COLORS.text }}>método location-based</b>, que mede a carbon intensity
                real do grid elétrico local de cada região, conforme recomendado pelo ISO/IEC 21031:2024 para o cálculo
                do SCI. Por isso <b style={{ color: COLORS.text }}>us-east-1</b> (Virgínia, 391 gCO₂/kWh) ainda apresenta
                SCI elevado mesmo com certificação de 100% renovável: o grid da Virgínia é majoritariamente termal,
                e nenhum certificado altera a composição física da energia que alimenta os servidores.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                {[
                  { title: 'Américas ✓', regions: ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ca-central-1'], certified: true },
                  { title: 'Europa ✓', regions: ['eu-north-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1', 'eu-south-1'], certified: true },
                  { title: 'Ásia / América do Sul ✓', regions: ['ap-south-1', 'ap-northeast-1', 'ap-northeast-2', 'sa-east-1'], certified: true },
                  { title: 'Sem confirmação', regions: ['ap-southeast-1', 'ap-southeast-2', 'af-south-1', 'me-south-1'], certified: false },
                ].map(group => (
                  <div key={group.title}>
                    <div style={{ fontSize: '10px', fontWeight: 600, color: group.certified ? COLORS.green : COLORS.text3, marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{group.title}</div>
                    <div>{group.regions.map(r => (
                      <span key={r} className="region-tag" style={{ background: group.certified ? 'rgba(61,186,111,0.08)' : COLORS.bg3, border: `1px solid ${group.certified ? 'rgba(61,186,111,0.25)' : COLORS.border}`, color: group.certified ? COLORS.text2 : COLORS.text3 }}>{r}</span>
                    ))}</div>
                  </div>
                ))}
              </div>
              <p style={{ fontSize: '11px', color: COLORS.text3 }}>Fonte: Amazon Sustainability Report 2024</p>
            </div>
          </div>

          {/* FONTES */}
          <div>
            <SectionLabel>Fontes de dados</SectionLabel>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                { title: 'Preços AWS', sub: 'AWS Pricing Bulk API', desc: 'EC2, RDS e Lambda. Tempo real, sem autenticação.' },
                { title: 'Consumo de energia', sub: 'Cloud Carbon Footprint', desc: 'ThoughtWorks. Benchmarks SPECpower por instância.' },
                { title: 'Carbon intensity', sub: 'Electricity Maps, EPA eGRID, IEA', desc: 'Médias anuais 2022–2023 por região AWS.' },
                { title: 'Carbono embutido', sub: 'Boavizta dataset', desc: 'Ciclo de vida do hardware, amortizado pela vida útil.' },
              ].map(s => (
                <div key={s.title} className="source-card" style={{ background: COLORS.bg2, border: `1px solid ${COLORS.border}`, borderRadius: '10px', padding: '14px 16px', transition: 'all 0.2s ease', cursor: 'default', display: 'flex', gap: '14px', alignItems: 'flex-start' }}>
                  <div style={{ width: '3px', height: '100%', minHeight: '40px', background: `linear-gradient(180deg, ${COLORS.green}, transparent)`, borderRadius: '2px', flexShrink: 0 }} />
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: COLORS.text, marginBottom: '2px' }}>{s.title}</div>
                    <div style={{ fontSize: '11px', color: COLORS.green, marginBottom: '4px', fontFamily: 'IBM Plex Mono, monospace' }}>{s.sub}</div>
                    <div style={{ fontSize: '12px', color: COLORS.text3, lineHeight: 1.5 }}>{s.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
