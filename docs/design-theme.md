# Delhivery Commerce AI — Design Theme & System

## Brand Foundation

Derived from Delhivery's public brand identity (Animal agency rebrand). Commerce AI extends the core palette for a data-heavy intelligence product while staying visually consistent with Delhivery One.

### Core Principles

1. **Trust over flash** — No gradients, glowing orbs, or "AI aesthetic." This is a merchant operations tool. It should feel like a Bloomberg terminal, not a Figma showcase.
2. **Geometric precision** — Delhivery's tangram-inspired design language uses clean geometric shapes. Charts, cards, and status indicators follow this.
3. **Data density without clutter** — Merchants need to see a lot of information. Use whitespace and hierarchy, not decoration.
4. **Human-led, machine-driven** — AI outputs are presented as recommendations with clear data backing, not magic black-box answers.

---

## Color System

### Primary Palette (from Delhivery brand)

| Token | Hex | Usage |
|---|---|---|
| `--color-primary` | `#EE3C26` | Delhivery Red. Primary actions, active states, critical alerts. Use sparingly. |
| `--color-primary-dark` | `#C42E1C` | Hover/pressed states on primary elements |
| `--color-primary-light` | `#FFF0EE` | Light red background for critical status cards |
| `--color-black` | `#1A1A1A` | Primary text, headings |
| `--color-white` | `#FFFFFF` | Page background, card backgrounds |

### Neutral Palette (extended for data UI)

| Token | Hex | Usage |
|---|---|---|
| `--color-gray-900` | `#1A1A1A` | Primary text |
| `--color-gray-700` | `#4A4A4A` | Secondary text, labels |
| `--color-gray-500` | `#8A8A8A` | Tertiary text, placeholders |
| `--color-gray-300` | `#D1D1D1` | Borders, dividers |
| `--color-gray-100` | `#F5F5F5` | Background surfaces, table alternating rows |
| `--color-gray-50` | `#FAFAFA` | Page background (slightly off-white) |

### Semantic Palette (status and risk)

| Token | Hex | Usage |
|---|---|---|
| `--color-success` | `#1B8A4E` | Delivered, resolved, healthy cohort |
| `--color-success-light` | `#E8F5EE` | Success background |
| `--color-warning` | `#D4850A` | Medium risk, pending, attention needed |
| `--color-warning-light` | `#FFF8EC` | Warning background |
| `--color-danger` | `#EE3C26` | High risk, RTO, auto-cancelled (same as primary red) |
| `--color-danger-light` | `#FFF0EE` | Danger background |
| `--color-info` | `#2563EB` | Informational, links, express upgrade |
| `--color-info-light` | `#EFF6FF` | Info background |

### Chart Palette (for cohort visualizations)

| Token | Hex | Usage |
|---|---|---|
| `--chart-1` | `#EE3C26` | Primary series (merchant) |
| `--chart-2` | `#2563EB` | Secondary series (peer benchmark) |
| `--chart-3` | `#1B8A4E` | Positive delta / improvement |
| `--chart-4` | `#D4850A` | Neutral / warning series |
| `--chart-5` | `#7C3AED` | Tertiary series |
| `--chart-6` | `#8A8A8A` | Muted / inactive series |

---

## Typography

### Font Stack

```css
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

Inter is chosen because:
- Clean, geometric sans-serif — aligns with Delhivery's neo-modernist aesthetic
- Excellent readability at small sizes (critical for data tables)
- Wide weight range (400–700 used here)
- Free and open source

### Type Scale

| Token | Size | Weight | Line Height | Usage |
|---|---|---|---|---|
| `--text-display` | 28px | 700 | 1.2 | Page titles ("Merchant Snapshot") |
| `--text-heading` | 20px | 600 | 1.3 | Section headings ("Demand Mix Advisor") |
| `--text-subheading` | 16px | 600 | 1.4 | Card titles, table headers |
| `--text-body` | 14px | 400 | 1.5 | Body text, descriptions, NL insights |
| `--text-caption` | 12px | 400 | 1.4 | Labels, timestamps, secondary info |
| `--text-mono` | 13px | 400 | 1.4 | Scores, IDs, technical values |

---

## Spacing and Layout

### Spacing Scale (4px base)

| Token | Value |
|---|---|
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-5` | 20px |
| `--space-6` | 24px |
| `--space-8` | 32px |
| `--space-10` | 40px |
| `--space-12` | 48px |

### Layout

- Page max-width: 1440px, centered
- Sidebar navigation: 240px fixed width, dark (`--color-gray-900`)
- Content area: fluid, with 32px padding
- Card grid: 24px gap
- Border radius: 8px for cards, 4px for inputs/buttons, 2px for tags

