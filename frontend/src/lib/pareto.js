export function computePareto(scenarios) {
  return scenarios.map((sc, i) => {
    const dominated = scenarios.some((other, j) => {
      if (i === j) return false
      return (
        other.sci_score <= sc.sci_score &&
        other.cost_usd_month <= sc.cost_usd_month &&
        (other.sci_score < sc.sci_score || other.cost_usd_month < sc.cost_usd_month)
      )
    })
    return { ...sc, pareto_optimal: !dominated }
  })
}

export function getLatencyLabel(ms) {
  if (ms === null || ms === undefined) return { label: '—', color: '#A8BCA8' }
  if (ms < 80)  return { label: `🟢 ${ms} ms`, color: '#3DBA6F' }
  if (ms < 150) return { label: `🟡 ${ms} ms`, color: '#E8963A' }
  return { label: `🔴 ${ms} ms`, color: '#E05252' }
}

export function getSciReduction(base, best) {
  if (!base || !best) return 0
  return Math.round((base.sci_score - best.sci_score) / base.sci_score * 100 * 10) / 10
}