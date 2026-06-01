import { useState, useEffect } from 'react'
import type { RankingDimension } from '../../../types'
import { createRankingDimension, updateRankingDimension } from '../../../api/client'
import Modal from '../../../components/Modal'
import { resolveAdminError } from '../../rankingUtils'

interface DimensionModalProps {
  open: boolean
  editingDimension: RankingDimension | null
  onClose: () => void
  onSaved: () => void
  onError: (msg: string) => void
}

export default function DimensionModal({
  open,
  editingDimension,
  onClose,
  onSaved,
  onError,
}: DimensionModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    calculation_method: '',
    weight: 1.0,
    is_active: true,
  })

  useEffect(() => {
    if (!open) return
    if (editingDimension) {
      setFormData({
        name: editingDimension.name,
        description: editingDimension.description,
        calculation_method: editingDimension.calculation_method,
        weight: editingDimension.weight,
        is_active: editingDimension.is_active,
      })
    } else {
      setFormData({
        name: '',
        description: '',
        calculation_method: '',
        weight: 1.0,
        is_active: true,
      })
    }
  }, [open, editingDimension])

  const handleSave = async () => {
    try {
      if (editingDimension) {
        await updateRankingDimension(editingDimension.id, formData)
      } else {
        await createRankingDimension(formData)
      }
      onSaved()
      onClose()
    } catch (err) {
      onError(resolveAdminError(err, '保存维度失败'))
    }
  }

  if (!open) return null

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={editingDimension ? '编辑评价维度' : '新增评价维度'}
    >
      <div className="modal-body">
        <form className="dimension-form">
          <div className="form-group">
            <label htmlFor="dim-name">维度名称 *</label>
            <input
              type="text"
              id="dim-name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="请输入维度名称"
            />
          </div>

          <div className="form-group">
            <label htmlFor="dim-description">维度描述 *</label>
            <textarea
              id="dim-description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="请输入维度描述"
              rows={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="dim-calculation">计算方法 *</label>
            <textarea
              id="dim-calculation"
              value={formData.calculation_method}
              onChange={(e) => setFormData(prev => ({ ...prev, calculation_method: e.target.value }))}
              placeholder="请输入计算方法"
              rows={4}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="dim-weight">默认权重</label>
              <input
                type="number"
                id="dim-weight"
                min="0.1"
                max="10"
                step="0.1"
                value={formData.weight}
                onChange={(e) => setFormData(prev => ({ ...prev, weight: parseFloat(e.target.value) }))}
              />
            </div>
            <div className="form-group checkbox-group">
              <input
                type="checkbox"
                id="dim-active"
                checked={formData.is_active}
                onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              />
              <label htmlFor="dim-active">启用</label>
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
