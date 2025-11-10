/**
 * Main App Component
 * Defines routes and overall application structure
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';

// Import pages (will be created by other agents)
import Dashboard from './pages/Dashboard';
import CaseDetails from './pages/CaseDetails';
import DocumentDetails from './pages/DocumentDetails';
import AnalysisViewer from './pages/AnalysisViewer';
import NotFound from './pages/NotFound';

function App() {
  return (
    <Routes>
      {/* Main Layout Routes */}
      <Route path="/" element={<MainLayout />}>
        {/* Dashboard - Case list */}
        <Route index element={<Dashboard />} />

        {/* Case Details */}
        <Route path="cases/:caseId" element={<CaseDetails />} />

        {/* Document Details */}
        <Route path="cases/:caseId/documents/:documentId" element={<DocumentDetails />} />

        {/* Analysis Viewer */}
        <Route
          path="cases/:caseId/documents/:documentId/analysis"
          element={<AnalysisViewer />}
        />

        {/* 404 Not Found */}
        <Route path="404" element={<NotFound />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
