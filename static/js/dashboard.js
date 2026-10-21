(() => {
        const form = document.getElementById('order-form');
        if (!form) return;

        // Clear empties every field, including values re-filled after a server-side error
        document.getElementById('order-clear').addEventListener('click', () => {
            form.reset();
            form.querySelectorAll('input, select, textarea').forEach((el) => {
                el.value = '';
                el.removeAttribute('aria-invalid');
            });
            form.querySelectorAll('.field-error, .form-summary').forEach((el) => el.remove());
            document.getElementById('order-medicine').focus();
        });

        // After a rejected submission, take the user straight to the first problem
        const firstInvalid = form.querySelector('[aria-invalid="true"]');
        if (firstInvalid) firstInvalid.focus();
    })();

    // Set KPI bar widths from data attributes
    document.querySelectorAll('.bar-fill').forEach(bar => {
    const percent = bar.dataset.percent || 0;
    bar.style.setProperty('--bar-width', percent + '%');
    });