---

## Component Patterns

### Cards

```
┌─────────────────────────────────────┐
│  [Icon]  Card Title          [Tag]  │  ← --text-subheading, --space-4 padding
│                                     │
│  Primary metric: 0.82        ▲ 12%  │  ← --text-display for metric, --text-caption for delta
│                                     │
│  Supporting text or NL insight      │  ← --text-body, --color-gray-700
│  that explains the data point.      │
│                                     │
│  [Action Button]                    │  ← Right-aligned, --color-primary
└─────────────────────────────────────┘
```

- Background: `--color-white`
- Border: 1px solid `--color-gray-300`
- Shadow: none (flat design, consistent with geometric aesthetic)
- Hover: border color changes to `--color-gray-500`

### Status Tags

Small pill-shaped indicators for order status, risk level, communication status.

| Status | Background | Text Color | Border |
|---|---|---|---|
| High Risk | `--color-danger-light` | `--color-danger` | none |
| Medium Risk | `--color-warning-light` | `--color-warning` | none |
| Low Risk | `--color-success-light` | `--color-success` | none |
| Auto-Cancelled | `--color-danger-light` | `--color-danger` | 1px solid `--color-danger` |
| Express Upgrade | `--color-info-light` | `--color-info` | none |
| WA Sent | `--color-info-light` | `--color-info` | none |
| Voice Scheduled | `--color-warning-light` | `--color-warning` | none |
| Resolved | `--color-success-light` | `--color-success` | none |
| No Response | `--color-gray-100` | `--color-gray-700` | none |
| Impulsive | `--color-info-light` | `--color-info` | 1px dashed `--color-info` |

Tag styling: `font-size: 12px; font-weight: 500; padding: 2px 8px; border-radius: 4px;`

### Data Tables

- Header: `--color-gray-100` background, `--text-caption` uppercase, `--color-gray-700`
- Rows: alternating `--color-white` and `--color-gray-50`
- Row hover: `--color-gray-100`
- Sortable columns: small arrow indicator, `--color-gray-500` default, `--color-primary` when active
- Numeric values: right-aligned, `--font-mono`
- RTO scores: color-coded inline (green < 0.3, amber 0.3–0.7, red > 0.7)

### Buttons

| Variant | Background | Text | Border | Usage |
|---|---|---|---|---|
| Primary | `--color-primary` | white | none | Execute action, approve |
| Secondary | white | `--color-gray-900` | 1px solid `--color-gray-300` | Cancel, secondary actions |
| Danger | `--color-danger-light` | `--color-danger` | 1px solid `--color-danger` | Auto-cancel, reject |
| Ghost | transparent | `--color-primary` | none | Inline links, tertiary actions |

Button sizing: `height: 36px; padding: 0 16px; font-size: 14px; font-weight: 500; border-radius: 4px;`

### NL Insight Blocks

AI-generated explanations are displayed in a distinct container to differentiate them from raw data.

```
┌─ ◆ AI Insight ──────────────────────┐
│                                     │
│  "This COD order to a tier-3        │  ← --text-body, --color-gray-900
│  pincode in electronics has 3x      │
│  the RTO rate of prepaid orders     │
│  in the same cluster."              │
│                                     │
│  Based on: 847 peer orders          │  ← --text-caption, --color-gray-500
└─────────────────────────────────────┘
```

- Background: `--color-gray-50`
- Left border: 3px solid `--color-gray-300`
- No "sparkle" icons, no "AI" branding beyond the small label
- The ◆ is a small geometric diamond (tangram nod), not a sparkle emoji

---

## Screen Layouts

### Navigation (Sidebar)

```
┌──────────┬──────────────────────────────────────┐
│          │                                      │
│  [Logo]  │                                      │
│          │                                      │
│  ──────  │         Content Area                 │
│          │                                      │
│  📊 Snapshot  │                                 │
│  💡 Advisor   │                                 │
│  📋 Orders    │                                 │
│  ⚡ Actions   │                                 │
│          │                                      │
│          │                                      │
│  ──────  │                                      │
│          │                                      │
│  ⚙ Settings  │                                  │
│          │                                      │
└──────────┴──────────────────────────────────────┘
```

- Sidebar: `--color-gray-900` background, white text
- Active item: `--color-primary` left border accent, `--color-white` text
- Inactive: `--color-gray-500` text
- Icons: simple geometric line icons (not filled, not emoji — the above are placeholders)

### Screen 1: Merchant Snapshot

