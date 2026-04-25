import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import SearchResults from "./pages/SearchResults";
import NoteViewer from "./pages/NoteViewer";
import Connections from "./pages/Connections";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<SearchResults />} />
        <Route path="/note/:id" element={<NoteViewer />} />
        <Route path="/connections" element={<Connections />} />
      </Routes>
    </Router>
  );
}
