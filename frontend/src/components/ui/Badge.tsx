import { cn } from '@/lib/utils'
import type { WarningSeverity } from '@/types'
import { AlertCircle, AlertTriangle, Info } from 'lucide-react'

interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
  className?: string
  children: React.ReactNode
}

export function Badge({ variant = 'default', className, children }: BadgeProps) {
  const variants = {
    default: 'bg-muted text-muted-foreground',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  )
}

export function SeverityBadge({ severity }: { severity: WarningSeverity }) {
  const config = {
    info: { variant: 'info' as const, icon: Info, label: 'Info' },
    warning: { variant: 'warning' as const, icon: AlertTriangle, label: 'Warning' },
    critical: { variant: 'error' as const, icon: AlertCircle, label: 'Critical' },
  }

  const { variant, icon: Icon, label } = config[severity]

  return (
    <Badge variant={variant} className="gap-1">
      <Icon className="w-3 h-3" />
      {label}
    </Badge>
  )
}

export function WallTypeBadge({ type }: { type: string }) {
  const config: Record<string, { variant: 'success' | 'warning' | 'error'; label: string }> = {
    load_bearing: { variant: 'error', label: 'Load Bearing' },
    partition: { variant: 'success', label: 'Partition' },
    structural_spine: { variant: 'warning', label: 'Structural Spine' },
  }

  const { variant, label } = config[type] || { variant: 'default' as const, label: type }

  return <Badge variant={variant}>{label}</Badge>
}