```
┌─────────────────────────────────────────────────┐
│  Merchant Snapshot                    [Refresh]  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Warehouse │  │ Category │  │ Payment  │      │
│  │ Nodes: 3  │  │ Mix      │  │ Mode     │      │
│  │           │  │ [bar]    │  │ [donut]  │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│                                                  │
│  Peer Benchmark Gaps                             │
│  ┌──────────────────────────────────────────┐   │
│  │  Category    │ You  │ Peers │ Gap        │   │
│  │  Electronics │ 0.72 │ 0.81  │ -0.09 ▼   │   │
│  │  Fashion     │ 0.68 │ 0.65  │ +0.03 ▲   │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### Screen 2: Demand Mix Advisor

```
┌─────────────────────────────────────────────────┐
│  Demand Mix Advisor                              │
│                                                  │
│  ┌─ Suggestion 1 ──────────────────────────┐    │
│  │  Destination: Mumbai Cluster    +0.12 ▲  │    │
│  │                                          │    │
│  │  ◆ "Your electronics orders to Mumbai    │    │
│  │  cluster show 12% higher delivery rate   │    │
│  │  than your current Tier-3 focus..."      │    │
│  │                                          │    │
│  │  Peer sample: 847 orders | CI: ±8pp     │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  ┌─ Suggestion 2 ──────────────────────────┐    │
│  │  Payment: Prepaid push         +0.08 ▲  │    │
│  │  ...                                     │    │
│  └──────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

### Screen 3: Live Order Feed

```
┌──────────────────────────────────────────────────────────────────┐
│  Live Order Feed                          [Sort: RTO Score ▼]    │
│                                                                   │
│  Order ID  │ RTO  │ Risk Tag          │ Action      │ Comms     │
│  ─────────────────────────────────────────────────────────────── │
│  ORD-4821  │ 0.94 │ [Auto-Cancelled]  │ —           │ —         │
│  ORD-3917  │ 0.82 │ [High Risk]       │ WA: Address │ [WA Sent] │
│  ORD-2204  │ 0.71 │ [High Risk]       │ COD→Prepaid │ [Resolved]│
│  ORD-1893  │ 0.65 │ [Medium] [Impulse]│ Express ▲   │ —         │
│  ORD-0412  │ 0.23 │ —                 │ —           │ —         │
└──────────────────────────────────────────────────────────────────┘
```

### Screen 4: Action Console

```
┌──────────────────────────────────────────────────────────────────┐
│  Action Console                                                   │
│                                                                   │
│  Delhivery-Executable              │  Merchant-Owned              │
│  ─────────────────────             │  ──────────────              │
│  ORD-3917: Address WA  [Sent ✓]   │  ORD-5521: Confirm [Pending] │
│  ORD-2204: Payment WA  [Resolved] │                               │
│  ORD-1893: Express ▲   [Done ✓]   │                               │
│  ORD-4821: Auto-Cancel [Done ✓]   │                               │
│                                    │                               │
│  ── Intervention Summary ──────────────────────────────────────── │
│  Today: 47 executed | 3 queued | Rate: 12/hr (cap: 100)          │
└──────────────────────────────────────────────────────────────────┘
```

---

## React Implementation Notes

### Tech Stack
- React 18 + TypeScript
- Vite for build
- Tailwind CSS (configured with the design tokens above as custom theme)
- Recharts for charts (lightweight, composable)
- TanStack Table for data tables
- React Router for 4-screen navigation

### Tailwind Config Extension

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        delhivery: {
          red: '#EE3C26',
          'red-dark': '#C42E1C',
          'red-light': '#FFF0EE',
        },
        success: { DEFAULT: '#1B8A4E', light: '#E8F5EE' },
        warning: { DEFAULT: '#D4850A', light: '#FFF8EC' },
        danger: { DEFAULT: '#EE3C26', light: '#FFF0EE' },
        info: { DEFAULT: '#2563EB', light: '#EFF6FF' },
      },
      fontFamily: {
        sans: ['Inter', ...defaultTheme.fontFamily.sans],
        mono: ['JetBrains Mono', ...defaultTheme.fontFamily.mono],
      },
    },
  },
}
```

### Component Library (minimal, purpose-built)

Only build what we need for the 4 screens:
- `StatusTag` — pill component with variant prop
- `MetricCard` — number + label + delta
- `InsightBlock` — NL explanation container with diamond icon
- `DataTable` — sortable table with TanStack
- `BarChart` / `DonutChart` — Recharts wrappers with theme colors
- `Sidebar` — navigation with active state
- `Button` — primary/secondary/danger/ghost variants
