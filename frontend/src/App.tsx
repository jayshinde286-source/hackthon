import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppSidebar } from './components/AppSidebar';
import { AppHeader } from './components/AppHeader';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { AnalyzePage } from './pages/AnalyzePage';
import { AnalysisResultPage } from './pages/AnalysisResultPage';
import { ComparePage } from './pages/ComparePage';
import { EvidencePage } from './pages/EvidencePage';
import { ManifestPage } from './pages/ManifestPage';
import { RecoveryPage } from './pages/RecoveryPage';
import { ReportsPage } from './pages/ReportsPage';
import { BenchmarksPage } from './pages/BenchmarksPage';
import { AboutPage } from './pages/AboutPage';
import { VivaGuidePage } from './pages/VivaGuidePage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/20 selection:text-cyan-200">
        {/* Fixed Sidebar */}
        <AppSidebar />

        {/* Main Content Area */}
        <div className="pl-64 flex flex-col min-h-screen flex-1">
          <AppHeader />
          <main className="flex-1 px-8 py-8">
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/analyze" element={<AnalyzePage />} />
              <Route path="/analysis/:id" element={<AnalysisResultPage />} />
              <Route path="/compare" element={<ComparePage />} />
              <Route path="/evidence" element={<EvidencePage />} />
              <Route path="/manifest" element={<ManifestPage />} />
              <Route path="/recovery" element={<RecoveryPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/benchmarks" element={<BenchmarksPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/viva-guide" element={<VivaGuidePage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
};

export default App;
