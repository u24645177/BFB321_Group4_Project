"""
Unit tests for input validation and stock rules (B2.4, B2.5, B7).

These tests need no running database: the two functions that look things up
in MySQL (find_medicine and get_supplier_names) are replaced with fakes, so
only the validation rules themselves are tested.

Run from the PROJECT ROOT with:
    python -m pytest tests/
"""

from datetime import date, timedelta

import pytest

from data import dashboard, deliveries


# ---------------------------------------------------------------------------
# validate_medicine  (POST /api/medicines)
# ---------------------------------------------------------------------------

def valid_medicine(**changes):
    """A complete, valid new-medicine payload; pass keyword arguments to break one field."""
    payload = {
        'name': 'Aspirin 300mg',
        'category': 'analgesics',
        'current_stock': 120,
        'avg_daily_demand': 8,
        'demand_std_dev': 2,
        'lead_time_days': 7,
    }
    payload.update(changes)
    return payload


class TestValidateMedicine:
    def test_valid_medicine_has_no_errors(self):
        medicine, errors = dashboard.validate_medicine(valid_medicine())
        assert errors == {}
        assert medicine['name'] == 'Aspirin 300mg'
        assert medicine['current_stock'] == 120

    def test_costs_default_when_left_out(self):
        medicine, _ = dashboard.validate_medicine(valid_medicine())
        assert medicine['unit_cost'] == dashboard.DEFAULT_UNIT_COST
        assert medicine['order_cost'] == dashboard.DEFAULT_ORDER_COST

    def test_costs_are_rounded_to_cents(self):
        medicine, errors = dashboard.validate_medicine(valid_medicine(unit_cost='12.3456', order_cost=300))
        assert errors == {}
        assert medicine['unit_cost'] == 12.35
        assert medicine['order_cost'] == 300

    def test_category_is_case_insensitive_and_stored_lowercase(self):
        medicine, errors = dashboard.validate_medicine(valid_medicine(category='  Antibiotics '))
        assert errors == {}
        assert medicine['category'] == 'antibiotics'

    def test_name_is_trimmed(self):
        medicine, _ = dashboard.validate_medicine(valid_medicine(name='  Aspirin 300mg  '))
        assert medicine['name'] == 'Aspirin 300mg'

    def test_missing_name_is_rejected(self):
        medicine, errors = dashboard.validate_medicine(valid_medicine(name='   '))
        assert medicine is None
        assert 'name' in errors

    def test_name_longer_than_limit_is_rejected(self):
        _, errors = dashboard.validate_medicine(valid_medicine(name='x' * (dashboard.MAX_NAME_LENGTH + 1)))
        assert 'name' in errors

    def test_unknown_category_is_rejected(self):
        _, errors = dashboard.validate_medicine(valid_medicine(category='sweets'))
        assert 'category' in errors

    @pytest.mark.parametrize('field, bad_value', [
        ('current_stock', -1),             # below minimum
        ('current_stock', 10.5),           # must be a whole number
        ('current_stock', 'lots'),         # not a number
        ('avg_daily_demand', -0.1),
        ('demand_std_dev', -2),
        ('lead_time_days', 0),             # at least 1 day
        ('lead_time_days', 3.5),
        ('lead_time_days', float('nan')),  # not a finite number
        ('lead_time_days', float('inf')),
        ('unit_cost', 0),                  # a cost, if sent, must be positive
        ('order_cost', -50),
    ])
    def test_bad_numbers_are_rejected_with_a_message_on_that_field(self, field, bad_value):
        medicine, errors = dashboard.validate_medicine(valid_medicine(**{field: bad_value}))
        assert medicine is None
        assert field in errors
        assert errors[field]            # a readable message, not empty

    def test_missing_required_numbers_are_rejected(self):
        _, errors = dashboard.validate_medicine({'name': 'X', 'category': 'vaccines'})
        for field in ('current_stock', 'avg_daily_demand', 'demand_std_dev', 'lead_time_days'):
            assert field in errors

    def test_every_error_is_reported_at_once(self):
        _, errors = dashboard.validate_medicine({})
        assert len(errors) >= 6


