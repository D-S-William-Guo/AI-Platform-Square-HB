import { useState, useEffect } from 'react'
import type { RankingDimension } from '../../../types'
import { createRankingConfig, updateRankingConfig } from '../../../api/client'
import Modal from '../../../components/Modal'
import { resolveAdminError } from '../../rankingUtils'

interface RankingConfigRecord {
  id: string
  name: string
  description: string
  calculation_method: string
  is_active: boolean
  dimensions_config: string
}

interface RankingConfigModalProps {
  open: boolean
  editingConfig: RankingConfigRecord | null
  dimensions: RankingDimension[]
  onClose: () => void
  onSaved: () => void
  onError: (msg: string) => void
}

export default function RankingConfigModal({
  open,
  editingConfig,
  dimensions,
  onClose,
  onSaved,
  onError,
}: RankingConfigModalProps) {
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    description: '',
    calculation_method: 'composite' as string,
    is_active: true,
    selectedDimensions: [] as { dim_id: number; weight: number }[],
  })

  useEffect(() => {
    if (!open) return
    if (editingConfig) {
      let selectedDims: { dim_id: number; weight: number }[] = []
      try {
        selectedDims = JSON.parse(editingConfig.dimensions_config) || []
      } catch {
        selectedDims = []
      }
      setFormData({
        id: editingConfig.id,
        name: editingConfig.name,
        description: editingConfig.description,
        calculation_method: editingConfig.calculation_method,
        is_active: editingConfig.is_active,
        selectedDimensions: selectedDims,
      })
    } else {
      setFormData({
        id: '',
        name: '',
        description: '',
        calculation_method: 'composite',
        is_active: true,
        selectedDimensions: [],
      })
    }
  }, [open, editingConfig])

  const toggleDimension = (dimId: number) => {
    setFormData(prev => {
      const exists = prev.selectedDimensions.find(d => d.dim_id === dimId)
      if (exists) {
        return { ...prev, selectedDimensions: prev.selectedDimensions.filter(d => d.dim_id !== dimId) }
      }
      return { ...prev, selectedDimensions: [...prev.selectedDimensions, { dim_id: dimId, weight: 1.0 }] }
    })
  }

  const updateWeight = (dimId: number, weight: number) => {
    setFormData(prev => ({
      ...prev,
      selectedDimensions: prev.selectedDimensions.map(d =>
        d.dim_id === dimId ? { ...d, weight } : d
      ),
    }))
  }

  const handleSave = async () => {
    try {
      const payload = {
        id: formData.id,
        name: formData.name,
        description: formData.description,
        calculation_method: formData.calculation_method,
        is_active: formData.is_active,
        dimensions_config: JSON.stringify(formData.selectedDimensions),
      }
      if (editingConfig) {
        await updateRankingConfig(editingConfig.id, payload)
      } else {
        await createRankingConfig(payload)
      }
      onSaved()
      onClose()
    } catch (err) {
      onError(resolveAdminError(err, '保存榜单配置失败'))
    }
  }

  if (!open) return null

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={editingConfig ? '编辑榜单配置' : '新增榜单配置'}
      className="large"
    >
      <div className="modal-body">
        <form className="config-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="config-id">榜单ID *</label>
              <input
                type="text"
                id="config-id"
                value={formData.id}
                onChange={(e) => setFormData(prev => ({ ...prev, id: e.target.value }))}
                placeholder="如: excellent, trend"
                disabled={!!editingConfig}
              />
            </div>
            <div className="form-group">
              <label htmlFor="config-name">榜单名称 *</label>
              <input
                type="text"
                id="config-name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="请输入榜单名称"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="config-description">榜单描述</label>
            <textarea
              id="config-description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="请输入榜单描述"
              rows={3}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="config-method">计算公式</label>
              <select
                id="config-method"
                value={formData.calculation_method}
                onChange={(e) => setFormData(prev => ({ ...prev, calculation_method: e.target.value }))}
              >
                <option value="composite">综合评分</option>
                <option value="growth_rate">增长率</option>
              </select>
            </div>
            <div className="form-group checkbox-group">
              <input
                type="checkbox"
                id="config-active"
                checked={formData.is_active}
                onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              />
              <label htmlFor="config-active">启用此榜单</label>
            </div>
          </div>

          <div className="form-group">
            <label>选择评价维度</label>
            <div className="dimensions-selector">
              {dimensions.filter(d => d.is_active).map(dimension => {
                const selected = formData.selectedDimensions.find(d => d.dim_id === dimension.id)
                return (
                  <div key={dimension.id} className={`dimension-select-item ${selected ? 'selected' : ''}`}>
                    <label className="dimension-checkbox">
                      <input
                        type="checkbox"
                        checked={!!selected}
                        onChange={() => toggleDimension(dimension.id)}
                      />
                      <span className="dimension-name">{dimension.name}</span>
                    </label>
                    {selected && (
                      <div className="dimension-weight-input">
                        <span>权重:</span>
                        <input
                          type="number"
                          min="0.1"
                          max="10"
                          step="0.1"
                          value={selected.weight}
                          onChange={(e) => updateWeight(dimension.id, parseFloat(e.target.value))}
                        />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
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
