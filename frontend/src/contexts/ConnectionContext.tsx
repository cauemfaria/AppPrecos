import React, { createContext, useContext } from 'react'

interface ConnectionContextValue {
  isConnected: boolean
}

const ConnectionContext = createContext<ConnectionContextValue | undefined>(undefined)

export function ConnectionProvider({ children, isConnected }: { children: React.ReactNode; isConnected: boolean }) {
  return (
    <ConnectionContext.Provider value={{ isConnected }}>
      {children}
    </ConnectionContext.Provider>
  )
}

export function useConnection() {
  const context = useContext(ConnectionContext)
  if (context === undefined) {
    throw new Error('useConnection must be used within ConnectionProvider')
  }
  return context
}
