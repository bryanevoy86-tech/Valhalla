import { BrowserRouter, Routes, Route } from "react-router-dom";
import Pricing from "./pages/Pricing";
import AuditViewer from "./pages/AuditViewer";
import Notifications from "./pages/Notifications";
import ImportExport from "./pages/ImportExport";
import Search from "./pages/Search";
import Reports from "./pages/Reports";

import AdminConsole from "./pages/AdminConsole";
import Shield from "./pages/Shield";
import Funfund from "./pages/Funfund";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/audit" element={<AuditViewer />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/io" element={<ImportExport />} />
        <Route path="/search" element={<Search />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/org/switch" element={<OrgSwitch />} />
  <Route path="/admin" element={<AdminConsole />} />
  <Route path="/shield" element={<Shield />} />
  <Route path="/funfund" element={<Funfund />} />
  {/* ...existing routes... */}
      </Routes>
    </BrowserRouter>
  );
}
