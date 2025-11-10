/**
 * API Client for Investigation Intelligence Platform
 * Axios-based HTTP client with error handling
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type { ErrorResponse } from '../types';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const API_TIMEOUT = 30000; // 30 seconds

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ErrorResponse>) => {
    // Handle common error scenarios
    if (error.response) {
      // Server responded with error status
      const errorData = error.response.data;

      // Log error for debugging
      console.error('API Error:', {
        status: error.response.status,
        data: errorData,
        url: error.config?.url,
      });

      // Return formatted error
      return Promise.reject({
        message: errorData?.error || 'An error occurred',
        detail: errorData?.detail,
        status: error.response.status,
        data: errorData,
      });
    } else if (error.request) {
      // Request was made but no response received
      console.error('Network Error:', error.request);
      return Promise.reject({
        message: 'Network error - please check your connection',
        detail: 'No response received from server',
        status: 0,
      });
    } else {
      // Something else happened
      console.error('Request Error:', error.message);
      return Promise.reject({
        message: error.message || 'An unexpected error occurred',
        status: 0,
      });
    }
  }
);

/**
 * API Error class for better error handling
 */
export class ApiError extends Error {
  status: number;
  detail?: string;
  data?: any;

  constructor(message: string, status: number, detail?: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.data = data;
  }
}

/**
 * Helper to handle API errors in a consistent way
 */
export function handleApiError(error: any): ApiError {
  if (error instanceof ApiError) {
    return error;
  }

  return new ApiError(
    error.message || 'An error occurred',
    error.status || 500,
    error.detail,
    error.data
  );
}
