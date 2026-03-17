const API_STATIC_PREFIX = '/api/static/'

export function resolveMediaUrl(input?: string | null): string {
  const raw = (input || '').trim()
  if (!raw) {
    return ''
  }

  if (
    raw.startsWith('http://')
    || raw.startsWith('https://')
    || raw.startsWith('data:')
    || raw.startsWith('blob:')
  ) {
    return raw
  }

  if (raw.startsWith('/static/')) {
    return `/api${raw}`
  }
  if (raw.startsWith(API_STATIC_PREFIX)) {
    return raw
  }

  return raw.startsWith('/') ? raw : `/${raw}`
}
