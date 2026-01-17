import { Link } from "react-router-dom";

export default function Nav() {
  return (
    <nav className="flex gap-3 p-2 border-b">
      <Link to="/search">Search</Link>
      <Link to="/reports">Reports</Link>
      <Link to="/notifications">Notifications</Link>
      <Link to="/io">Import/Export</Link>
      <Link to="/audit">Audit</Link>
      <Link to="/org/switch">Orgs</Link>
      <Link to="/pricing">Pricing</Link>
    </nav>
  );
}
