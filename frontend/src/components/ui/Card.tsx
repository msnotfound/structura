import { cn } from '@/lib/utils'
import React from 'react'

interface CardProps {
  className?: string
  children: React.ReactNode
  style?: React.CSSProperties
}

export function Card({ className, children, style }: CardProps) {
  return (
    <div className={cn('card p-6', className)} style={style}>
      {children}
    </div>
  )
}

interface CardHeaderProps {
  className?: string
  children: React.ReactNode
  style?: React.CSSProperties
}

export function CardHeader({ className, children, style }: CardHeaderProps) {
  return (
    <div className={cn('mb-4', className)} style={style}>
      {children}
    </div>
  )
}

interface CardTitleProps {
  className?: string
  children: React.ReactNode
  style?: React.CSSProperties
}

export function CardTitle({ className, children, style }: CardTitleProps) {
  return (
    <h3 className={cn('text-lg font-semibold text-foreground', className)} style={style}>
      {children}
    </h3>
  )
}

interface CardDescriptionProps {
  className?: string
  children: React.ReactNode
  style?: React.CSSProperties
}

export function CardDescription({ className, children, style }: CardDescriptionProps) {
  return (
    <p className={cn('text-sm text-muted-foreground mt-1', className)} style={style}>
      {children}
    </p>
  )
}

interface CardContentProps {
  className?: string
  children: React.ReactNode
  style?: React.CSSProperties
}

export function CardContent({ className, children, style }: CardContentProps) {
  return (
    <div className={cn('', className)} style={style}>
      {children}
    </div>
  )
}
