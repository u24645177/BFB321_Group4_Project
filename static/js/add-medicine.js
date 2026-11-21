// Flow 1: Add medicine
// The form on the dashboard is sent to POST /api/medicines with apiFetch() (static/js/api.js).
// On success the new medicine is added to the inventory table straight away, without reloading.

(() => {
    const form = document.getElementById('medicine-form');
    if (!form) return;   // only runs on the dashboard

    const tableBody = document.getElementById('inventory-body');
    const submitButton = document.getElementById('medicine-submit');

    // Show a green (success) or red (error) confirmation message (static/js/notify.js)
    function showMessage(text, isError) {
        notify(text, isError ? 'error' : 'success');
    } 

    // Remove the red borders and error text from the last attempt
    function clearFieldErrors() {
        form.querySelectorAll('.field-error').forEach((el) => el.remove());
        form.querySelectorAll('[aria-invalid]').forEach((el) => el.removeAttribute('aria-invalid'));
    }

    // Put the API's message under each field it rejected, e.g. { name: 'This medicine already exists.' }
    function showFieldErrors(fields) {
        Object.entries(fields).forEach(([fieldName, text]) => {
            const input = form.elements[fieldName];
            if (!input) return;
            input.setAttribute('aria-invalid', 'true');
            const error = document.createElement('span');
            error.className = 'field-error';
            error.textContent = text;
            input.after(error);
        });
        const firstInvalid = form.querySelector('[aria-invalid="true"]');
        if (firstInvalid) firstInvalid.focus();
    }

    // Build a table row that looks the same as the rows Flask renders in index.html
    function buildRow(medicine) {
        const row = document.createElement('tr');
                row.dataset.medicine = medicine.name;   // lets request-status.js find this row later

        const name = document.createElement('td');
        name.className = 'cell-strong';
        name.textContent = medicine.name;

        const stock = document.createElement('td');
        stock.className = 'num';
        stock.textContent = medicine.current_stock.toLocaleString('en-US');

        const reorderPoint = document.createElement('td');
        reorderPoint.className = 'num';
        reorderPoint.textContent = medicine.reorder_point.toLocaleString('en-US');

        const statusCell = document.createElement('td');
        const statusWrap = document.createElement('div');
        statusWrap.className = 'status-cell';
        const badge = document.createElement('span');
        badge.className = 'status-badge status-' + medicine.status.toLowerCase();
        badge.textContent = medicine.status;
        statusWrap.append(badge);
        if (medicine.status !== 'Sufficient') {
            const link = document.createElement('a');
            link.className = 'row-action';
            link.href = '/reorder?medicine=' + encodeURIComponent(medicine.name);
            link.textContent = 'Reorder';
            statusWrap.append(link);
        }
        statusCell.append(statusWrap);

        row.append(name, stock, reorderPoint, statusCell);
        return row;
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();   // stop the browser reloading the page
        clearFieldErrors();

        // Collect the form values as the JSON body the API expects
        const body = Object.fromEntries(new FormData(form));

        // Loading state: stop double-clicks while the request is running
        submitButton.disabled = true;
        submitButton.textContent = 'Adding...';

        try {
            const result = await apiFetch('/api/medicines', { method: 'POST', body: body });
            const medicine = result.data;

            // Update the table from the API response
            const newRow = buildRow(medicine);
            tableBody.append(newRow);
            clearTableState(tableBody);   // remove the "No medicines" row if it is showing
            newRow.scrollIntoView({ behavior: 'smooth', block: 'center' });

            refreshDashboardKpis();   // live metrics include the new medicine (static/js/live-kpis.js)
            showMessage(`${medicine.name} added. Reorder point: ${medicine.reorder_point} units, status: ${medicine.status}.`, false);
            form.reset();
        } catch (error) {
            showMessage(error.message, true);
            if (error.details && error.details.fields) {
                showFieldErrors(error.details.fields);
            }
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'Add medicine';
        }
    });
})();

