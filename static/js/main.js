// MedSync shared front-end behaviour

// 1. Bootstrap client-side validation for every form with class "needs-validation"
document.querySelectorAll('form.needs-validation').forEach(function (form) {
    form.addEventListener('submit', function (event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
            // Move focus to the first invalid field so keyboard users find the error
            const firstInvalid = form.querySelector(':invalid');
            if (firstInvalid) firstInvalid.focus();
        }
        form.classList.add('was-validated');
    });
});

// 2. Sortable columns for tables with class "sortable-table"
document.querySelectorAll('table.sortable-table').forEach(function (table) {
    const headers = table.querySelectorAll('th.sortable');

    headers.forEach(function (th) {
        th.querySelector('.sort-btn').addEventListener('click', function () {
            const index = Array.from(th.parentNode.children).indexOf(th);
            const type = th.dataset.sortType;
            const ascending = th.getAttribute('aria-sort') !== 'ascending';
            const tbody = table.tBodies[0];
            const rows = Array.from(tbody.rows);

            rows.sort(function (a, b) {
                let x = a.cells[index].textContent.trim();
                let y = b.cells[index].textContent.trim();
                if (type === 'number') { x = parseFloat(x); y = parseFloat(y); }
                if (type === 'date') { x = Date.parse(x); y = Date.parse(y); }
                const result = (type === 'text') ? x.localeCompare(y) : x - y;
                return ascending ? result : -result;
            });
            rows.forEach(function (row) { tbody.appendChild(row); });

            // Update the sort state shown to screen readers and sighted users
            headers.forEach(function (h) {
                h.setAttribute('aria-sort', 'none');
                h.querySelector('.sort-icon').textContent = '↕';
            });
            th.setAttribute('aria-sort', ascending ? 'ascending' : 'descending');
            th.querySelector('.sort-icon').textContent = ascending ? '▲' : '▼';
        });
    });
});

const categorySelect = document.querySelector('#category-select');

categorySelect.addEventListener('change', () => {
    document.querySelector('#search-form').submit();
});
