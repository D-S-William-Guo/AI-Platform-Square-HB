import { buildApiPath } from './basePath'

const API_STATIC_PREFIX = '/api/static/'
const apiStaticPath = buildApiPath('/api/static')

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
    return `${apiStaticPath}${raw.slice('/static'.length)}`
  }
  if (raw.startsWith(API_STATIC_PREFIX)) {
    return buildApiPath(raw)
  }

  return raw.startsWith('/') ? raw : `/${raw}`
}
