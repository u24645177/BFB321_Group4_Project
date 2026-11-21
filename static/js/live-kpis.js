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

// Reload every KPI card for the category currently shown on the dashboard
async function refreshDashboardKpis() {
    if (!document.querySelector('[data-kpi]')) return;   // only on the dashboard

    const category = new URLSearchParams(window.location.search).get('category') || 'all';
    try {
        const result = await apiFetch('/api/kpis?category=' + encodeURIComponent(category));
        result.data.forEach(updateKpiCard);
    } catch (error) {
        notify('Could not refresh the KPIs: ' + error.message, 'error');
    }
}
