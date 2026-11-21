// Flow 2 (part 2): Status progression and stock update
// Each "Approve" / "Mark ordered" / ... button calls PATCH /api/requests/<id>/status.
// The row's status badge and button update straight away, and when an order is
// delivered the medicine's stock and status in the inventory table update too.

(() => {
    const requestsBody = document.getElementById('requests-body');
    if (!requestsBody) return;   // only runs on the dashboard

    // Update one reorder request row from the API's request data
    function updateRequestRow(row, request) {
        const badge = row.querySelector('.status-badge');
        badge.className = 'status-badge status-' + request.status_class;
        badge.textContent = request.status;

        // The status just changed, so it has been 0 days in this status
        const daysCell = row.cells[5];
        daysCell.textContent = '0';
        daysCell.classList.remove('is-attention');

        const actionCell = row.cells[6];
        if (request.next_action) {
            actionCell.querySelector('button').textContent = request.next_action;
        } else {
            actionCell.innerHTML = '<span class="cell-sub">Complete</span>';
        }
    }

    // Update the medicine's row in the inventory table (stock, reorder point, status, Reorder link)
    function updateInventoryRow(item) {
        const row = Array.from(document.querySelectorAll('#inventory-body tr'))
            .find((tr) => tr.dataset.medicine === item.name);
        if (!row) return;   // medicine is hidden by the category filter

        row.cells[1].textContent = item.current_stock.toLocaleString('en-US');
        row.cells[2].textContent = item.reorder_point.toLocaleString('en-US');

        const badge = row.querySelector('.status-badge');
        badge.className = 'status-badge status-' + item.status.toLowerCase();
        badge.textContent = item.status;

        // Only medicines that are not Sufficient get a Reorder link
        const link = row.querySelector('.row-action');
        if (item.status === 'Sufficient' && link) link.remove();
    }

    // Show a green (success) or red (error) confirmation message (static/js/notify.js)
    function showMessage(text, isError) {
        notify(text, isError ? 'error' : 'success');
    }

    // One listener for every button in the table
    requestsBody.addEventListener('click', async (event) => {
        const button = event.target.closest('button.status-step');
        if (!button) return;

        const row = button.closest('tr');
        const oldLabel = button.textContent;
        button.disabled = true;
        button.textContent = 'Saving…';

        try {
            const result = await apiFetch(`/api/requests/${button.dataset.requestId}/status`, { method: 'PATCH' });
            const { request, inventory } = result.data;

            updateRequestRow(row, request);

            if (request.status === 'Delivered') {
                updateInventoryRow(inventory);
                showMessage(`${request.medicine}: ${request.quantity.toLocaleString('en-US')} units delivered. ` +
                    `Stock is now ${inventory.current_stock.toLocaleString('en-US')} (${inventory.status}).`, false);
            } else {
                showMessage(`${request.medicine} is now ${request.status}.`, false);
            }
        } catch (error) {
            button.textContent = oldLabel;
            showMessage(error.message, true);
        } finally {
            button.disabled = false;
        }
    });
})();
