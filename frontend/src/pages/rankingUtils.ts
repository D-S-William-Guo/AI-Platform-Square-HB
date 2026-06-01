import { isMissingAdminTokenError, getAdminTokenSetupHint } from '../api/client'

export function resolveAdminError(err: unknown, fallback: string): string {
  if (isMissingAdminTokenError(err)) {
    return `缺少管理员认证信息。${getAdminTokenSetupHint()}`
  }

  const status = (err as { response?: { status?: number } })?.response?.status
  if (status === 401) {
    return `登录状态已失效。${getAdminTokenSetupHint()}`
  }
  if (status === 403) {
    return '当前账号不是管理员，无法访问该页面。'
  }
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string') {
    return detail
  }
  if (detail && typeof detail === 'object') {
    const message = (detail as { message?: string }).message || fallback
    const fieldErrors = (detail as { field_errors?: Array<{ field?: string; message?: string }> }).field_errors || []
    if (fieldErrors.length > 0) {
      const rendered = fieldErrors
        .map((item) => `${item.field || '字段'}: ${item.message || '参数无效'}`)
        .join('；')
      return `${message}（${rendered}）`
    }
    return message
  }
  return fallback
}

export interface AppRankingSettingItem {
  id: number
  app_id: number
  ranking_config_id: string
  is_enabled: boolean
  weight_factor: number
  custom_tags: string
  created_at: string
  updated_at: string
}

export interface DimensionConfig {
  dim_id: number
  weight: number
}
