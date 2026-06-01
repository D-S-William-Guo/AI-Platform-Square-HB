import { useState, useCallback } from 'react'
import { createGroupApp, uploadImage } from '../../../api/client'
import { resolveMediaUrl } from '../../../utils/media'
import UiIcon from '../../../components/UiIcon'
import { resolveAdminError } from '../../rankingUtils'

interface GroupAppsTabProps {
  appCategories: string[]
  defaultAppCategory: string
  categoryOptionsLoading: boolean
  categoryOptionsError: string | null
  onError: (msg: string) => void
  onSaved: () => void
}

export default function GroupAppsTab({
  appCategories,
  defaultAppCategory,
  categoryOptionsLoading,
  categoryOptionsError,
  onError,
  onSaved,
}: GroupAppsTabProps) {
  const [form, setForm] = useState({
    name: '', org: '', category: defaultAppCategory, description: '',
    status: 'available', monthly_calls: 0, api_open: false,
    difficulty: 'Low', contact_name: '', highlight: '',
    access_mode: 'direct', access_url: '', target_system: '',
    target_users: '', problem_statement: '',
    effectiveness_type: 'efficiency_gain', effectiveness_metric: '',
    cover_image_url: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [imageUploading, setImageUploading] = useState(false)
  const [imageUploadProgress, setImageUploadProgress] = useState(0)

  const resetForm = () => {
    setForm({
      name: '', org: '', category: defaultAppCategory, description: '',
      status: 'available', monthly_calls: 0, api_open: false,
      difficulty: 'Low', contact_name: '', highlight: '',
      access_mode: 'direct', access_url: '', target_system: '',
      target_users: '', problem_statement: '',
      effectiveness_type: 'efficiency_gain', effectiveness_metric: '',
      cover_image_url: '',
    })
    setImagePreview(null)
    setImageUploadProgress(0)
  }

  const handleImageUpload = useCallback(async (file: File) => {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg']
    if (!allowedTypes.includes(file.type)) {
      onError('集团应用封面图仅支持 JPG、PNG 格式')
      return
    }
    const maxSize = 5 * 1024 * 1024
    if (file.size > maxSize) {
      onError('集团应用封面图不能超过 5MB')
      return
    }

    const reader = new FileReader()
    reader.onload = (event) => { setImagePreview(event.target?.result as string) }
    reader.readAsDataURL(file)

    setImageUploading(true)
    setImageUploadProgress(0)
    try {
      const result = await uploadImage(file, 'group_app')
      if (result.success) {
        setForm((prev) => ({ ...prev, cover_image_url: result.image_url }))
        setImageUploadProgress(100)
      } else {
        onError(result.message || '集团应用封面图上传失败')
        setImagePreview(null)
      }
    } catch (err) {
      onError(resolveAdminError(err, '集团应用封面图上传失败'))
      setImagePreview(null)
    } finally {
      setImageUploading(false)
    }
  }, [onError])

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) handleImageUpload(file)
    event.target.value = ''
  }, [handleImageUpload])

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const file = event.dataTransfer.files?.[0]
    if (file) handleImageUpload(file)
  }, [handleImageUpload])

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
  }, [])

  const removeImage = useCallback(() => {
    setImagePreview(null)
    setImageUploadProgress(0)
    setForm((prev) => ({ ...prev, cover_image_url: '' }))
  }, [])

  const handleSave = async () => {
    if (categoryOptionsLoading || categoryOptionsError || appCategories.length === 0) {
      onError(categoryOptionsError || '分类配置加载中，请稍后重试')
      return
    }
    const name = form.name.trim()
    const org = form.org.trim()
    const category = form.category.trim()
    const description = form.description.trim()
    if (!name || !org || !category || !description) {
      onError('请先填写集团应用录入的必填项')
      return
    }

    try {
      setSubmitting(true)
      setMessage(null)
      await createGroupApp({
        ...form, name, org, category, description,
        monthly_calls: Number(form.monthly_calls || 0),
        access_url: form.access_url.trim(),
        target_system: form.target_system.trim(),
        target_users: form.target_users.trim(),
        problem_statement: form.problem_statement.trim(),
        effectiveness_metric: form.effectiveness_metric.trim(),
        cover_image_url: form.cover_image_url.trim(),
        contact_name: form.contact_name.trim(),
        highlight: form.highlight.trim(),
      })
      setMessage('集团应用录入成功')
      resetForm()
      onSaved()
    } catch (err) {
      onError(resolveAdminError(err, '集团应用录入失败'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="group-app-section">
      <div className="section-header">
        <h2>集团应用录入</h2>
        <button
          className="primary-button"
          onClick={handleSave}
          disabled={submitting || categoryOptionsLoading || Boolean(categoryOptionsError)}
        >
          {submitting ? '保存中...' : '保存集团应用'}
        </button>
      </div>
      <p className="section-note">
        集团应用与省内应用保持同构字段，但仅管理员录入，不进入省内申报审核链路。
      </p>

      {message && <div className="sync-message success">{message}</div>}
      {categoryOptionsError && <div className="sync-message">{categoryOptionsError}</div>}

      <form className="group-app-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="group-name">应用名称 *</label>
            <input id="group-name" type="text" value={form.name}
              onChange={(e) => setForm(prev => ({ ...prev, name: e.target.value }))}
              placeholder="请输入集团应用名称" />
          </div>
          <div className="form-group">
            <label htmlFor="group-org">所属单位 *</label>
            <input id="group-org" type="text" value={form.org}
              onChange={(e) => setForm(prev => ({ ...prev, org: e.target.value }))}
              placeholder="请输入所属单位" />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="group-category">分类 *</label>
            <select id="group-category" value={form.category}
              onChange={(e) => setForm(prev => ({ ...prev, category: e.target.value }))}
              disabled={categoryOptionsLoading || Boolean(categoryOptionsError)}>
              {appCategories.map((category) => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="group-status">状态</label>
            <select id="group-status" value={form.status}
              onChange={(e) => setForm(prev => ({ ...prev, status: e.target.value }))}>
              <option value="available">可用</option>
              <option value="beta">试运行</option>
              <option value="approval">需申请</option>
              <option value="offline">已下线</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="group-description">应用描述 *</label>
          <textarea id="group-description" rows={4} value={form.description}
            onChange={(e) => setForm(prev => ({ ...prev, description: e.target.value }))}
            placeholder="请输入应用描述（不少于10字）" />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="group-access-mode">接入方式</label>
            <select id="group-access-mode" value={form.access_mode}
              onChange={(e) => setForm(prev => ({ ...prev, access_mode: e.target.value }))}>
              <option value="direct">直接接入</option>
              <option value="profile">介绍页跳转</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="group-access-url">访问地址</label>
            <input id="group-access-url" type="text" value={form.access_url}
              onChange={(e) => setForm(prev => ({ ...prev, access_url: e.target.value }))}
              placeholder="https://..." />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="group-monthly-calls">月调用量</label>
            <input id="group-monthly-calls" type="number" min="0" step="1" value={form.monthly_calls}
              onChange={(e) => setForm(prev => ({ ...prev, monthly_calls: Number(e.target.value || 0) }))} />
          </div>
          <div className="form-group checkbox-group">
            <input id="group-api-open" type="checkbox" checked={form.api_open}
              onChange={(e) => setForm(prev => ({ ...prev, api_open: e.target.checked }))} />
            <label htmlFor="group-api-open">开放API</label>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="group-target-system">接入系统</label>
            <input id="group-target-system" type="text" value={form.target_system}
              onChange={(e) => setForm(prev => ({ ...prev, target_system: e.target.value }))} />
          </div>
          <div className="form-group">
            <label htmlFor="group-target-users">适用人群</label>
            <input id="group-target-users" type="text" value={form.target_users}
              onChange={(e) => setForm(prev => ({ ...prev, target_users: e.target.value }))} />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="group-effectiveness-type">成效类型</label>
            <select id="group-effectiveness-type" value={form.effectiveness_type}
              onChange={(e) => setForm(prev => ({ ...prev, effectiveness_type: e.target.value }))}>
              <option value="cost_reduction">降本</option>
              <option value="efficiency_gain">增效</option>
              <option value="perception_uplift">感知提升</option>
              <option value="revenue_growth">拉动收入</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="group-effectiveness-metric">成效指标</label>
            <input id="group-effectiveness-metric" type="text" value={form.effectiveness_metric}
              onChange={(e) => setForm(prev => ({ ...prev, effectiveness_metric: e.target.value }))} />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="group-problem">解决问题</label>
          <textarea id="group-problem" rows={3} value={form.problem_statement}
            onChange={(e) => setForm(prev => ({ ...prev, problem_statement: e.target.value }))} />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="group-contact-name">联系人</label>
            <input id="group-contact-name" type="text" value={form.contact_name}
              onChange={(e) => setForm(prev => ({ ...prev, contact_name: e.target.value }))} />
          </div>
          <div className="form-group">
            <label htmlFor="group-difficulty">接入难度</label>
            <select id="group-difficulty" value={form.difficulty}
              onChange={(e) => setForm(prev => ({ ...prev, difficulty: e.target.value }))}>
              <option value="Low">低</option>
              <option value="Medium">中</option>
              <option value="High">高</option>
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="group-highlight">亮点标签</label>
            <input id="group-highlight" type="text" value={form.highlight}
              onChange={(e) => setForm(prev => ({ ...prev, highlight: e.target.value }))} />
          </div>
          <div className="form-group">
            <label>集团应用封面图</label>
            <div
              className={`group-image-upload-area ${(imagePreview || form.cover_image_url) ? 'has-image' : ''}`}
              onDrop={handleDrop} onDragOver={handleDragOver}
            >
              {(imagePreview || form.cover_image_url) ? (
                <div className="group-image-preview">
                  <img src={imagePreview || resolveMediaUrl(form.cover_image_url)} alt="集团应用封面预览" />
                  <button type="button" className="remove-image" aria-label="移除集团应用封面图"
                    onClick={(event) => { event.preventDefault(); event.stopPropagation(); removeImage() }}>×</button>
                </div>
              ) : (
                <div className="upload-placeholder">
                  <div className="upload-icon"><UiIcon name="upload" /></div>
                  <p>点击或拖拽上传封面图</p>
                  <p className="upload-hint">集团应用图片保存到独立目录，支持 JPG、PNG，最大 5MB</p>
                </div>
              )}
              <input type="file" accept="image/jpeg,image/png,image/jpg" onChange={handleFileSelect} className="file-input" />
              {imageUploading && (
                <div className="upload-progress"><div className="progress-bar" style={{ width: `${imageUploadProgress}%` }} /></div>
              )}
            </div>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="group-cover-url">封面图 URL（可选兜底）</label>
          <input id="group-cover-url" type="text" value={form.cover_image_url}
            onChange={(e) => { setImagePreview(null); setForm(prev => ({ ...prev, cover_image_url: e.target.value })) }}
            placeholder="上传成功后自动填充，也可粘贴已有图片地址" />
          <p className="form-hint">手填地址仅作为补录兜底；新上传图片会进入集团应用独立目录。</p>
        </div>
      </form>
    </section>
  )
}
