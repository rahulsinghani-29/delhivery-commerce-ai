import { useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from 'recharts'
import { fetchSnapshot } from '../lib/api'
import MetricCard from '../components/MetricCard'
import Button from '../components/Button'

const MERCHANT_ID = 'M001'
const CHART_MERCHANT = '#EE3C26'
const CHART_PEER = '#2563EB'

interface CohortKey {
  category: string
  price_band: string
  payment_mode: string
  origin_node: string
  destination_cluster: string
}

interface PeerBenchmark {
  cohort_key: CohortKey
  merchant_score: number
  peer_avg_score: number
  peer_sample_size: number
  confidence_interval_width: number
  gap: number
}

interface SnapshotData {
  merchant_id: string
  warehouse_nodes: Record<string, unknown>[]
  category_distribution: Record<string, number>
  price_band_distribution: Record<string, number>
  payment_mode_distribution: Record<string, number>
  benchmark_gaps: PeerBenchmark[]
}

export default function Snapshot() {
  const [data, setData] = useState<SnapshotData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    setLoading(true)
    setError(null)
    fetchSnapshot(MERCHANT_ID)
      .then((d) => setData(d as SnapshotData))
      .catch((e) => setError(e.message ?? 'Failed to load snapshot'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  if (loading) return <p className="text-sm text-gray-500">Loading...</p>
  if (error) return <p className="text-sm text-danger">{error}</p>
  if (!data) return null

  const categoryData = Object.entries(data.category_distribution).map(
    ([name, value]) => ({ name, value }),
  )

  const paymentData = Object.entries(data.payment_mode_distribution).map(
    ([name, value]) => ({ name, value }),
  )

  const totalOrders = Object.values(data.category_distribution).reduce(
    (s, v) => s + v,
    0,
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-[28px] font-bold leading-tight text-gray-900">
          Merchant Snapshot
        </h1>
        <Button variant="secondary" onClick={load}>
          Refresh
        </Button>
      </div>

      {/* Top metric cards */}
      <div className="grid grid-cols-3 gap-6">
        <MetricCard label="Warehouse Nodes" value={data.warehouse_nodes.length} />
        <MetricCard label="Total Orders" value={totalOrders} />
        <MetricCard
          label="Payment Mode"
          value={`${paymentData.length} types`}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-2 gap-6">
        {/* Category distribution bar chart */}
        <div className="bg-white border border-gray-300 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-3">
            Category Distribution
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={categoryData} layout="vertical" margin={{ left: 60 }}>
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fontSize: 12 }}
                width={55}
              />
              <Tooltip />
              <Bar dataKey="value" fill={CHART_MERCHANT} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Payment mode donut chart */}
        <div className="bg-white border border-gray-300 rounded-lg p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-3">
            Payment Mode
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={paymentData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={2}
              >
                {paymentData.map((_, i) => (
                  <Cell
                    key={i}
                    fill={i === 0 ? CHART_MERCHANT : CHART_PEER}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-2">
            {paymentData.map((d, i) => (
              <span key={d.name} className="flex items-center gap-1.5 text-xs text-gray-700">
                <span
                  className="inline-block w-2.5 h-2.5 rounded-sm"
                  style={{ background: i === 0 ? CHART_MERCHANT : CHART_PEER }}
                />
                {d.name}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Peer benchmark gaps table */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-3">
          Peer Benchmark Gaps
        </h2>
        <div className="bg-white border border-gray-300 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 text-xs uppercase text-gray-700">
                <th className="text-left px-4 py-2">Dimension</th>
                <th className="text-right px-4 py-2">Your Score</th>
                <th className="text-right px-4 py-2">Peer Avg</th>
                <th className="text-right px-4 py-2">Gap</th>
              </tr>
            </thead>
            <tbody>
              {data.benchmark_gaps.map((b, i) => {
                const label = b.cohort_key.category
                const positive = b.gap >= 0
                return (
                  <tr
                    key={i}
                    className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                  >
                    <td className="px-4 py-2 text-gray-900">{label}</td>
                    <td className="px-4 py-2 text-right font-mono">
                      {b.merchant_score.toFixed(2)}
                    </td>
                    <td className="px-4 py-2 text-right font-mono">
                      {b.peer_avg_score.toFixed(2)}
                    </td>
                    <td
                      className={`px-4 py-2 text-right font-mono ${
                        positive ? 'text-success' : 'text-danger'
                      }`}
                    >
                      {positive ? '+' : ''}
                      {b.gap.toFixed(2)} {positive ? '▲' : '▼'}
                    </td>
                  </tr>
                )
              })}
              {data.benchmark_gaps.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-gray-500">
                    No benchmark data available yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
