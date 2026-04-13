const rawBaseUrl = import.meta.env.BASE_URL || '/'

export const appBasePath = rawBaseUrl === '/'
  ? '/'
  : `/${rawBaseUrl.replace(/^\/+|\/+$/g, '')}/`

export const routerBasename = appBasePath === '/'
  ? undefined
  : appBasePath.replace(/\/$/, '')

export function buildAppPath(path: string = '/') {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  if (appBasePath === '/') {
    return normalizedPath
  }
  if (normalizedPath === '/') {
    return appBasePath
  }
  return `${appBasePath}${normalizedPath.slice(1)}`
}

export function buildApiPath(path: string = '/api') {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return buildAppPath(normalizedPath)
}
