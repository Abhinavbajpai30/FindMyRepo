import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { PreferencesProvider, usePreferences } from "@/contexts/PreferencesContext";
import { BookmarksProvider } from "@/contexts/BookmarksContext";
import ErrorBoundary from "@/components/ErrorBoundary";
import Home from "./pages/Home";
import Onboarding from "./pages/Onboarding";
import SearchResults from "./pages/SearchResults";
import HiddenGems from "./pages/HiddenGems";
import AllRepos from "./pages/AllRepos";
import Hacktoberfest from "./pages/Hacktoberfest";
import Saved from "./pages/Saved";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const AppRoutes = () => {
  const { hasCompletedOnboarding } = usePreferences();

  return (
    <Routes>
      <Route path="/" element={hasCompletedOnboarding ? <Home /> : <Navigate to="/onboarding" />} />
      <Route path="/onboarding" element={<Onboarding />} />
      <Route path="/search" element={<ErrorBoundary><SearchResults /></ErrorBoundary>} />
      <Route path="/hidden-gems" element={<ErrorBoundary><HiddenGems /></ErrorBoundary>} />
      <Route path="/all-repos" element={<ErrorBoundary><AllRepos /></ErrorBoundary>} />
      <Route path="/hacktoberfest" element={<ErrorBoundary><Hacktoberfest /></ErrorBoundary>} />
      <Route path="/saved" element={<ErrorBoundary><Saved /></ErrorBoundary>} />
<Route path="*" element={<NotFound />} />
    </Routes>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <PreferencesProvider>
      <BookmarksProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </TooltipProvider>
      </BookmarksProvider>
    </PreferencesProvider>
  </QueryClientProvider>
);

export default App;
