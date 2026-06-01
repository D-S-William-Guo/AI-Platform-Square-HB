import { Link } from 'react-router-dom'
import UiIcon from './UiIcon'

interface PageHeaderProps {
  title?: string
  showBackLink?: boolean
  backTo?: string
  showBrand?: boolean
}

export default function PageHeader({
  title,
  showBackLink = true,
  backTo = '/',
  showBrand = true,
}: PageHeaderProps) {
  return (
    <header className="header">
      {showBrand && (
        <div className="brand">
          <div className="brand-icon">河</div>
          <span>HEBEI · AI 应用广场</span>
        </div>
      )}
      {title && <h2 className="page-title">{title}</h2>}
      {showBackLink && (
        <Link to={backTo} className="back-link">
          <UiIcon name="platform" />
          <span>返回首页</span>
        </Link>
      )}
    </header>
  )
}
