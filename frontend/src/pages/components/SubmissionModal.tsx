import { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import type { AuthUser, SubmissionPayload, FormErrors, ValueDimension } from '../../types'
import { auditEvent, submitApp, uploadImage, uploadDocument } from '../../api/client'
import Modal from '../../components/Modal'
import { createSubmissionDraft, validationRules, ValidationRule } from '../homeUtils'

interface SubmissionModalProps {
  open: boolean
  onClose: () => void
  currentUser: AuthUser | null
  appCategories: string[]
  defaultCategory: string
  submissionCategoryUnavailable: boolean
  categoryOptionsError: string | null
}

export default function SubmissionModal({
  open,
  onClose,
  currentUser,
  appCategories,
  defaultCategory,
  submissionCategoryUnavailable,
  categoryOptionsError,
}: SubmissionModalProps) {
  const navigate = useNavigate()
  const [submission, setSubmission] = useState<SubmissionPayload>(() =>
    createSubmissionDraft(currentUser, defaultCategory)
  )
  const [errors, setErrors] = useState<FormErrors>({})
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [documentUploading, setDocumentUploading] = useState(false)
  const [documentMeta, setDocumentMeta] = useState<{
    url: string
    name: string
    size: number
    mimeType: string
  } | null>(null)

  // Sync unit_name from currentUser.company
  useEffect(() => {
    setSubmission((prev) => ({ ...prev, unit_name: currentUser?.company || prev.unit_name }))
  }, [currentUser?.company])

  // Sync category when appCategories changes
  useEffect(() => {
    if (!defaultCategory) return
    setSubmission((prev) => {
      if (appCategories.includes(prev.category)) return prev
      return { ...prev, category: defaultCategory }
    })
  }, [appCategories, defaultCategory])

  const validateField = useCallback((name: keyof SubmissionPayload, value: string | number | boolean): string => {
    const rule = validationRules[name as keyof typeof validationRules] as ValidationRule | undefined
    if (!rule) return ''

    if (rule.pattern) {
      const stringValue = String(value)
      if (stringValue && !rule.pattern.test(stringValue)) {
        return rule.message
      }
      return ''
    }

    if (rule.required) {
      if (typeof value === 'string' && !value.trim()) {
        return '此字段为必填项'
      }
      if (value === null || value === undefined) {
        return '此字段为必填项'
      }
    }

    if (typeof value === 'number') {
      if (rule.min !== undefined && value < rule.min) {
        return rule.message
      }
      if (rule.max !== undefined && value > rule.max) {
        return rule.message
      }
      return ''
    }

    if (typeof value === 'string' && value) {
      if (rule.minLength !== undefined && value.length < rule.minLength) {
        return `最少需要 ${rule.minLength} 个字符`
      }
      if (rule.maxLength !== undefined && value.length > rule.maxLength) {
        return `最多允许 ${rule.maxLength} 个字符`
      }
    }

    return ''
  }, [])

  const validateForm = useCallback((): boolean => {
    const newErrors: FormErrors = {}
    let isValid = true

    Object.keys(validationRules).forEach((key) => {
      const fieldName = key as keyof SubmissionPayload
      const value = submission[fieldName]
      const error = validateField(fieldName, value)
      if (error) {
        newErrors[key] = error
        isValid = false
      }
    })

    setErrors(newErrors)
    return isValid
  }, [submission, validateField])

  const handleFieldChange = useCallback((field: keyof SubmissionPayload, value: string | number) => {
    setSubmission(prev => ({ ...prev, [field]: value }))
    const error = validateField(field, value)
    setErrors(prev => ({ ...prev, [field]: error }))
  }, [validateField])

  const handleImageUpload = useCallback(async (file: File) => {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg']
    if (!allowedTypes.includes(file.type)) {
      alert('仅支持 JPG、PNG 格式的图片')
      return
    }

    const maxSize = 5 * 1024 * 1024
    if (file.size > maxSize) {
      alert('图片大小不能超过 5MB')
      return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string)
    }
    reader.readAsDataURL(file)

    setUploading(true)
    setUploadProgress(0)

    try {
      const result = await uploadImage(file, 'submission')
      if (result.success) {
        setSubmission(prev => ({ ...prev, cover_image_url: result.image_url }))
        setUploadProgress(100)
      } else {
        alert(result.message)
        setImagePreview(null)
      }
    } catch {
      alert('图片上传失败，请重试')
      setImagePreview(null)
    } finally {
      setUploading(false)
    }
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleImageUpload(file)
  }, [handleImageUpload])

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file) handleImageUpload(file)
  }, [handleImageUpload])

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
  }, [])

  const removeImage = useCallback(() => {
    setImagePreview(null)
    setSubmission(prev => ({ ...prev, cover_image_url: '' }))
  }, [])

  const handleDocumentUpload = useCallback(async (file: File) => {
    const allowedExt = ['pdf', 'doc', 'docx', 'txt', 'md']
    const ext = (file.name.split('.').pop() || '').toLowerCase()
    if (!allowedExt.includes(ext)) {
      alert('详细文档仅支持 PDF/DOC/DOCX/TXT/MD')
      return
    }

    setDocumentUploading(true)
    try {
      const result = await uploadDocument(file)
      if (!result.success) {
        alert(result.message || '文档上传失败')
        return
      }
      setDocumentMeta({
        url: result.file_url,
        name: result.original_name,
        size: result.file_size,
        mimeType: file.type || ''
      })
      setSubmission(prev => ({
        ...prev,
        detail_doc_url: result.file_url,
        detail_doc_name: result.original_name
      }))
    } catch {
      alert('文档上传失败，请重试')
    } finally {
      setDocumentUploading(false)
    }
  }, [])

  const handleDocumentSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleDocumentUpload(file)
  }, [handleDocumentUpload])

  const resetForm = useCallback(() => {
    setSubmission(createSubmissionDraft(currentUser, defaultCategory))
    setImagePreview(null)
    setDocumentMeta(null)
    setErrors({})
  }, [currentUser, defaultCategory])

  const handleClose = useCallback(() => {
    resetForm()
    onClose()
  }, [resetForm, onClose])

  const onSubmit = useCallback(async () => {
    if (!currentUser) {
      auditEvent({
        event_name: 'auth.intent.submit.click',
        intent: 'submit',
        result: 'redirect_login',
        return_to: '/',
        context: 'home.submit.modal.submit',
      })
      navigate('/login', { state: { intent: 'submit', returnTo: '/' } })
      return
    }
    if (submissionCategoryUnavailable) {
      alert(categoryOptionsError || '分类配置加载中，请稍后重试')
      return
    }
    if (!validateForm()) {
      alert('请检查表单填写是否正确')
      return
    }

    try {
      await submitApp(submission)
      alert('申报已提交，等待审核。')
      resetForm()
      onClose()
    } catch {
      alert('提交失败，请重试')
    }
  }, [currentUser, submissionCategoryUnavailable, categoryOptionsError, validateForm, submission, resetForm, onClose, navigate])

  if (!open) return null

  return (
    <Modal open={open} onClose={handleClose} title="应用申报" subtitle="请填写完整的应用信息，带 * 的为必填项">
      <div className="modal-body">
        {/* 图片上传区域 */}
        <div className="form-group">
          <label className="form-label">应用封面图</label>
          <div
            className={`image-upload-area ${imagePreview ? 'has-image' : ''}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
          >
            {imagePreview ? (
              <div className="image-preview">
                <img src={imagePreview} alt="预览" />
                <button
                  type="button"
                  className="remove-image"
                  aria-label="移除封面图"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    removeImage()
                  }}
                >
                  ×
                </button>
              </div>
            ) : (
              <div className="upload-placeholder">
                <div className="upload-icon">📷</div>
                <p>点击或拖拽上传图片</p>
                <p className="upload-hint">支持 JPG、PNG 格式，最大 5MB</p>
              </div>
            )}
            <input
              type="file"
              accept="image/jpeg,image/png,image/jpg"
              onChange={handleFileSelect}
              className="file-input"
            />
            {uploading && (
              <div className="upload-progress">
                <div className="progress-bar" style={{ width: `${uploadProgress}%` }}></div>
                <span className="progress-text">{uploadProgress}%</span>
              </div>
            )}
          </div>
        </div>

        {/* 详细文档上传 */}
        <div className="form-group">
          <label className="form-label">详细文档（可选）</label>
          <div className="doc-upload-area">
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt,.md"
              onChange={handleDocumentSelect}
              className="doc-file-input"
            />
            {documentUploading ? (
              <span className="doc-upload-status">文档上传中...</span>
            ) : documentMeta ? (
              <div className="doc-uploaded">
                <span className="doc-name">{documentMeta.name}</span>
                <button
                  type="button"
                  className="doc-remove-btn"
                  onClick={() => {
                    setDocumentMeta(null)
                    setSubmission(prev => ({ ...prev, detail_doc_url: '', detail_doc_name: '' }))
                  }}
                >
                  移除
                </button>
              </div>
            ) : (
              <span className="doc-upload-status">点击上传文档，支持 PDF/DOC/DOCX/TXT/MD</span>
            )}
          </div>
        </div>

        {/* 基础信息 */}
        <div className="form-section">
          <h4 className="form-section-title">基础信息</h4>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">应用名称 *</label>
              <input
                className={`form-input ${errors.app_name ? 'error' : ''}`}
                placeholder="请输入应用名称"
                value={submission.app_name}
                onChange={(e) => handleFieldChange('app_name', e.target.value)}
              />
              {errors.app_name && <span className="error-message">{errors.app_name}</span>}
            </div>
            <div className="form-group">
              <label className="form-label">所属公司 *</label>
              <input
                className={`form-input ${errors.unit_name ? 'error' : ''}`}
                value={submission.unit_name}
                readOnly
              />
              {errors.unit_name && <span className="error-message">{errors.unit_name}</span>}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">所属部门</label>
              <input
                className="form-input"
                value={currentUser?.department || '未设置'}
                readOnly
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">联系人 *</label>
              <input
                className={`form-input ${errors.contact ? 'error' : ''}`}
                placeholder="请输入联系人姓名"
                value={submission.contact}
                onChange={(e) => handleFieldChange('contact', e.target.value)}
              />
              {errors.contact && <span className="error-message">{errors.contact}</span>}
            </div>
            <div className="form-group">
              <label className="form-label">联系电话</label>
              <input
                className={`form-input ${errors.contact_phone ? 'error' : ''}`}
                placeholder="请输入手机号码"
                value={submission.contact_phone}
                onChange={(e) => handleFieldChange('contact_phone', e.target.value)}
              />
              {errors.contact_phone && <span className="error-message">{errors.contact_phone}</span>}
            </div>
          </div>

          <div className="form-row">
            {categoryOptionsError && (
              <div className="form-group">
                <span className="error-message">{categoryOptionsError}</span>
              </div>
            )}
            <div className="form-group">
              <label className="form-label">联系邮箱</label>
              <input
                className={`form-input ${errors.contact_email ? 'error' : ''}`}
                placeholder="请输入邮箱地址"
                value={submission.contact_email}
                onChange={(e) => handleFieldChange('contact_email', e.target.value)}
              />
              {errors.contact_email && <span className="error-message">{errors.contact_email}</span>}
            </div>
            <div className="form-group">
              <label className="form-label">应用分类 *</label>
              <select
                className="form-select"
                value={submission.category}
                onChange={(e) => handleFieldChange('category', e.target.value)}
                disabled={submissionCategoryUnavailable}
              >
                {appCategories.length === 0 ? (
                  <option value="">分类配置不可用</option>
                ) : (
                  appCategories.map((category) => (
                    <option key={category} value={category}>{category}</option>
                  ))
                )}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">月调用量（k）</label>
              <input
                className={`form-input ${errors.monthly_calls ? 'error' : ''}`}
                type="number"
                min="0"
                step="0.1"
                value={submission.monthly_calls}
                onChange={(e) => handleFieldChange('monthly_calls', Math.max(0, Number(e.target.value || 0)))}
              />
              {errors.monthly_calls && <span className="error-message">{errors.monthly_calls}</span>}
            </div>
            <div className="form-group">
              <label className="form-label">接入难度</label>
              <select
                className="form-select"
                value={submission.difficulty}
                onChange={(e) => handleFieldChange('difficulty', e.target.value as SubmissionPayload['difficulty'])}
              >
                <option value="Low">低</option>
                <option value="Medium">中</option>
                <option value="High">高</option>
              </select>
            </div>
          </div>
        </div>

        {/* 应用信息 */}
        <div className="form-section">
          <h4 className="form-section-title">应用信息</h4>
          <div className="form-group">
            <label className="form-label">应用场景 *</label>
            <textarea
              className={`form-textarea ${errors.scenario ? 'error' : ''}`}
              placeholder="请详细描述应用场景（至少20字）..."
              value={submission.scenario}
              onChange={(e) => handleFieldChange('scenario', e.target.value)}
            />
            {errors.scenario && <span className="error-message">{errors.scenario}</span>}
            <span className="char-count">{submission.scenario.length}/500</span>
          </div>

          <div className="form-group">
            <label className="form-label">嵌入系统 *</label>
            <input
              className={`form-input ${errors.embedded_system ? 'error' : ''}`}
              placeholder="请输入嵌入系统名称"
              value={submission.embedded_system}
              onChange={(e) => handleFieldChange('embedded_system', e.target.value)}
            />
            {errors.embedded_system && <span className="error-message">{errors.embedded_system}</span>}
          </div>

          <div className="form-group">
            <label className="form-label">解决的问题 *</label>
            <textarea
              className={`form-textarea ${errors.problem_statement ? 'error' : ''}`}
              placeholder="请描述解决的问题（至少10字）..."
              value={submission.problem_statement}
              onChange={(e) => handleFieldChange('problem_statement', e.target.value)}
            />
            {errors.problem_statement && <span className="error-message">{errors.problem_statement}</span>}
            <span className="char-count">{submission.problem_statement.length}/255</span>
          </div>
        </div>

        {/* 成效评估 */}
        <div className="form-section">
          <h4 className="form-section-title">成效评估</h4>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">成效类型 *</label>
              <select
                className="form-select"
                value={submission.effectiveness_type}
                onChange={(e) => handleFieldChange('effectiveness_type', e.target.value as ValueDimension)}
              >
                <option value="cost_reduction">降本</option>
                <option value="efficiency_gain">增效</option>
                <option value="perception_uplift">感知提升</option>
                <option value="revenue_growth">拉动收入</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">数据级别 *</label>
              <select
                className="form-select"
                value={submission.data_level}
                onChange={(e) => handleFieldChange('data_level', e.target.value)}
              >
                <option value="L1">L1 - 公开数据</option>
                <option value="L2">L2 - 内部数据</option>
                <option value="L3">L3 - 敏感数据</option>
                <option value="L4">L4 - 机密数据</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">成效指标 *</label>
            <input
              className={`form-input ${errors.effectiveness_metric ? 'error' : ''}`}
              placeholder="如：工时下降30%、效率提升50%..."
              value={submission.effectiveness_metric}
              onChange={(e) => handleFieldChange('effectiveness_metric', e.target.value)}
            />
            {errors.effectiveness_metric && <span className="error-message">{errors.effectiveness_metric}</span>}
          </div>

          <div className="form-group">
            <label className="form-label">预期收益 *</label>
            <textarea
              className={`form-textarea ${errors.expected_benefit ? 'error' : ''}`}
              placeholder="请描述预期收益（至少10字）..."
              value={submission.expected_benefit}
              onChange={(e) => handleFieldChange('expected_benefit', e.target.value)}
            />
            {errors.expected_benefit && <span className="error-message">{errors.expected_benefit}</span>}
            <span className="char-count">{submission.expected_benefit.length}/300</span>
          </div>
        </div>
      </div>

      <div className="modal-footer">
        <button className="modal-btn secondary" onClick={handleClose}>取消</button>
        <button
          className="modal-btn primary"
          onClick={onSubmit}
          disabled={uploading || submissionCategoryUnavailable}
        >
          {uploading ? '上传中...' : '提交申报'}
        </button>
      </div>
    </Modal>
  )
}
