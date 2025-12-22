import type { WebSocketMessage, WebSocketMessageType } from '../types';

/**
 * WebSocket Service for Real-time Job Updates
 * Handles connection, reconnection, and event subscriptions
 */
class WebSocketService {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;
    private listeners: Map<string, Set<(message: WebSocketMessage) => void>> = new Map();
    private baseURL: string;
    private isConnecting = false;

    constructor() {
        this.baseURL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    }

    /**
     * Connect to WebSocket for a specific job
     */
    connect(jobId: string): void {
        if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
            return;
        }

        this.isConnecting = true;
        const url = `${this.baseURL}/api/jobs/${jobId}/status`;

        try {
            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                console.log(`WebSocket connected for job ${jobId}`);
                this.isConnecting = false;
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                try {
                    const message: WebSocketMessage = JSON.parse(event.data);
                    this.notifyListeners(message.type, message);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.isConnecting = false;
            };

            this.ws.onclose = () => {
                console.log('WebSocket closed');
                this.isConnecting = false;
                this.attemptReconnect(jobId);
            };
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.isConnecting = false;
        }
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    private attemptReconnect(jobId: string): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            this.connect(jobId);
        }, delay);
    }

    /**
     * Subscribe to specific message types
     */
    subscribe(
        messageType: WebSocketMessageType | string,
        callback: (message: WebSocketMessage) => void
    ): () => void {
        if (!this.listeners.has(messageType)) {
            this.listeners.set(messageType, new Set());
        }

        this.listeners.get(messageType)!.add(callback);

        // Return unsubscribe function
        return () => {
            const listeners = this.listeners.get(messageType);
            if (listeners) {
                listeners.delete(callback);
            }
        };
    }

    /**
     * Notify all listeners for a specific message type
     */
    private notifyListeners(messageType: string, message: WebSocketMessage): void {
        const listeners = this.listeners.get(messageType);
        if (listeners) {
            listeners.forEach((callback) => callback(message));
        }
    }

    /**
     * Disconnect WebSocket
     */
    disconnect(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.listeners.clear();
        this.reconnectAttempts = 0;
        this.isConnecting = false;
    }

    /**
     * Check if WebSocket is connected
     */
    isConnected(): boolean {
        return this.ws?.readyState === WebSocket.OPEN;
    }
}

// Export singleton instance
export const wsService = new WebSocketService();
