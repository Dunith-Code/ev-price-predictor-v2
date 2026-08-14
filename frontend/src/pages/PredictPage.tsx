import React, { useState } from 'react';
import { predictPrice, type PredictionRequest } from '../api/client';

const initialForm: PredictionRequest = {
  brand: 'Tesla',
  model: 'Model 3',
  battery: 75,
  autonomy: 400,
  safety: 4,
  year: 2024,
  autonomous_level: 2,
};

const PredictPage: React.FC = () => {
  const [form, setForm] = useState<PredictionRequest>(initialForm);
  const [price, setPrice] = useState<number | null>(null);
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]:
        name === 'battery' ||
        name === 'autonomy' ||
        name === 'safety' ||
        name === 'year' ||
        name === 'autonomous_level'
          ? Number(value)
          : value,
    }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await predictPrice(form);
      if (response.success && response.price !== undefined) {
        setPrice(response.price);
      } else {
        setError(response.error || 'Prediction failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: '500px', margin: '0 auto', padding: '20px' }}>
      <h1>EV Price Predictor</h1>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Brand</label>
          <input type="text" name="brand" value={form.brand} onChange={handleInputChange} required />
        </div>
        <div className="form-group">
          <label>Model</label>
          <input type="text" name="model" value={form.model} onChange={handleInputChange} required />
        </div>
        <div className="form-group">
          <label>Battery (kWh)</label>
          <input type="number" name="battery" value={form.battery} onChange={handleInputChange} step="0.1" required />
        </div>
        <div className="form-group">
          <label>Range (km)</label>
          <input type="number" name="autonomy" value={form.autonomy} onChange={handleInputChange} required />
        </div>
        <div className="form-group">
          <label>Safety Rating (1-5)</label>
          <input type="number" name="safety" value={form.safety} onChange={handleInputChange} min="1" max="5" required />
        </div>
        <div className="form-group">
          <label>Year</label>
          <input type="number" name="year" value={form.year} onChange={handleInputChange} min="2015" max="2026" required />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Predicting...' : 'Predict Price'}
        </button>
      </form>

      {price !== null && (
        <div className="result success">
          <h2>${price.toFixed(2)} USD</h2>
        </div>
      )}
      {error && <div className="result error">{error}</div>}
    </div>
  );
};

export default PredictPage;