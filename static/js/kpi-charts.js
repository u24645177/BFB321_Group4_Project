// KPI charts (Chart.js)
// Draws three charts on the KPI page from live API data, so they always match the app:
//   Figure 1: current stock vs reorder point  - GET /api/medicines
//   Figure 2: deliveries by status            - GET /api/deliveries
//   Figure 3: before/after KPIs + Table 1     - GET /api/kpis

(() => {
    const stockCanvas = document.getElementById('stock-chart');
    if (!stockCanvas) return;   // only runs on the KPI page

    const deliveryCanvas = document.getElementById('delivery-chart');
    const improvementCanvas = document.getElementById('improvement-chart');
    const beforeAfterBody = document.getElementById('before-after-body');

    // Status colours (checked for colour-blind separation); every colour also has a label
    const COLOURS = {
        good: '#2e7d32', warning: '#d98200', critical: '#c62828',
        marker: '#3d3d3a', neutral: '#5a7184', grid: '#e6e6e3', text: '#666666',
    };
    const STOCK_COLOURS = { Sufficient: COLOURS.good, Low: COLOURS.warning, Critical: COLOURS.critical };
    const DELIVERY_STATUSES = ['Scheduled', 'In Transit', 'Delayed', 'Delivered', 'Failed'];

    // Show a loading / empty / error message over a chart, or hide it ('' = show the chart)
    function chartMessage(canvas, text, isError) {
        const box = canvas.parentElement;
        let note = box.querySelector('.chart-state');
        if (!note) {
            note = document.createElement('p');
            note.className = 'chart-state';
            note.setAttribute('role', 'status');
            box.append(note);
        }
        note.textContent = text;
        note.classList.toggle('is-error', Boolean(isError));
        note.hidden = !text;
        canvas.hidden = Boolean(text);
    }

    // Settings shared by every chart: quiet grid, thin bars, rounded ends
    function axis(title, extra) {
        return {
            title: { display: Boolean(title), text: title, color: COLOURS.text },
            grid: { color: COLOURS.grid },
            ticks: { color: COLOURS.text },
            ...extra,
        };
    }
    const BAR = { borderRadius: 4, maxBarThickness: 36 };

    // Figure 1: stock vs reorder point
    async function drawStockChart() {
        chartMessage(stockCanvas, 'Loading chart…');
        const result = await apiFetch('/api/medicines?size=100');
        const medicines = result.data;
        if (medicines.length === 0) {
            chartMessage(stockCanvas, 'No medicines yet.');
            return;
        }
        chartMessage(stockCanvas, '');

        new Chart(stockCanvas, {
            data: {
                labels: medicines.map((m) => m.name),
                datasets: [
                    {
                        type: 'bar', label: 'Current stock', order: 2, ...BAR,
                        data: medicines.map((m) => m.current_stock),
                        backgroundColor: medicines.map((m) => STOCK_COLOURS[m.status]),
                    },
                    {
                        // Markers only: each reorder point belongs to one medicine, so no joining line
                        type: 'line', label: 'Reorder point', order: 1, showLine: false,
                        data: medicines.map((m) => m.reorder_point),
                        pointStyle: 'rectRot', pointRadius: 6, pointHoverRadius: 8,
                        backgroundColor: COLOURS.marker, borderColor: '#ffffff', borderWidth: 2,
                    },
                ],
            },
            options: {
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: {
                    x: axis('', { grid: { display: false } }),
                    y: axis('Units', { beginAtZero: true }),
                },
                plugins: {
                    // Legend explains the bar colours (status) and the ◆ marker
                    legend: {
                        labels: {
                            usePointStyle: true,
                            generateLabels: () => [
                                ...Object.entries(STOCK_COLOURS).map(([status, colour]) => ({
                                    text: status, fillStyle: colour, strokeStyle: colour, pointStyle: 'rect',
                                })),
                                { text: 'Reorder point', fillStyle: COLOURS.marker, strokeStyle: COLOURS.marker, pointStyle: 'rectRot' },
                            ],
                        },
                        onClick: () => {},   // the legend explains colours; it does not hide data
                    },
                    tooltip: {
                        callbacks: {
                            afterBody: (items) => 'Status: ' + medicines[items[0].dataIndex].status,
                        },
                    },
                },
            },
        });
    }

    // Figure 2: deliveries by status
    async function drawDeliveryChart() {
        chartMessage(deliveryCanvas, 'Loading chart…');
        const result = await apiFetch('/api/deliveries');
        if (result.data.length === 0) {
            chartMessage(deliveryCanvas, 'No deliveries yet.');
            return;
        }
        chartMessage(deliveryCanvas, '');

        const counts = DELIVERY_STATUSES.map((status) => result.data.filter((d) => d.status === status).length);
        new Chart(deliveryCanvas, {
            type: 'bar',
            data: {
                labels: DELIVERY_STATUSES,
                datasets: [{ label: 'Deliveries', data: counts, backgroundColor: COLOURS.neutral, ...BAR }],
            },
            options: {
                maintainAspectRatio: false,
                scales: {
                    x: axis('', { grid: { display: false } }),
                    y: axis('Deliveries', {
                        beginAtZero: true,
                        suggestedMax: Math.max(...counts) + 1,   // a little headroom above the tallest bar
                        ticks: { stepSize: 1, color: COLOURS.text },
                    }),
                },
                plugins: { legend: { display: false } },   // one series: the title names it
            },
        });
    }

    // Figure 3 and Table 1: each KPI against last month's baseline
    function fillBeforeAfterTable(kpis) {
        clearTableState(beforeAfterBody);
        kpis.forEach((kpi) => {
            const row = beforeAfterBody.insertRow();
            const change = kpi.improvement_percent;
            const cells = [
                kpi.name,
                `${kpi.previous} ${kpi.unit}`,
                `${kpi.display_value} ${kpi.unit}`,
                `${kpi.target} ${kpi.unit}`,
                (change > 0 ? '▲ ' : change < 0 ? '▼ ' : '') + Math.abs(change) + '% ' +
                    (change > 0 ? 'better' : change < 0 ? 'worse' : 'no change'),
            ];
            cells.forEach((text, index) => {
                const cell = row.insertCell();
                cell.textContent = text;
                if (index > 0) cell.className = 'text-end';
            });
            row.cells[4].style.color = change > 0 ? COLOURS.good : change < 0 ? COLOURS.critical : COLOURS.text;
        });
    }

    async function drawImprovementChart() {
        chartMessage(improvementCanvas, 'Loading chart…');
        const result = await apiFetch('/api/kpis');
        const kpis = result.data;
        if (kpis.length === 0) {
            chartMessage(improvementCanvas, 'No KPIs yet.');
            showTableState(beforeAfterBody, 'empty', 'No KPIs yet.');
            return;
        }
        chartMessage(improvementCanvas, '');
        fillBeforeAfterTable(kpis);

        const changes = kpis.map((k) => k.improvement_percent);
        new Chart(improvementCanvas, {
            type: 'bar',
            data: {
                labels: kpis.map((k) => k.name),
                datasets: [{
                    label: 'Change vs baseline', ...BAR,
                    data: changes,
                    backgroundColor: changes.map((c) => (c >= 0 ? COLOURS.good : COLOURS.critical)),
                }],
            },
            options: {
                indexAxis: 'y',   // horizontal bars so the long KPI names fit
                maintainAspectRatio: false,
                scales: {
                    x: axis('% better than last month (negative = worse)', {
                        ticks: { color: COLOURS.text, callback: (value) => value + '%' },
                    }),
                    y: axis('', { grid: { display: false } }),
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (item) => {
                                const kpi = kpis[item.dataIndex];
                                return `${kpi.previous} → ${kpi.display_value} ${kpi.unit} (${item.raw > 0 ? '+' : ''}${item.raw}%)`;
                            },
                        },
                    },
                },
            },
        });
    }

    // Draw each chart on its own, so one failing does not stop the others
    function draw(drawChart, canvas, onError) {
        drawChart().catch((error) => {
            chartMessage(canvas, 'Could not load this chart: ' + error.message, true);
            if (onError) onError(error);
        });
    }

    if (typeof Chart === 'undefined') {
        // Chart.js comes from the internet; without it, say so instead of showing empty boxes
        [stockCanvas, deliveryCanvas, improvementCanvas].forEach((canvas) =>
            chartMessage(canvas, 'Charts need an internet connection to load Chart.js.', true));
        return;
    }

    draw(drawStockChart, stockCanvas);
    draw(drawDeliveryChart, deliveryCanvas);
    draw(drawImprovementChart, improvementCanvas, (error) =>
        showTableState(beforeAfterBody, 'error', 'Could not load KPIs: ' + error.message, () => location.reload()));
})();

