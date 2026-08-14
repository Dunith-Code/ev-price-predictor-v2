import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
    baseURL: API_URL,
    headers: { 'Content-Type': 'application/json'}
});

//Typescript interfaces (matching FastAPI)
export interface PredictionRequest {
    brand: string;
    model: string;
    battery: number;
    autonomy: number;
    safety: number;
    year: number;
    autonomous_level?: number;
}

export interface PredictionResponse {
    success: boolean;
    price?: number;
    currency?: string;
    error?: string;
}

export interface HistoryResponse {
    success: boolean;
    count: number;
    predictions: any[];
}

// API Functions
export const predictPrice = async (
    data: PredictionRequest
): Promise<PredictionResponse> => {
    const response = await client.post<PredictionResponse>('/predict', data);
    return response.data;
};

export const getHistory = async (limit: number = 50): Promise<HistoryResponse> => {
    const response = await client.get(`/history?limit=${limit}`);
    return response.data;
};