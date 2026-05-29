interface ConnectionModalProps {
  isChecking: boolean
  error: string | null
  onRetry?: () => void
}

export default function ConnectionModal({ isChecking, error, onRetry }: ConnectionModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
    >
      <div
        className="rounded-2xl p-8 w-96 max-w-sm mx-4"
        style={{
          backgroundColor: 'var(--color-surface)',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div className="flex flex-col items-center gap-4">
          {isChecking ? (
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
                  {error ?? 'Por favor, aguarde'}
                </p>
              </div>
            </>
          ) : (
            <>
              <div
                className="w-12 h-12 rounded-full flex items-center justify-center text-xl"
                style={{ backgroundColor: 'color-mix(in srgb, var(--color-error) 5%, var(--color-surface))' }}
              >
                ⚠️
              </div>
              <div className="text-center">
                <p className="text-sm font-semibold" style={{ color: 'var(--color-error)' }}>
                  Erro de conexão
                </p>
                <p className="text-xs mt-2" style={{ color: 'var(--color-text-muted)' }}>
                  {error ?? 'Não foi possível conectar ao servidor.'}
                </p>
                <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
                  Tentando reconectar automaticamente...
                </p>
              </div>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="mt-1 px-5 py-2 rounded-xl text-sm font-semibold transition-all duration-200 active:scale-[0.97]"
                  style={{
                    backgroundColor: 'var(--color-primary)',
                    color: 'white',
                    fontFamily: 'var(--font-body)',
                  }}
                >
                  Tentar novamente
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
