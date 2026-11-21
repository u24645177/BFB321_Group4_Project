// Flow 3: Update delivery status or exception
// The modal on the delivery board sends PATCH /api/deliveries/<id> with apiFetch() (static/js/api.js).
// The row and the delivery KPI cards update straight away, and the KPI page shows the same numbers.

(() => {
    const modalElement = document.getElementById('exceptionModal');
    if (!modalElement) return;   // only runs on the tracking page

    const form = document.getElementById('exceptionForm');
    const statusSelect = document.getElementById('exceptionStatus');
    const exceptionText = document.getElementById('exceptionText');
    const modalError = document.getElementById('modal-error');
    const saveButton = form.querySelector('button[type="submit"]');
    let currentButton = null;   // the "Report exception" button that opened the modal

    // Same colours as the status_badge macro in templates/components/macros.html
    const BADGE_COLOURS = {
        'Delivered': 'success', 'Delayed': 'warning text-dark', 'Failed': 'danger',
        'In Transit': 'primary', 'Scheduled': 'secondary',
    };

    // Fill the modal with the selected delivery's details when it opens
    modalElement.addEventListener('show.bs.modal', (event) => {
        currentButton = event.relatedTarget;
        form.classList.remove('was-validated');
        modalError.classList.add('d-none');
        document.getElementById('modalDeliveryId').textContent = currentButton.dataset.id;
        statusSelect.value = currentButton.dataset.status;
        exceptionText.value = currentButton.dataset.exception;
    });

    // Update the delivery's row on the board
    function updateRow(delivery) {
        const row = document.querySelector(`tr[data-delivery-id="${delivery.id}"]`);
        const colour = BADGE_COLOURS[delivery.status] || 'secondary';
        row.cells[4].innerHTML = `<span class="badge bg-${colour}"></span>`;
        row.cells[4].firstChild.textContent = delivery.status;
        row.cells[5].textContent = delivery.exception || '—';

        // So the modal shows the new values next time it opens
        currentButton.dataset.status = delivery.status;
        currentButton.dataset.exception = delivery.exception;
    }

    // Update the four delivery KPI cards at the top of the board
    function updateSummary(summary) {
        const values = {
            in_transit: summary.in_transit,
            problems: summary.problems,
            delivered: summary.delivered_percent + '%',
            open_exceptions: summary.open_exceptions,
        };
        Object.entries(values).forEach(([key, value]) => {
            const card = document.querySelector(`[data-summary="${key}"]`);
            if (card) card.querySelector('.kpi-value').textContent = value;
        });
        const deliveredCard = document.querySelector('[data-summary="delivered"] .kpi-target');
        if (deliveredCard) deliveredCard.textContent = `${summary.delivered} of ${summary.total} deliveries`;
    }

        // ---- Loading the board from the API (loading, empty and error states) ----

    const tableBody = document.getElementById('deliveries-body');
    const refreshButton = document.getElementById('refresh-deliveries');

    // Build one delivery row, the same as the old server-rendered rows
    function buildRow(delivery) {
        const row = tableBody.insertRow();
        row.dataset.deliveryId = delivery.id;

        [delivery.id, delivery.route, delivery.vehicle, delivery.eta].forEach((value) => {
            row.insertCell().textContent = value;
        });

        const badge = document.createElement('span');
        badge.className = 'badge bg-' + (BADGE_COLOURS[delivery.status] || 'secondary');
        badge.textContent = delivery.status;
        row.insertCell().append(badge);

        row.insertCell().textContent = delivery.exception || '—';

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-sm btn-outline-danger';
        button.dataset.bsToggle = 'modal';
        button.dataset.bsTarget = '#exceptionModal';
        button.dataset.id = delivery.id;
        button.dataset.status = delivery.status;
        button.dataset.exception = delivery.exception;
        button.textContent = 'Report exception';
        row.insertCell().append(button);
    }

    // Load every delivery from GET /api/deliveries and show the right state
    async function loadDeliveries() {
        showTableState(tableBody, 'loading', 'Loading deliveries…');
        refreshButton.disabled = true;

        try {
            const result = await apiFetch('/api/deliveries');

            if (result.data.length === 0) {
                showTableState(tableBody, 'empty', 'No deliveries scheduled yet.');
            } else {
                clearTableState(tableBody);
                result.data.forEach(buildRow);
            }
            updateSummary(result.summary);
        } catch (error) {
            showTableState(tableBody, 'error', 'Could not load deliveries: ' + error.message, loadDeliveries);
        } finally {
            refreshButton.disabled = false;
        }
    }

    refreshButton.addEventListener('click', loadDeliveries);
    loadDeliveries();   // load the board as soon as the page opens
    
    form.addEventListener('submit', async (event) => {
        event.preventDefault();   // stop the normal page reload
        modalError.classList.add('d-none');

        saveButton.disabled = true;
        saveButton.textContent = 'Saving…';

        try {
            const result = await apiFetch('/api/deliveries/' + encodeURIComponent(currentButton.dataset.id), {
                method: 'PATCH',
                body: { status: statusSelect.value, exception: exceptionText.value },
            });
            const { delivery, summary } = result.data;

            updateRow(delivery);
            updateSummary(summary);
            bootstrap.Modal.getInstance(modalElement).hide();

            notify(`Delivery ${delivery.id} updated: ${delivery.status}` +
                (delivery.exception ? ` (${delivery.exception}).` : '.'));
                
        } catch (error) {
            // Keep the modal open and show what to fix
            const fields = error.details && error.details.fields;
            modalError.textContent = fields ? Object.values(fields).join(' ') : error.message;
            modalError.classList.remove('d-none');
        } finally {
            saveButton.disabled = false;
            saveButton.textContent = 'Save';
        }
    });
})();