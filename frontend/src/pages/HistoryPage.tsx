import React, { useEffect, useState } from 'react';
import { getHistory } from '../api/client';

const HistoryPage: React.FC = () => {
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchHistory =async () => {
            try {
                const data = await getHistory(100);
                setHistory(data.predictions || []);
            } catch (err) {
                setError('Failed to load history');
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);

    if (loading) return <p style={{ padding: '24px', textAlign: 'center' }}>Loading history...</p>;
    if (error) return <p className="error-box" style={{ margin: '24px'}}>{error}</p>;

    return (
        <div className="dashboard">
            <div className="card full-width">
                <h2>Full Prediction History</h2>
                {history.length === 0 ? (
                    <p>No predictions yet</p>
                ) : (
                    <table className="history-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Brand</th>
                                <th>Model</th>
                                <th>Battery (kWh)</th>
                                <th>Range (km)</th>
                                <th>Safety</th>
                                <th>Year</th>
                                <th>Price (USD)</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {history.map((item: any) => (
                                <tr key={item.id}>
                                    <td>{item.id}</td>
                                    <td>{item.brand}</td>
                                    <td>{item.model_name}</td>
                                    <td>{item.battery_capacity}</td>
                                    <td>{item.range_km}</td>
                                    <td>{item.safety_rating}</td>
                                    <td>{item.year}</td>
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

export default HistoryPage;