# ---------------------------------------------------------------------------
# validate_medicine_update  (PATCH /api/medicines/<id>)
# ---------------------------------------------------------------------------

class TestValidateMedicineUpdate:
    def test_single_field_update_is_accepted(self):
        changes, errors = dashboard.validate_medicine_update({'current_stock': 250})
        assert errors == {}
        assert changes == {'current_stock': 250}

    def test_only_the_fields_sent_are_returned(self):
        changes, _ = dashboard.validate_medicine_update({'lead_time_days': 10, 'unit_cost': '4.5'})
        assert set(changes) == {'lead_time_days', 'unit_cost'}
        assert changes['unit_cost'] == 4.5

    def test_empty_update_is_rejected(self):
        changes, errors = dashboard.validate_medicine_update({})
        assert changes is None
        assert 'fields' in errors

    def test_unknown_field_is_rejected(self):
        _, errors = dashboard.validate_medicine_update({'name': 'Renamed'})
        assert 'fields' in errors

    def test_out_of_range_value_is_rejected(self):
        _, errors = dashboard.validate_medicine_update({'current_stock': -5})
        assert 'current_stock' in errors

    def test_fractional_lead_time_is_rejected(self):
        _, errors = dashboard.validate_medicine_update({'lead_time_days': 2.5})
        assert 'lead_time_days' in errors


# ---------------------------------------------------------------------------
# stock_status  (the Critical / Low / Sufficient rule)
# ---------------------------------------------------------------------------

class TestStockStatus:
    def test_below_safety_stock_is_critical(self):
        assert dashboard.stock_status(stock=10, safety_stock=20, reorder_point=80) == 'Critical'

    def test_exactly_at_safety_stock_is_low_not_critical(self):
        assert dashboard.stock_status(stock=20, safety_stock=20, reorder_point=80) == 'Low'

    def test_exactly_at_reorder_point_is_low(self):
        assert dashboard.stock_status(stock=80, safety_stock=20, reorder_point=80) == 'Low'

    def test_above_reorder_point_is_sufficient(self):
        assert dashboard.stock_status(stock=81, safety_stock=20, reorder_point=80) == 'Sufficient'

    def test_empty_shelf_is_critical(self):
        assert dashboard.stock_status(stock=0, safety_stock=5, reorder_point=40) == 'Critical'


# ---------------------------------------------------------------------------
# validate_order  (POST /api/requests); database look-ups are faked
# ---------------------------------------------------------------------------

TODAY = date(2026, 11, 22)


@pytest.fixture
def fake_lookups(monkeypatch):
    """Pretend 'Paracetamol 500mg' and the supplier 'MediSupply SA' exist in the database."""
    monkeypatch.setattr(dashboard, 'find_medicine',
                        lambda name: {'name': name} if name == 'Paracetamol 500mg' else None)
    monkeypatch.setattr(dashboard, 'get_supplier_names', lambda: ['MediSupply SA'])


def valid_order(**changes):
    form = {
        'medicine': 'Paracetamol 500mg',
        'quantity': '418',
        'supplier': 'MediSupply SA',
        'expected_delivery': (TODAY + timedelta(days=7)).isoformat(),
        'notes': 'Urgent for ward 4',
    }
    form.update(changes)
    return form


