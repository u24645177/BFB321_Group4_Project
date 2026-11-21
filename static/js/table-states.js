// MedSync table states
// showTableState() replaces a table's rows with one full-width message row, so the
// user always sees what is happening: loading, nothing to show yet, or an error.
// Used by any page that fills a table from the API (e.g. static/js/tracking.js).

/**
 * Show a loading, empty or error message inside a table body.
 *
 * @param {HTMLElement} tbody - The <tbody> to fill
 * @param {string} state - 'loading', 'empty' or 'error'
 * @param {string} message - The text to show
 * @param {Function} onRetry - Optional: for 'error', what the Retry button should do
 *
 * Examples:
 *   showTableState(tbody, 'loading', 'Loading deliveries…');
 *   showTableState(tbody, 'empty', 'No deliveries scheduled yet.');
 *   showTableState(tbody, 'error', error.message, loadDeliveries);
 */
function showTableState(tbody, state, message, onRetry) {
    const table = tbody.closest('table');
    const columnCount = table.querySelectorAll('thead th').length;

    // Screen readers are told the table is busy while it loads
    table.setAttribute('aria-busy', state === 'loading' ? 'true' : 'false');

    tbody.innerHTML = '';
    const row = tbody.insertRow();
    row.className = 'table-state table-state-' + state;

    const cell = row.insertCell();
    cell.colSpan = columnCount;   // one cell across the whole table
    cell.setAttribute('role', state === 'error' ? 'alert' : 'status');

    if (state === 'loading') {
        const spinner = document.createElement('span');
        spinner.className = 'table-spinner';
        spinner.setAttribute('aria-hidden', 'true');
        cell.append(spinner);
    }

    const text = document.createElement('span');
    text.textContent = message;
    cell.append(text);

    if (state === 'error' && onRetry) {
        const retry = document.createElement('button');
        retry.type = 'button';
        retry.className = 'btn btn-sm btn-outline-secondary table-state-retry';
        retry.textContent = 'Retry';
        retry.addEventListener('click', onRetry);
        cell.append(retry);
    }
}

/**
 * Remove the state row (if there is one) before real rows are added.
 */
function clearTableState(tbody) {
    const stateRow = tbody.querySelector('.table-state');
    if (stateRow) stateRow.remove();
    tbody.closest('table').setAttribute('aria-busy', 'false');
}
