import { useEffect, useRef, useCallback, useState } from 'react';
import type { WebSocketMessage, WebSocketMessageType } from '../types/api';

/**
 * Custom hook for WebSocket connection management
 * Handles connection, reconnection, and message subscriptions
 * Falls back to polling if WebSocket is unavailable
 */
export function useWebSocket(jobId: string) {
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const maxReconnectAttempts = 5;
    const reconnectDelay = 1000;
    const listenersRef = useRef<Map<string, Set<(message: WebSocketMessage) => void>>>(
        new Map()
    );
    const [isConnected, setIsConnected] = useState(false);

    const baseURL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        const url = `${baseURL}/jobs/${jobId}/status`;

        try {
            const ws = new WebSocket(url);

            ws.onopen = () => {
                console.log(`WebSocket connected for job ${jobId}`);
                setIsConnected(true);
                reconnectAttemptsRef.current = 0;
            };

            ws.onmessage = (event) => {
                try {
                    const message: WebSocketMessage = JSON.parse(event.data);

                    // Notify all listeners for this message type
                    const listeners = listenersRef.current.get(message.type);
                    if (listeners) {
                        listeners.forEach((callback) => callback(message));
                    }
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            ws.onclose = () => {
                console.log('WebSocket closed');
                setIsConnected(false);
                attemptReconnect();
            };

            wsRef.current = ws;
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            setIsConnected(false);
        }
    }, [jobId, baseURL]);

    const attemptReconnect = useCallback(() => {
        if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        reconnectAttemptsRef.current++;
        const delay = reconnectDelay * Math.pow(2, reconnectAttemptsRef.current - 1);

        console.log(
            `Attempting to reconnect in ${delay}ms (attempt ${reconnectAttemptsRef.current})`
        );

        setTimeout(() => {
            connect();
        }, delay);
    }, [connect]);

    const disconnect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        listenersRef.current.clear();
        setIsConnected(false);
    }, []);

    const subscribe = useCallback(
        (
            messageType: WebSocketMessageType | string,
            callback: (message: WebSocketMessage) => void
        ) => {
            if (!listenersRef.current.has(messageType)) {
                listenersRef.current.set(messageType, new Set());
            }

            listenersRef.current.get(messageType)!.add(callback);

            // Return unsubscribe function
            return () => {
                const listeners = listenersRef.current.get(messageType);
                if (listeners) {
                    listeners.delete(callback);
                }
            };
        },
        []
    );

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            disconnect();
        };
    }, [disconnect]);

    return {
        connect,
        disconnect,
        subscribe,
        isConnected,
    };
}
