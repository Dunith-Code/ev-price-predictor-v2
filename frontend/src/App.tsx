import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import PredictionPage from './pages/PredictPage';
import HistoryPage from './pages/HistoryPage';

function App() {


  return (
    <BrowserRouter>
      <div id="root">
        <nav className="navbar">
          <Link to="/" className="nav-link">Predict</Link>
          <Link to="/history" className="nav-link">History</Link>
        </nav>
        <main>
          <Routes>
            <Route path="/" element={<PredictionPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>
      </div>

    </BrowserRouter>
  );
}

export default App;