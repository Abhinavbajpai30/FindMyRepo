import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { PreferencesProvider, usePreferences } from "@/contexts/PreferencesContext";
import Home from "./pages/Home";
import Onboarding from "./pages/Onboarding";
import SearchResults from "./pages/SearchResults";
import HiddenGems from "./pages/HiddenGems";
import AllRepos from "./pages/AllRepos";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const AppRoutes = () => {
  const { hasCompletedOnboarding } = usePreferences();

  return (
    <Routes>
      <Route path="/" element={hasCompletedOnboarding ? <Home /> : <Navigate to="/onboarding" />} />
      <Route path="/onboarding" element={<Onboarding />} />
      <Route path="/search" element={<SearchResults />} />
      <Route path="/hidden-gems" element={<HiddenGems />} />
      <Route path="/all-repos" element={<AllRepos />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <PreferencesProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </TooltipProvider>
    </PreferencesProvider>
  </QueryClientProvider>
);

export default App;
