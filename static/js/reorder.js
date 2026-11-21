// Flow 2 (part 1): Reorder using the EOQ-recommended quantity
// When a medicine is chosen, GET /api/eoq fills in the EOQ quantity.
// Submitting sends the request to POST /api/requests with apiFetch() (static/js/api.js).

(() => {
    const form = document.getElementById('reorder-form');
    if (!form) return;   // only runs on the reorder page

    const medicineSelect = document.getElementById('medicine');
    const quantityInput = document.getElementById('quantity');
    const hint = document.getElementById('eoq-hint');
    const submitButton = form.querySelector('button[type="submit"]');
    

    // Show a green (success) or red (error) confirmation message (static/js/notify.js)
    function showToast(text, isError) {
        notify(text, isError ? 'error' : 'success');
    }

    // Ask the API for the EOQ and put it in the quantity box
    async function loadRecommendation() {
        const medicine = medicineSelect.value;
        if (!medicine) return;

        hint.textContent = 'Calculating EOQ…';
        try {
            const result = await apiFetch('/api/eoq?medicine=' + encodeURIComponent(medicine));
            const eoq = result.data;
            quantityInput.value = eoq.recommended_quantity;
            hint.textContent = `EOQ recommends ${eoq.recommended_quantity.toLocaleString('en-US')} units ` +
                `(annual demand ${eoq.annual_demand.toLocaleString('en-US')}, R${eoq.order_cost} per order, ` +
                `R${eoq.holding_cost} holding cost per unit). Current stock: ${eoq.current_stock}, ` +
                `reorder point: ${eoq.reorder_point}.`;
        } catch (error) {
            hint.textContent = 'Could not load the EOQ recommendation: ' + error.message;
        }
    }

    medicineSelect.addEventListener('change', loadRecommendation);
    loadRecommendation();   // also runs when the page opens from a "Reorder" link with a medicine chosen

    form.addEventListener('submit', async (event) => {
        event.preventDefault();               // stop the normal page reload
        if (!form.checkValidity()) return;    // main.js already shows the red field messages

        const body = Object.fromEntries(new FormData(form));

        submitButton.disabled = true;
        submitButton.textContent = 'Submitting…';

        try {
            const result = await apiFetch('/api/requests', { method: 'POST', body: body });
            const created = result.data;
            showToast(`Request #${created.id}: ${created.quantity.toLocaleString('en-US')} × ${created.medicine} ` +
                `submitted. Status: ${created.status}. Track it on the dashboard.`, false);
            form.reset();
            form.classList.remove('was-validated');
            hint.textContent = 'Choose a medicine to see the EOQ recommendation.';
        } catch (error) {
            const fields = error.details && error.details.fields;
            const detail = fields ? ' ' + Object.values(fields).join(' ') : '';
            showToast(error.message + detail, true);
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'Submit Request';
        }
    });
})();
