// MedSync confirmation messages
// notify() shows a small message in the top-right corner after every action,
// so the user always knows whether it worked. Every page script uses it.

/**
 * Show a confirmation or error message.
 *
 * @param {string} text - What happened, e.g. 'Aspirin 300mg added.'
 * @param {string} type - 'success' (green, the default) or 'error' (red)
 *
 * Examples:
 *   notify('Aspirin 300mg added.');
 *   notify('Could not reach the server.', 'error');
 */
function notify(text, type = 'success') {
    const container = document.getElementById('notifications');
    if (!container) return;

    const message = document.createElement('div');
    message.className = `notification notification-${type}`;
    // Screen readers announce errors straight away and successes politely
    message.setAttribute('role', type === 'error' ? 'alert' : 'status');

    const icon = document.createElement('span');
    icon.className = 'notification-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = type === 'error' ? '!' : '✓';

    const body = document.createElement('p');
    body.className = 'notification-text';
    body.textContent = text;

    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'notification-close';
    close.setAttribute('aria-label', 'Dismiss message');
    close.textContent = '×';
    close.addEventListener('click', () => message.remove());

    message.append(icon, body, close);
    container.append(message);

    // Successes disappear after 5 seconds; errors stay for 10 so there is time to read them
    setTimeout(() => message.remove(), type === 'error' ? 10000 : 5000);
}

// Show Flask flash messages (from form posts that reload the page) the same way
document.querySelectorAll('[data-flash]').forEach((flash) => {
    notify(flash.textContent.trim(), flash.dataset.flash === 'danger' ? 'error' : 'success');
    flash.remove();
});
