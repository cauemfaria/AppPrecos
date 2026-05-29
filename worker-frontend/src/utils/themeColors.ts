/**
 * Semantic color utilities that respond to theme changes.
 * Returns CSS colors adjusted for the current theme.
 */

export const semanticColors = {
  // Icon backgrounds - light, muted versions of semantic colors
  iconBg: {
    primary: 'color-mix(in srgb, var(--color-primary) 8%, var(--color-surface))',
    secondary: 'color-mix(in srgb, var(--color-secondary) 8%, var(--color-surface))',
    error: 'color-mix(in srgb, var(--color-error) 8%, var(--color-surface))',
    success: 'color-mix(in srgb, var(--color-success) 8%, var(--color-surface))',
    cta: 'color-mix(in srgb, var(--color-cta) 8%, var(--color-surface))',
    info: 'color-mix(in srgb, #0D9488 8%, var(--color-surface))',
    accent: 'color-mix(in srgb, #7C3AED 8%, var(--color-surface))',
  },
  
  // Icon colors - bold, saturated versions
  iconColor: {
    primary: 'var(--color-primary)',
    secondary: 'var(--color-secondary)',
    error: 'var(--color-error)',
    success: 'var(--color-success)',
    cta: 'var(--color-cta)',
    info: '#0D9488',
    accent: '#7C3AED',
  },
}
