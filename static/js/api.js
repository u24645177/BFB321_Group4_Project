// MedSync reusable API helper
// Every page will use apiFetch() to talk to the Flask API (routes/api.py),
// so that requests like JSON handling and error messages work the same for everywhere.

/**
 * Send a request to the API and return the JSON response.
 *
 * @param {string} url - The endpoint, e.g. '/api/medicines'
 * @param {object} options - Optional: { method: 'POST', body: { ... } }
 * @returns {Promise<object>} The JSON data the API sent back
 * @throws {Error} With a friendly message if the request fails
 *
 * Examples:
 *   const medicines = await apiFetch('/api/medicines');
 *   const newOrder = await apiFetch('/api/requests', { method: 'POST', body: { medicine: 'Paracetamol 500mg', quantity: 100 } });
 */
async function apiFetch(url, options = {}) {
    const settings = {
        method: options.method || 'GET',
        headers: { 'Accept': 'application/json' },
    };

    // Only POST/PUT/PATCH requests send a body, converted to JSON
    if (options.body !== undefined) {
        settings.headers['Content-Type'] = 'application/json';
        settings.body = JSON.stringify(options.body);
    }

    // 1. Send the request (this fails if the server is off or there is no internet)
    let response;
    try {
        response = await fetch(url, settings);
    } catch (networkError) {
        throw new Error('Could not reach the server. Check your connection and try again.');
    }

    // 2. Read the reply as JSON (only if the server actually sent JSON)
    const contentType = response.headers.get('Content-Type') || '';
    const data = contentType.includes('application/json') ? await response.json() : null;

    // 3. If the status is an error (400, 404, 500...), throw the API's message
    if (!response.ok) {
        const message = (data && (data.error || data.message)) || `Request failed (${response.status})`;
        const error = new Error(message);
        error.status = response.status;   // e.g. 404, so pages can react differently
        error.details = data;             // the full error JSON, e.g. field errors
        throw error;
    }

    return data;
}
