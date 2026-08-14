import React, { useState, useEffect } from 'react';
import { predictPrice, getHistory, type PredictionRequest } from '../api/client';

const PredictionPage: React.FC = () => {
  const [form, setForm] = useState<PredictionRequest>({
    brand: 'Tesla',
    model: 'Model 3',
    battery: 75,
    autonomy: 400,
    safety: 4,
    year: 2024,
    autonomous_level: 2,
  });

  const [price, setPrice] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [recentHistory, setRecentHistory] = useState<any[]>([]);

  // Fetch stats and recent history on mount
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const history = await getHistory(10);
        setRecentHistory(history.predictions || []);

        // compute stats from history
        if (history.predictions && history.predictions.length > 0) {
          const prices = history.predictions.map((p: any) => p.predicted_price);
          const avg = prices.reduce((a: number, b: number) => a + b, 0) / prices.length;
          setStats({
            total: history.count || history.predictions.length,
            avgPrice: avg,
            minPrice: Math.min(...prices),
            maxPrice: Math.max(...prices),
          });
        } else {
          setStats({ total: 0, avgPrice: 0, minPrice: 0, maxPrice: 0 });
        }
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      }
    };

    fetchStats();
  }, []);

const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
  const { name, value } = e.target;
  setForm((prev) => ({ ...prev, [name]: value }));
};

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setLoading(true);
  setError(null);
  setPrice(null);

  try {
    const response = await predictPrice(form);
    if (response.success) {
      setPrice(response.price || 0);

      //refresh stats after prediction
      const history = await getHistory(10);
      setRecentHistory(history.predictions || []);
    } else {
      setError(response.error || 'Prediction failed');
    }
  } catch (err) {
    setError('Network error: Could not reach the API');
  } finally {
    setLoading(false);
  }
};

return (
  <div className="dashboard">
    {/*STATS ROW*/}
    <div className="stats-row">
      <div className="stat-card">
        <span className="stat-label">Total Predictions</span>
        <span className="stat-value">{stats?.total || 0}</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Average Price</span>
        <span className="stat-value">${(stats?.avgPrice || 0).toFixed(2)}</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Min /Max Price</span>
        <span className="stat-value">${(stats?.minPrice || 0).toFixed(0)} / ${(stats?.maxPrice || 0).toFixed(0)}</span> 
      </div>
      <div className="stat-card">
        <span className="stat-label">Model Status</span>
        <span className="stat-value" style={{ color: 'var(--accent)' }}>Online</span>
      </div>
    </div>

    {/*TWO COLUMN LAYOUT --- Form + Result */}
    <div className="dashboard-grid">
      {/*Prediction Form*/}
      <div className="card">
        <h2> New Prediction</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Brand</label>
            <input type="text" name="brand" value={form.brand} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label>Model</label>
            <input type="text" name="model" value={form.model} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label>Battery (kWh)</label>
            <input type="number" name="battery" value={form.battery} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label>Brand (km)</label>
            <input type="number" name="autonomy" value={form.autonomy} onChange={handleChange} required />
          </div>
          <div className="form-row">
              <div className="form-group">
                <label>Safety (1-5)</label>
                <input type="number" name="safety" value={form.safety} onChange={handleChange} min="1" max="5" required />
              </div>
              <div className="form-group">
                <label>Year</label>
                <input type="number" name="year" value={form.year} onChange={handleChange} min="2015" max="2026" required />
              </div>
            </div>
            <button type="submit" disabled={loading}>
              {loading ? 'Predicting...' : 'Predict Price'}
            </button>
        </form>
      </div>

      {/* Result / Stats Card */}
        <div className="card result-card">
          <h2>Prediction Result</h2>
          {price !== null ? (
            <div className="result-price">
              <span className="currency">USD</span>
              <span className="price">{price.toFixed(2)}</span>
            </div>
          ) : (
            <p className="placeholder">Enter vehicle specs and click "Predict Price"</p>
          )}
          {error && <div className="error-box">{error}</div>}
        </div>
      </div>

      {/* RECENT HISTORY TABLE */}
      <div className="card full-width">
        <h2>Recent Predictions</h2>
        {recentHistory.length === 0 ? (
          <p>No predictions yet.</p>
        ) : (
          <table className="history-table">
            <thead>
              <tr>
                <th>Brand</th>
                <th>Model</th>
                <th>Price (USD)</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {recentHistory.map((item: any) => (
                <tr key={item.id}>
                  <td>{item.brand}</td>
                  <td>{item.model_name}</td>
                  <td>${item.predicted_price?.toFixed(2)}</td>
                  <td>{new Date(item.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
    </div>
  </div>
);

};

export default PredictionPage;