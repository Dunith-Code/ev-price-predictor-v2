import React, { useEffect, useState } from 'react';
import { getHistory } from '../api/client';

const HistoryPage: React.FC = () => {
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchHistory =async () => {
            try {
                const data = await getHistory(20);
                setHistory(data.predictions || []);
            } catch (err) {
                setError('Failed to load history');
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);

    if (loading) return <p>Loading history...</p>;
    if (error) return <p className="error">{error}</p>;

    return (
        <div className="container" style={{ maxWidth: '700px', margin: '0 auto', padding: '20px' }}>
            <h1>Prediction History</h1>
            {history.length === 0? (
                <p>No prediction yet. Go back and predict one!</p>
            ) : (
                <ul className="history-list">
                    {history.map((item) => (
                        <li key={item.id}>
                            <span>
                                {item.brand} {item.model_name}
                            </span>
                            <span className="price">${item.predicted_price?.toFixed(2)}</span>
                            <span className="date">${new Date(item.created_at).toLocaleString()}</span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default HistoryPage;