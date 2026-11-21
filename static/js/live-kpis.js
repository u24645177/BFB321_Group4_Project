// Live dashboard KPIs
// refreshDashboardKpis() reloads the KPI cards from GET /api/kpis, so the numbers
// change straight after an action (e.g. a delayed order is delivered) without a reload.

const KPI_STATUS_LABELS = { good: 'On target', warning: 'Needs attention', critical: 'Critical' };

// Update one KPI card on the dashboard from the API's data
function updateKpiCard(kpi) {
    const card = document.querySelector(`[data-kpi="${kpi.key}"]`);
    if (!card) return;

    card.className = 'kpi-card kpi-' + kpi.status;   // colour: good / warning / critical
    card.querySelector('.kpi-value').firstChild.textContent = kpi.display_value;
    card.querySelector('.bar-fill').style.setProperty('--bar-width', kpi.progress_percent + '%');
    card.querySelector('.kpi-status').textContent = KPI_STATUS_LABELS[kpi.status];

    // Rebuild the "↑ 1 vs last month" trend so it matches the new value
    const trend = document.createElement('span');
    if (kpi.trend_direction === 'flat') {
        trend.className = 'kpi-trend';
        trend.textContent = 'No change';
    } else {
        trend.className = 'kpi-trend ' + (kpi.trend_improving ? 'is-improving' : 'is-worsening');
        const arrow = document.createElement('span');
        arrow.setAttribute('aria-hidden', 'true');
        arrow.textContent = kpi.trend_direction === 'up' ? '↑' : '↓';
        const spoken = document.createElement('span');
        spoken.className = 'visually-hidden';
        spoken.textContent = kpi.trend_direction === 'up' ? 'Up' : 'Down';
        trend.append(arrow, spoken, ' ' + kpi.trend_text);
    }
    card.querySelector('.kpi-trend').replaceWith(trend);
}

// ---- Live stock metrics (B3.3) ----

// Build one metric card, styled like the KPI cards below it
function buildMetricCard(metric) {
    const card = document.createElement('li');
    card.className = 'kpi-card kpi-' + metric.status;
    card.dataset.metric = metric.key;

    const name = document.createElement('p');
    name.className = 'kpi-name';
    name.textContent = metric.name;

    const value = document.createElement('p');
    value.className = 'kpi-value';
    value.textContent = metric.display_value;
    const unit = document.createElement('span');
    unit.className = 'kpi-unit';
    unit.textContent = metric.unit;
    value.append(unit);

    const description = document.createElement('p');
    description.className = 'kpi-desc';
    description.textContent = metric.description;

    card.append(name, value, description);
    return card;
}

// Show the metric cards, or a loading / error message in their place
function showMetrics(list, metrics) {
    list.innerHTML = '';
    metrics.forEach((metric) => list.append(buildMetricCard(metric)));
    list.setAttribute('aria-busy', 'false');
}

function showMetricsError(list, message) {
    list.innerHTML = '';
    const item = document.createElement('li');
    item.className = 'metrics-state is-error';
    item.setAttribute('role', 'alert');
    item.textContent = 'Could not load the live metrics: ' + message;
    const retry = document.createElement('button');
    retry.type = 'button';
    retry.className = 'btn btn-sm btn-outline-secondary';
    retry.textContent = 'Retry';
    retry.addEventListener('click', refreshDashboardKpis);
    item.append(retry);
    list.append(item);
    list.setAttribute('aria-busy', 'false');
}

// Reload the live metrics and every KPI card for the category shown on the dashboard
async function refreshDashboardKpis() {
    const metricsList = document.getElementById('live-metrics');
    if (!metricsList) return;   // only on the dashboard

    const category = new URLSearchParams(window.location.search).get('category') || 'all';
    try {
        const result = await apiFetch('/api/kpis?category=' + encodeURIComponent(category));
        showMetrics(metricsList, result.metrics);
        result.data.forEach(updateKpiCard);
    } catch (error) {
        showMetricsError(metricsList, error.message);
    }
}

refreshDashboardKpis();   // load the live metrics as soon as the dashboard opens