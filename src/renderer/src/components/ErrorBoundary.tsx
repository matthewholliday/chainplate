import { Component, type ErrorInfo, type ReactNode } from 'react'

type Props = {
  children: ReactNode
}

type State = {
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('Renderer error:', error, info.componentStack)
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <div className="flex h-full items-center justify-center p-6">
          <div className="max-w-lg text-center">
            <h1 className="mb-2 text-lg font-semibold text-foreground">Something went wrong</h1>
            <p className="text-sm text-muted-foreground">{this.state.error.message}</p>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
