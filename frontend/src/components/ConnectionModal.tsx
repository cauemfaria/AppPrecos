import { useState } from 'react'

interface ConnectionModalProps {
  isConnected: boolean
  isChecking: boolean
  error: string | null
}

export default function ConnectionModal({ isConnected, isChecking, error }: ConnectionModalProps) {
  if (isConnected && !isChecking) {
    return null  // Hide when connected
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
    >
      <div
        className="rounded-2xl p-8 w-96 max-w-sm"
        style={{
          backgroundColor: 'var(--color-surface)',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div className="flex flex-col items-center gap-4">
          {isChecking && !error ? (
            <>
              <span
                className="w-12 h-12 border-4 rounded-full animate-spin"
                style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }}
              />
              <div className="text-center">
                <p className="text-sm font-semibold" style={{ color: 'var(--color-text)' }}>
                  Conectando ao servidor...
                </p>
                <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
                  Por favor, aguarde
                </p>
              </div>
            </>
          ) : error ? (
            <>
              <div
                className="w-12 h-12 rounded-full flex items-center justify-center"
                style={{ backgroundColor: '#FEF2F2' }}
              >
                <span style={{ color: '#DC2626', fontSize: '20px' }}>⚠️</span>
              </div>
              <div className="text-center">
                <p className="text-sm font-semibold" style={{ color: '#DC2626' }}>
                  Erro de conexão
                </p>
                <p className="text-xs mt-2" style={{ color: 'var(--color-text-muted)' }}>
                  {error}
                </p>
                <p className="text-xs mt-3" style={{ color: 'var(--color-text-muted)' }}>
                  Tentando reconectar...
                </p>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}
