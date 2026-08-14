import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import PredictPage from './pages/PredictPage';
import HistoryPage from './pages/HistoryPage';

function App() {


  return (
    <BrowserRouter>
      <div id="root">
        <nav className="navbar">
          <Link to="/">Predict</Link>
          <Link to="/history">History</Link>
        </nav>
        <main>
          <Routes>
            <Route path="/" element={<PredictPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>
      </div>

    </BrowserRouter>
  );
}

export default App;
