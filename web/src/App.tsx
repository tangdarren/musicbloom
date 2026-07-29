import { RouterProvider } from "react-router-dom";

import { ErrorBoundary } from "./components/ErrorBoundary";
import { QueryProvider } from "./providers/QueryProvider";
import { router } from "./routes/router";

export default function App() {
  return (
    <ErrorBoundary>
      <QueryProvider>
        <RouterProvider router={router} />
      </QueryProvider>
    </ErrorBoundary>
  );
}
