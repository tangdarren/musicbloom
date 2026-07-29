import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  message: string;
}

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = {
    hasError: false,
    message: "",
  };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      message: error.message || "Something went wrong.",
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("MusicBloom UI error:", error, errorInfo);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, message: "" });
  };

  render() {
    if (this.state.hasError) {
      return (
        <section className="error-boundary" role="alert">
          <div className="card error-boundary__card">
            <p className="eyebrow">BloomBud needs a moment</p>
            <h1>Something sprouted unexpectedly</h1>
            <p className="lede">{this.state.message}</p>
            <button type="button" className="button" onClick={this.handleRetry}>
              Try again
            </button>
          </div>
        </section>
      );
    }

    return this.props.children;
  }
}