class TestValidateOrder:
    def test_valid_order_has_no_errors(self, fake_lookups):
        order, errors = dashboard.validate_order(valid_order(), today=TODAY)
        assert errors == {}
        assert order['quantity'] == 418
        assert order['expected_delivery'] == TODAY + timedelta(days=7)

    def test_unknown_medicine_is_rejected(self, fake_lookups):
        _, errors = dashboard.validate_order(valid_order(medicine='Magic Pills'), today=TODAY)
        assert 'medicine' in errors

    @pytest.mark.parametrize('quantity', ['0', '-5', 'ten', '', '2.5', str(dashboard.MAX_ORDER_QUANTITY + 1)])
    def test_bad_quantity_is_rejected(self, fake_lookups, quantity):
        _, errors = dashboard.validate_order(valid_order(quantity=quantity), today=TODAY)
        assert 'quantity' in errors

    def test_largest_allowed_quantity_is_accepted(self, fake_lookups):
        _, errors = dashboard.validate_order(valid_order(quantity=str(dashboard.MAX_ORDER_QUANTITY)), today=TODAY)
        assert 'quantity' not in errors

    def test_unknown_supplier_is_rejected(self, fake_lookups):
        _, errors = dashboard.validate_order(valid_order(supplier='Fly By Night Ltd'), today=TODAY)
        assert 'supplier' in errors

    def test_delivery_date_in_the_past_is_rejected(self, fake_lookups):
        yesterday = (TODAY - timedelta(days=1)).isoformat()
        _, errors = dashboard.validate_order(valid_order(expected_delivery=yesterday), today=TODAY)
        assert 'expected_delivery' in errors

    def test_delivery_today_is_accepted(self, fake_lookups):
        _, errors = dashboard.validate_order(valid_order(expected_delivery=TODAY.isoformat()), today=TODAY)
        assert 'expected_delivery' not in errors

    def test_missing_or_malformed_date_is_rejected(self, fake_lookups):
        for bad in ('', 'next week', '2026-13-45'):
            _, errors = dashboard.validate_order(valid_order(expected_delivery=bad), today=TODAY)
            assert 'expected_delivery' in errors

    def test_notes_over_the_limit_are_rejected(self, fake_lookups):
        long_notes = 'x' * (dashboard.MAX_NOTES_LENGTH + 1)
        _, errors = dashboard.validate_order(valid_order(notes=long_notes), today=TODAY)
        assert 'notes' in errors


# ---------------------------------------------------------------------------
# validate_delivery_update  (PATCH /api/deliveries/<id>)
# ---------------------------------------------------------------------------

class TestValidateDeliveryUpdate:
    def test_simple_status_change_is_accepted(self):
        changes, errors = deliveries.validate_delivery_update({'status': 'In Transit'})
        assert errors == {}
        assert changes == {'status': 'In Transit', 'exception': ''}

    def test_unknown_status_is_rejected(self):
        changes, errors = deliveries.validate_delivery_update({'status': 'Teleported'})
        assert changes is None
        assert 'status' in errors

    def test_missing_status_is_rejected(self):
        _, errors = deliveries.validate_delivery_update({})
        assert 'status' in errors

    @pytest.mark.parametrize('status', deliveries.PROBLEM_STATUSES)
    def test_problem_status_needs_an_explanation(self, status):
        _, errors = deliveries.validate_delivery_update({'status': status})
        assert 'exception' in errors

    def test_problem_status_with_explanation_is_accepted(self):
        changes, errors = deliveries.validate_delivery_update(
            {'status': 'Delayed', 'exception': 'Vehicle breakdown on N4'})
        assert errors == {}
        assert changes['exception'] == 'Vehicle breakdown on N4'

    def test_too_short_explanation_is_rejected(self):
        _, errors = deliveries.validate_delivery_update({'status': 'Failed', 'exception': 'bad'})
        assert 'exception' in errors

    def test_explanation_over_the_database_limit_is_rejected(self):
        too_long = 'x' * (deliveries.MAX_EXCEPTION_LENGTH + 1)
        _, errors = deliveries.validate_delivery_update({'status': 'Delivered', 'exception': too_long})
        assert 'exception' in errors

    def test_delivered_does_not_need_an_explanation(self):
        _, errors = deliveries.validate_delivery_update({'status': 'Delivered'})
        assert errors == {}
