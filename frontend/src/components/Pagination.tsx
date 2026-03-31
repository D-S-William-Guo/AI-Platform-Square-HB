type PaginationProps = {
  page: number
  pageSize: number
  total: number
  totalPages: number
  disabled?: boolean
  onPageChange: (page: number) => void
  onPageSizeChange?: (pageSize: number) => void
  pageSizeOptions?: number[]
}

function buildPageItems(page: number, totalPages: number) {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1)
  }

  const pages = new Set<number>([1, totalPages, page - 1, page, page + 1])
  if (page <= 3) {
    pages.add(2)
    pages.add(3)
    pages.add(4)
  }
  if (page >= totalPages - 2) {
    pages.add(totalPages - 1)
    pages.add(totalPages - 2)
    pages.add(totalPages - 3)
  }

  const sorted = Array.from(pages)
    .filter((value) => value >= 1 && value <= totalPages)
    .sort((left, right) => left - right)

  const items: Array<number | string> = []
  sorted.forEach((value, index) => {
    const previous = sorted[index - 1]
    if (previous && value - previous > 1) {
      items.push(`ellipsis-${previous}-${value}`)
    }
    items.push(value)
  })
  return items
}

const Pagination = ({
  page,
  pageSize,
  total,
  totalPages,
  disabled = false,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 20],
}: PaginationProps) => {
  const pages = buildPageItems(page, totalPages)
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1
  const end = total === 0 ? 0 : Math.min(page * pageSize, total)

  return (
    <div className="pagination-shell">
      <div className="pagination-summary">
        <strong>{total}</strong>
        <span>条记录</span>
        <span>
          当前显示 {start}-{end}
        </span>
      </div>

      <div className="pagination-controls">
        {onPageSizeChange ? (
          <label className="pagination-size">
            <span>每页</span>
            <select
              value={pageSize}
              disabled={disabled}
              onChange={(event) => onPageSizeChange(Number(event.target.value))}
            >
              {pageSizeOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        ) : null}

        <button
          className="pagination-nav"
          disabled={disabled || page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          上一页
        </button>

        <div className="pagination-pages">
          {pages.map((item) =>
            typeof item === 'number' ? (
              <button
                key={item}
                className={`pagination-page ${item === page ? 'active' : ''}`}
                disabled={disabled}
                onClick={() => onPageChange(item)}
              >
                {item}
              </button>
            ) : (
              <span key={item} className="pagination-ellipsis">
                ...
              </span>
            )
          )}
        </div>

        <button
          className="pagination-nav"
          disabled={disabled || totalPages === 0 || page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          下一页
        </button>
      </div>
    </div>
  )
}

export default Pagination
