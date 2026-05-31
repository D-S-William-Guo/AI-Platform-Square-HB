import { useState, useCallback } from 'react'

export type ValidationRules<T> = Partial<Record<keyof T, (value: T[keyof T]) => string>>

export function useForm<T extends Record<string, unknown>>(
  initial: T,
  rules: ValidationRules<T> = {},
) {
  const [values, setValues] = useState<T>(initial)
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({})

  const setValue = useCallback(<K extends keyof T>(field: K, value: T[K]) => {
    setValues(prev => ({ ...prev, [field]: value }))
    // Real-time validation
    const rule = rules[field]
    if (rule) {
      const error = rule(value)
      setErrors(prev => {
        const next = { ...prev }
        if (error) {
          next[field] = error
        } else {
          delete next[field]
        }
        return next
      })
    }
  }, [rules])

  const validate = useCallback((): boolean => {
    const newErrors: Partial<Record<keyof T, string>> = {}
    let isValid = true
    for (const [field, rule] of Object.entries(rules) as Array<[string, (value: unknown) => string]>) {
      const error = rule(values[field as keyof T])
      if (error) {
        newErrors[field as keyof T] = error
        isValid = false
      }
    }
    setErrors(newErrors)
    return isValid
  }, [rules, values])

  const reset = useCallback((newValues?: T) => {
    setValues(newValues ?? initial)
    setErrors({})
  }, [initial])

  return { values, errors, setValue, validate, reset, setValues }
}
