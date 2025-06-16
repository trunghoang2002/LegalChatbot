const API_BASE_URL = process.env.REACT_APP_API_URL || '';

export const API_URLS = {
    LOGIN: `${API_BASE_URL}/login`,
    REGISTER: `${API_BASE_URL}/register`,
    PROFILE: `${API_BASE_URL}/api/profile`,
    SESSIONS: `${API_BASE_URL}/api/sessions`,
    CHAT: `${API_BASE_URL}/api/chat`,
    CHAT_STREAM: `${API_BASE_URL}/api/chat-stream`,
    HISTORY: (sessionId) => `${API_BASE_URL}/api/history/${sessionId}`,
    SESSION: (sessionId) => `${API_BASE_URL}/api/sessions/${sessionId}`,
}; 