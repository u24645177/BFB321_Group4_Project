// KPI charts (Chart.js)
// Draws three charts on the KPI page from live API data, so they always match the app:
//   Figure 1: current stock vs reorder point  - GET /api/medicines
//   Figure 2: deliveries by status            - GET /api/deliveries
//   Figure 3: before/after KPIs + Table 1     - GET /api/kpis


// Fill the progress bars on the KPI cards (width comes from data-progress in kpis.html)
document.querySelectorAll('.kpi-bar span[data-progress]').forEach(bar => {
  bar.style.width = bar.dataset.progress + '%';
});


(() => {
    const stockCanvas = document.getElementById('stock-chart');
    if (!stockCanvas) return;   // only runs on the KPI page

    const deliveryCanvas = document.getElementById('delivery-chart');
    const improvementCanvas = document.getElementById('improvement-chart');
    const beforeAfterBody = document.getElementById('before-after-body');

        const COLOURS = {
        good: '#8cc76a', warning: '#e0a243', critical: '#e07a5f',
        track: '#e2e8f0', neutral: '#94a3b8', grid: '#eef2f6', text: '#64748b', title: '#1e293b',
    };


    // Grey for normal statuses; colour only where it matters
    const DELIVERY_COLOURS = {
        Scheduled: COLOURS.neutral, 'In Transit': COLOURS.neutral, Delayed: COLOURS.critical,
        Delivered: COLOURS.good, Failed: COLOURS.critical,
    };

    // Look and feel for every chart
    if (typeof Chart !== 'undefined') {
        Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = COLOURS.text;
        Chart.defaults.layout.padding = { top: 8, right: 16 };
        Chart.defaults.plugins.legend.position = 'bottom';
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.padding = 16;
        Chart.defaults.plugins.tooltip.backgroundColor = '#1f2937';
        Chart.defaults.plugins.tooltip.padding = 10;
        Chart.defaults.plugins.tooltip.cornerRadius = 8;
        Chart.defaults.plugins.tooltip.boxPadding = 4;
    }
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
            title: { display: Boolean(title), text: title, color: COLOURS.title, font: { weight: '600' } },
            grid: { color: COLOURS.grid },
            border: { display: false },
            ticks: { color: COLOURS.text, padding: 6 },
            ...extra,
        };
    }
    const BAR = { borderRadius: 4, maxBarThickness: 28, barPercentage: 0.7 };

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
                        // Coloured bar: current stock, drawn on top of the grey track
                        type: 'bar', label: 'Current stock', order: 1, grouped: false, ...BAR,
                        data: medicines.map((m) => m.current_stock),
                        backgroundColor: medicines.map((m) => STOCK_COLOURS[m.status]),
                    },
                    {
                        // Grey track behind each bar: the reorder point to fill up to
                        type: 'bar', label: 'Reorder point', order: 2, grouped: false, ...BAR,
                        data: medicines.map((m) => m.reorder_point),
                        backgroundColor: COLOURS.track,
                    },
                ],
            },
            options: {
                indexAxis: 'y',
                maintainAspectRatio: false,
                interaction: { mode: 'index', axis: 'y', intersect: false },
                scales: {
                    x: axis('Units in stock', { beginAtZero: true }),
                    y: axis('', { grid: { display: false }, ticks: { color: COLOURS.text, autoSkip: false } }),
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
                                { text: 'Reorder point', fillStyle: COLOURS.track, strokeStyle: COLOURS.track, pointStyle: 'rect' },
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
                                datasets: [{
                    label: 'Deliveries', data: counts, ...BAR, maxBarThickness: 44,
                    backgroundColor: DELIVERY_STATUSES.map((status) => DELIVERY_COLOURS[status]),
                }],
            },
            options: {
                maintainAspectRatio: false,
                scales: {
                    x: axis('', { grid: { display: false }, ticks: { color: COLOURS.text, maxRotation: 0 } }),
                    y: axis('Deliveries', {
                        beginAtZero: true,
                        suggestedMax: Math.max(...counts) + 1,   // a little headroom above the tallest bar
                        ticks: { precision: 0, color: COLOURS.text },
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
            // Show the change as a coloured pill
            const pill = document.createElement('span');
            pill.className = 'change-pill ' + (change > 0 ? 'is-better' : change < 0 ? 'is-worse' : 'is-same');
            pill.textContent = row.cells[4].textContent;
            row.cells[4].replaceChildren(pill);
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

