import { useState, useCallback } from 'react'

export function usePagination(initialPage = 1, initialPageSize = 10) {
  const [page, setPage] = useState(initialPage)
  const [pageSize, setPageSize] = useState(initialPageSize)
  const [total, setTotal] = useState(0)

  const totalPages = Math.ceil(total / pageSize) || 0

  const goToPage = useCallback((p: number) => {
    setPage(Math.max(1, Math.min(p, totalPages || p)))
  }, [totalPages])

  return {
    page,
    pageSize,
    total,
    totalPages,
    setPage: goToPage,
    setPageSize,
    setTotal,
  }
}
