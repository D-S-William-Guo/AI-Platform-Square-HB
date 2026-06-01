import { useState, useEffect } from 'react'
import type { AppItem, RankingDimension } from '../../../types'
import { saveAppRankingSetting, fetchAppDimensionScores } from '../../../api/client'
import Modal from '../../../components/Modal'
import LoadingState from '../../../components/LoadingState'
import EmptyState from '../../../components/EmptyState'
import { resolveAdminError, type AppRankingSettingItem, type DimensionConfig } from '../../rankingUtils'

interface RankingConfig {
  id: string
  name: string
  dimensions_config: string
}

interface AppSettingModalProps {
  open: boolean
  app: AppItem
  allRankingConfigs: RankingConfig[]
  dimensions: RankingDimension[]
  editingSetting: AppRankingSettingItem | null
  existingSettings: AppRankingSettingItem[]
  onClose: () => void
  onSaved: () => void
  onError: (msg: string) => void
}

export default function AppSettingModal({
  open,
  app,
  allRankingConfigs,
  dimensions,
  editingSetting,
  existingSettings,
  onClose,
  onSaved,
  onError,
}: AppSettingModalProps) {
  const [form, setForm] = useState({
    ranking_config_id: '',
    is_enabled: true,
    weight_factor: 1.0,
    custom_tags: '',
  })
  const [dimensionScores, setDimensionScores] = useState<Record<number, number>>({})
  const [loadingScores, setLoadingScores] = useState(false)

  useEffect(() => {
    if (!open) return
    const defaultConfigId = editingSetting?.ranking_config_id || allRankingConfigs[0]?.id || ''
    if (editingSetting) {
      setForm({
        ranking_config_id: editingSetting.ranking_config_id,
        is_enabled: editingSetting.is_enabled,
        weight_factor: editingSetting.weight_factor,
        custom_tags: editingSetting.custom_tags,
      })
    } else {
      setForm({
        ranking_config_id: defaultConfigId,
        is_enabled: true,
        weight_factor: 1.0,
        custom_tags: '',
      })
    }
    setDimensionScores({})
  }, [open, editingSetting, allRankingConfigs])

  // Load dimension scores when config changes
  useEffect(() => {
    if (!open || !form.ranking_config_id) {
      setDimensionScores({})
      return
    }
    const loadScores = async () => {
      setLoadingScores(true)
      try {
        const scoreData = await fetchAppDimensionScores(app.id, undefined, form.ranking_config_id)
        const scoreMap: Record<number, number> = {}
        for (const item of scoreData) {
          if (typeof item.dimension_id === 'number') {
            scoreMap[item.dimension_id] = Number(item.score || 0)
          }
        }
        setDimensionScores(scoreMap)
      } catch (err) {
        console.error('Failed to fetch app dimension scores:', err)
        setDimensionScores({})
      } finally {
        setLoadingScores(false)
      }
    }
    loadScores()
  }, [open, form.ranking_config_id, app.id])

  const selectedConfigDimensions = (() => {
    const activeDimensions = dimensions.filter(d => d.is_active)
    if (!form.ranking_config_id) return activeDimensions
    const selectedConfig = allRankingConfigs.find(c => c.id === form.ranking_config_id)
    if (!selectedConfig) return activeDimensions
    try {
      const parsed = JSON.parse(selectedConfig.dimensions_config || '[]')
      const ids = new Set<number>(
        Array.isArray(parsed)
          ? parsed.map((item: DimensionConfig) => Number(item.dim_id)).filter((id: number) => !Number.isNaN(id))
          : []
      )
      if (ids.size === 0) return activeDimensions
      return activeDimensions.filter(d => ids.has(d.id))
    } catch {
      return activeDimensions
    }
  })()

  const handleSave = async () => {
    if (!form.ranking_config_id) {
      onError('请选择榜单后再保存')
      return
    }

    const sameConfigSetting = existingSettings.find(
      s => s.ranking_config_id === form.ranking_config_id && s.id !== editingSetting?.id
    )
    if (sameConfigSetting) {
      onError('该应用已参与所选榜单，请直接编辑已有配置')
      return
    }

    try {
      const scoreUpdates = Object.entries(dimensionScores).map(([dimensionId, score]) => ({
        dimension_id: Number(dimensionId),
        score: Math.max(0, Math.min(100, Number(score))),
      }))

      await saveAppRankingSetting(app.id, {
        setting_id: editingSetting?.id,
        ranking_config_id: form.ranking_config_id,
        is_enabled: form.is_enabled,
        weight_factor: form.weight_factor,
        custom_tags: form.custom_tags,
        dimension_scores: scoreUpdates,
      })

      onSaved()
      onClose()
    } catch (err) {
      onError(resolveAdminError(err, '保存应用榜单设置失败'))
    }
  }

  if (!open) return null

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`${editingSetting ? '编辑应用参与' : '配置应用参与'} - ${app.name}`}
    >
      <div className="modal-body">
        <form className="app-setting-form">
          <div className="form-group">
            <label htmlFor="setting-config">选择榜单 *</label>
            <select
              id="setting-config"
              value={form.ranking_config_id}
              onChange={(e) => setForm(prev => ({ ...prev, ranking_config_id: e.target.value }))}
            >
              <option value="">请选择榜单</option>
              {allRankingConfigs.map(config => (
                <option key={config.id} value={config.id}>{config.name}</option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group checkbox-group">
              <input
                type="checkbox"
                id="setting-enabled"
                checked={form.is_enabled}
                onChange={(e) => setForm(prev => ({ ...prev, is_enabled: e.target.checked }))}
              />
              <label htmlFor="setting-enabled">启用参与</label>
            </div>
            <div className="form-group">
              <label htmlFor="setting-weight">权重系数</label>
              <input
                type="number"
                id="setting-weight"
                min="0.1"
                max="10"
                step="0.1"
                value={form.weight_factor}
                onChange={(e) => setForm(prev => ({ ...prev, weight_factor: parseFloat(e.target.value) }))}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="setting-tags">自定义标签</label>
            <input
              type="text"
              id="setting-tags"
              value={form.custom_tags}
              onChange={(e) => setForm(prev => ({ ...prev, custom_tags: e.target.value }))}
              placeholder="多个标签用逗号分隔"
            />
          </div>

          <div className="form-group">
            <label>维度评分（0-100）</label>
            <p className="form-hint">
              应用最终分数由"榜单维度权重 × 应用维度评分 × 权重系数"计算，未填写时默认沿用当前评分。
            </p>
            {loadingScores ? (
              <LoadingState message="加载维度评分中..." />
            ) : selectedConfigDimensions.length === 0 ? (
              <EmptyState
                title="当前榜单未配置有效维度"
                description="请先在榜单配置中选择有效维度，再维护应用评分。"
              />
            ) : (
              <div className="dimension-score-grid">
                {selectedConfigDimensions.map((dimension) => (
                  <div key={dimension.id} className="dimension-score-item">
                    <span className="dimension-score-name">{dimension.name}</span>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="1"
                      value={dimensionScores[dimension.id] ?? 0}
                      onChange={(e) => {
                        const nextValue = Math.max(0, Math.min(100, Number(e.target.value || 0)))
                        setDimensionScores(prev => ({ ...prev, [dimension.id]: nextValue }))
                      }}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </form>
      </div>
      <div className="modal-footer">
        <button className="secondary-button" onClick={onClose}>取消</button>
        <button className="primary-button" onClick={handleSave}>保存</button>
      </div>
    </Modal>
  )
}
