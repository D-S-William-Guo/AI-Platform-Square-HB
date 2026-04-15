type UiIconName =
  | 'platform'
  | 'guide'
  | 'rule'
  | 'my'
  | 'ranking'
  | 'review'
  | 'user'
  | 'history'
  | 'search'
  | 'group'
  | 'province'
  | 'trophy'
  | 'trend'
  | 'medal'
  | 'error'
  | 'calls'
  | 'date'
  | 'trial'
  | 'locked'
  | 'doc'
  | 'empty'
  | 'sync'

export default function UiIcon({ name, size = 16 }: { name: UiIconName; size?: number }) {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
  }

  switch (name) {
    case 'platform':
      return <svg {...common}><path d="M12 3 3 7l9 4 9-4-9-4Z" /><path d="M3 12l9 4 9-4" /><path d="M3 17l9 4 9-4" /></svg>
    case 'guide':
      return <svg {...common}><path d="M5 4h10a3 3 0 0 1 3 3v13H8a3 3 0 0 0-3 3V4Z" /><path d="M8 8h7M8 12h7M8 16h5" /></svg>
    case 'rule':
      return <svg {...common}><path d="M7 3h10v18l-5-3-5 3V3Z" /><path d="M9 8h6M9 12h6" /></svg>
    case 'my':
      return <svg {...common}><path d="M8 3h8l3 3v15H5V3h3Z" /><path d="M14 3v4h4" /><path d="M8 10h8M8 14h8M8 18h5" /></svg>
    case 'ranking':
      return <svg {...common}><circle cx="12" cy="8" r="3" /><path d="M8 14h8" /><path d="M10 14v7l2-1 2 1v-7" /></svg>
    case 'review':
      return <svg {...common}><path d="M20 7 9 18l-5-5" /></svg>
    case 'user':
      return <svg {...common}><circle cx="9" cy="8" r="3" /><circle cx="17" cy="9" r="2.5" /><path d="M3.5 20a6 6 0 0 1 11 0" /><path d="M13.5 20a4.5 4.5 0 0 1 7 0" /></svg>
    case 'history':
      return <svg {...common}><path d="M4 19h16M6 17V7M12 17V4M18 17v-6" /></svg>
    case 'search':
      return <svg {...common}><circle cx="11" cy="11" r="6" /><path d="m20 20-3.5-3.5" /></svg>
    case 'group':
      return <svg {...common}><path d="M3 10 12 4l9 6v10H3V10Z" /><path d="M9 20v-6h6v6" /></svg>
    case 'province':
      return <svg {...common}><path d="M12 3a7 7 0 0 0-7 7c0 5 7 11 7 11s7-6 7-11a7 7 0 0 0-7-7Z" /><circle cx="12" cy="10" r="2.5" /></svg>
    case 'trophy':
      return <svg {...common}><path d="M8 4h8v4a4 4 0 0 1-8 0V4Z" /><path d="M10 12h4M12 12v4M9 20h6" /><path d="M6 6H4a2 2 0 0 0 2 3h1M18 6h2a2 2 0 0 1-2 3h-1" /></svg>
    case 'trend':
      return <svg {...common}><path d="M4 16l5-5 3 3 6-6" /><path d="M14 8h4v4" /></svg>
    case 'medal':
      return <svg {...common}><circle cx="12" cy="14" r="4" /><path d="M10 3h4l1 5h-6l1-5Z" /></svg>
    case 'error':
      return <svg {...common}><circle cx="12" cy="12" r="9" /><path d="m9 9 6 6M15 9l-6 6" /></svg>
    case 'calls':
      return <svg {...common}><path d="M4 19h16M7 17V9M12 17V6M17 17v-4" /></svg>
    case 'date':
      return <svg {...common}><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M8 3v4M16 3v4M4 10h16" /></svg>
    case 'trial':
      return <svg {...common}><path d="M5 13 9 17 19 7" /></svg>
    case 'locked':
      return <svg {...common}><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V8a4 4 0 1 1 8 0v3" /></svg>
    case 'doc':
      return <svg {...common}><path d="M7 3h8l4 4v14H7V3Z" /><path d="M15 3v4h4M10 12h6M10 16h6" /></svg>
    case 'sync':
      return <svg {...common}><path d="M20 7v5h-5" /><path d="M4 17v-5h5" /><path d="M6.5 9A7 7 0 0 1 18 7M17.5 15A7 7 0 0 1 6 17" /></svg>
    case 'empty':
      return <svg {...common}><path d="M4 19h16M6 17V7M12 17V4M18 17v-6" /></svg>
  }
}
