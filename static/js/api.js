/**
 * API клиент для работы с сервером
 */

const API_BASE = '/api';

// ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

async function request(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || `Ошибка ${response.status}`);
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, error: error.message };
    }
}

// ==================== МЕРОПРИЯТИЯ ====================

async function getEvents() {
    const result = await request(`${API_BASE}/events`);
    return result.success ? result.data : [];
}

async function getEvent(id) {
    const result = await request(`${API_BASE}/events/${id}`);
    return result.success ? result.data : null;
}

async function createEvent(data) {
    return request(`${API_BASE}/events`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function updateEvent(id, data) {
    return request(`${API_BASE}/events/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

async function deleteEvent(id) {
    return request(`${API_BASE}/events/${id}`, {
        method: 'DELETE'
    });
}

async function getEventsByDate(date) {
    const result = await request(`${API_BASE}/events/date/${date}`);
    return result.success ? result.data : [];
}

async function getEventsByRange(start, end) {
    const result = await request(`${API_BASE}/events/range?start=${start}&end=${end}`);
    return result.success ? result.data : [];
}

async function getEventTypes() {
    const result = await request(`${API_BASE}/event-types`);
    return result.success ? result.data : [];
}

// ==================== УЧАСТНИКИ ====================

async function getParticipants() {
    const result = await request(`${API_BASE}/participants`);
    return result.success ? result.data : [];
}

async function getParticipant(id) {
    const result = await request(`${API_BASE}/participants/${id}`);
    return result.success ? result.data : null;
}

async function createParticipant(data) {
    return request(`${API_BASE}/participants`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function updateParticipant(id, data) {
    return request(`${API_BASE}/participants/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

async function deleteParticipant(id) {
    return request(`${API_BASE}/participants/${id}`, {
        method: 'DELETE'
    });
}

async function searchParticipants(query) {
    const result = await request(`${API_BASE}/participants/search?q=${encodeURIComponent(query)}`);
    return result.success ? result.data : [];
}

// ==================== ЗАПИСЬ НА МЕРОПРИЯТИЯ ====================

async function registerToEvent(eventId, participantId) {
    return request(`${API_BASE}/events/${eventId}/register`, {
        method: 'POST',
        body: JSON.stringify({ participant_id: participantId })
    });
}

async function unregisterFromEvent(eventId, participantId) {
    return request(`${API_BASE}/events/${eventId}/unregister/${participantId}`, {
        method: 'DELETE'
    });
}

async function getEventParticipants(eventId) {
    const result = await request(`${API_BASE}/events/${eventId}/participants`);
    return result.success ? result.data : [];
}

async function getParticipantEvents(participantId) {
    const result = await request(`${API_BASE}/participants/${participantId}/events`);
    return result.success ? result.data : [];
}

// ==================== СТАТИСТИКА И ЛОГИ ====================

async function getStatistics() {
    const result = await request(`${API_BASE}/statistics`);
    return result.success ? result.data : null;
}

async function getLogs(limit = 100) {
    const result = await request(`${API_BASE}/logs?limit=${limit}`);
    return result.success ? result.data : [];
}

// ==================== ОТЧЁТЫ PDF ====================

function downloadEventsReport(start, end) {
    window.open(`${API_BASE}/reports/events/pdf?start=${start}&end=${end}`);
}

function downloadStatisticsReport() {
    window.open(`${API_BASE}/reports/statistics/pdf`);
}