-- =============================================================================
-- MedSync seed data: realistic demo data for every table.
--
-- Run after schema.sql:  mysql -u root -p medsync < database/seed.sql
--
-- Dates are relative to today (DATE_SUB(NOW(), ...)), so the dashboard,
-- alerts and KPIs look current whenever the database is loaded.
--
-- Demo sign-in (all three users): password MedSync2026!
--   admin@medsync.test          admin
--   procurement@medsync.test    procurement officer
--   pharmacist@medsync.test     pharmacist, Steve Biko Academic Hospital
-- Only a Werkzeug password hash is stored below, never the password itself.
-- =============================================================================

USE medsync;

-- Facilities
INSERT INTO facilities (facility_id, name, district) VALUES
    (1, 'Steve Biko Academic Hospital', 'City of Tshwane'),
    (2, 'Kalafong Provincial Tertiary Hospital', 'City of Tshwane'),
    (3, 'Tshwane District Hospital', 'City of Tshwane');

-- Users (password hash for the demo password above)
INSERT INTO users (user_id, full_name, email, password_hash, role, facility_id) VALUES
    (1, 'Thandi Mokoena', 'admin@medsync.test', 'scrypt:32768:8:1$iTK54Bw5IyrAua1G$cc49c6b65aebfbeb1eff13e977852916dd4b29990c279e8bea97cd3f7bbde0078115905253b14f32653b0d777d8472f23e4fe4795285c8d1fa8d702e80025cc2', 'admin', NULL),
    (2, 'Pieter van der Merwe', 'procurement@medsync.test', 'scrypt:32768:8:1$iTK54Bw5IyrAua1G$cc49c6b65aebfbeb1eff13e977852916dd4b29990c279e8bea97cd3f7bbde0078115905253b14f32653b0d777d8472f23e4fe4795285c8d1fa8d702e80025cc2', 'procurement_officer', NULL),
    (3, 'Lerato Nkosi', 'pharmacist@medsync.test', 'scrypt:32768:8:1$iTK54Bw5IyrAua1G$cc49c6b65aebfbeb1eff13e977852916dd4b29990c279e8bea97cd3f7bbde0078115905253b14f32653b0d777d8472f23e4fe4795285c8d1fa8d702e80025cc2', 'pharmacist', '1');

-- Suppliers
INSERT INTO suppliers (supplier_id, name, contact_email) VALUES
    (1, 'MediSupply SA', 'orders@medisupply.co.za'),
    (2, 'PharmaLink Distributors', 'procurement@pharmalink.co.za'),
    (3, 'HealthCore Wholesale', 'sales@healthcore.co.za'),
    (4, 'Afrimed Logistics', 'dispatch@afrimed.co.za');

-- Medicines: unit_cost is per pack in rand; demand is packs per day
INSERT INTO medicines (medicine_id, name, category, unit_cost, order_cost, holding_rate,
                       avg_daily_demand, demand_std_dev, lead_time_days) VALUES
    (1, 'Paracetamol 500mg', 'analgesics', 12.50, 350.00, 0.2000, 12.00, 4.00, 7),
    (2, 'Amoxicillin 250mg', 'antibiotics', 28.90, 400.00, 0.2000, 6.00, 2.00, 10),
    (3, 'Ibuprofen 400mg', 'analgesics', 18.40, 350.00, 0.2000, 10.00, 3.00, 7),
    (4, 'Metformin 500mg', 'antidiabetics', 35.60, 450.00, 0.2000, 8.00, 2.00, 14),
    (5, 'Insulin Glargine 100U/ml', 'antidiabetics', 245.00, 600.00, 0.2500, 3.00, 1.00, 21),
    (6, 'Salbutamol Inhaler', 'respiratory', 48.75, 400.00, 0.2000, 5.00, 2.00, 10),
    (7, 'Tenofovir/Emtricitabine', 'antiretrovirals', 120.00, 500.00, 0.2000, 7.00, 1.50, 14),
    (8, 'Measles-Rubella Vaccine', 'vaccines', 180.00, 550.00, 0.2500, 4.00, 1.50, 21);

-- Inventory: stock on hand of every medicine at every facility
INSERT INTO inventory (inventory_id, medicine_id, facility_id, quantity_on_hand) VALUES
    (1, 1, 1, 95),
    (2, 1, 2, 160),
    (3, 1, 3, 120),
    (4, 2, 1, 140),
    (5, 2, 2, 85),
    (6, 2, 3, 70),
    (7, 3, 1, 9),
    (8, 3, 2, 110),
    (9, 3, 3, 64),
    (10, 4, 1, 260),
    (11, 4, 2, 190),
    (12, 4, 3, 150),
    (13, 5, 1, 6),
    (14, 5, 2, 48),
    (15, 5, 3, 30),
    (16, 6, 1, 58),
    (17, 6, 2, 40),
    (18, 6, 3, 22),
    (19, 7, 1, 210),
    (20, 7, 2, 175),
    (21, 7, 3, 130),
    (22, 8, 1, 70),
    (23, 8, 2, 55),
    (24, 8, 3, 18);

-- Orders: open orders plus delivered history for the KPI calculations
INSERT INTO orders (order_id, medicine_id, facility_id, supplier_id, requested_by, quantity, unit_cost, status,
                    is_emergency, notes, requested_at, approved_at, expected_delivery, delivered_at, status_changed_at) VALUES
    (1, 3, 1, 1, 3, 300, 18.40, 'Awaiting Approval', 1, 'Ibuprofen below safety stock in casualty ward',
     DATE_SUB(DATE(NOW()), INTERVAL 4 DAY) + INTERVAL 8 HOUR, NULL, DATE_ADD(CURDATE(), INTERVAL 10 DAY), NULL, DATE_SUB(DATE(NOW()), INTERVAL 4 DAY) + INTERVAL 11 HOUR),
    (2, 5, 1, 3, 3, 120, 245.00, 'Awaiting Approval', 1, 'Cold chain delivery required',
     DATE_SUB(DATE(NOW()), INTERVAL 1 DAY) + INTERVAL 8 HOUR, NULL, DATE_ADD(CURDATE(), INTERVAL 21 DAY), NULL, DATE_SUB(DATE(NOW()), INTERVAL 1 DAY) + INTERVAL 11 HOUR),
    (3, 1, 1, 2, 3, 500, 12.50, 'Approved', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 3 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 1 DAY) + INTERVAL 11 HOUR, DATE_ADD(CURDATE(), INTERVAL 7 DAY), NULL, DATE_SUB(DATE(NOW()), INTERVAL 1 DAY) + INTERVAL 11 HOUR),
    (4, 6, 2, 1, 2, 80, 48.75, 'Ordered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 6 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 4 DAY) + INTERVAL 11 HOUR, DATE_ADD(CURDATE(), INTERVAL 5 DAY), NULL, DATE_SUB(DATE(NOW()), INTERVAL 3 DAY) + INTERVAL 11 HOUR),
    (5, 4, 3, 4, 2, 400, 35.60, 'In Transit', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 16 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 14 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 2 DAY), NULL, DATE_SUB(DATE(NOW()), INTERVAL 5 DAY) + INTERVAL 11 HOUR),
    (6, 2, 1, 2, 3, 250, 28.90, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 14 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 12 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 3 DAY), DATE_SUB(DATE(NOW()), INTERVAL 2 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 2 DAY) + INTERVAL 11 HOUR),
    (7, 7, 2, 3, 2, 180, 120.00, 'Delayed', 0, 'Supplier stock shortage at national depot',
     DATE_SUB(DATE(NOW()), INTERVAL 20 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 18 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 6 DAY), NULL, DATE_SUB(DATE(NOW()), INTERVAL 6 DAY) + INTERVAL 11 HOUR),
    (8, 2, 3, 4, 2, 100, 28.90, 'Delayed', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 18 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 16 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 1 DAY), NULL, DATE_SUB(DATE(NOW()), INTERVAL 4 DAY) + INTERVAL 11 HOUR),
    (9, 8, 3, 3, 2, 150, 180.00, 'Approved', 1, 'Catch-up immunisation campaign',
     DATE_SUB(DATE(NOW()), INTERVAL 2 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 1 DAY) + INTERVAL 11 HOUR, DATE_ADD(CURDATE(), INTERVAL 14 DAY), NULL, DATE_SUB(DATE(NOW()), INTERVAL 1 DAY) + INTERVAL 11 HOUR),
    (10, 1, 2, 2, 2, 450, 12.50, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 58 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 57 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 48 DAY), DATE_SUB(DATE(NOW()), INTERVAL 49 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 49 DAY) + INTERVAL 11 HOUR),
    (11, 4, 1, 4, 3, 380, 35.60, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 55 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 53 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 38 DAY), DATE_SUB(DATE(NOW()), INTERVAL 39 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 39 DAY) + INTERVAL 11 HOUR),
    (12, 6, 3, 1, 2, 90, 48.75, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 52 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 51 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 40 DAY), DATE_SUB(DATE(NOW()), INTERVAL 41 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 41 DAY) + INTERVAL 11 HOUR),
    (13, 7, 1, 3, 3, 200, 120.00, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 49 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 46 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 31 DAY), DATE_SUB(DATE(NOW()), INTERVAL 29 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 29 DAY) + INTERVAL 11 HOUR),
    (14, 2, 2, 2, 2, 220, 28.90, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 45 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 44 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 34 DAY), DATE_SUB(DATE(NOW()), INTERVAL 35 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 35 DAY) + INTERVAL 11 HOUR),
    (15, 5, 2, 3, 2, 100, 245.00, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 42 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 40 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 18 DAY), DATE_SUB(DATE(NOW()), INTERVAL 16 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 16 DAY) + INTERVAL 11 HOUR),
    (16, 3, 3, 1, 2, 260, 18.40, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 38 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 37 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 30 DAY), DATE_SUB(DATE(NOW()), INTERVAL 31 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 31 DAY) + INTERVAL 11 HOUR),
    (17, 8, 1, 3, 3, 140, 180.00, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 36 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 34 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 13 DAY), DATE_SUB(DATE(NOW()), INTERVAL 14 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 14 DAY) + INTERVAL 11 HOUR),
    (18, 1, 3, 2, 2, 400, 12.50, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 31 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 30 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 23 DAY), DATE_SUB(DATE(NOW()), INTERVAL 23 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 23 DAY) + INTERVAL 11 HOUR),
    (19, 4, 2, 4, 2, 350, 35.60, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 27 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 26 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 12 DAY), DATE_SUB(DATE(NOW()), INTERVAL 13 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 13 DAY) + INTERVAL 11 HOUR),
    (20, 6, 1, 1, 3, 100, 48.75, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 24 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 23 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 13 DAY), DATE_SUB(DATE(NOW()), INTERVAL 14 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 14 DAY) + INTERVAL 11 HOUR),
    (21, 7, 3, 3, 2, 160, 120.00, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 22 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 20 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 6 DAY), DATE_SUB(DATE(NOW()), INTERVAL 6 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 6 DAY) + INTERVAL 11 HOUR),
    (22, 3, 2, 1, 2, 280, 18.40, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 19 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 18 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 11 DAY), DATE_SUB(DATE(NOW()), INTERVAL 12 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 12 DAY) + INTERVAL 11 HOUR),
    (23, 2, 1, 2, 3, 240, 28.90, 'Delivered', 0, NULL,
     DATE_SUB(DATE(NOW()), INTERVAL 17 DAY) + INTERVAL 8 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 16 DAY) + INTERVAL 11 HOUR, DATE_SUB(CURDATE(), INTERVAL 6 DAY), DATE_SUB(DATE(NOW()), INTERVAL 5 DAY) + INTERVAL 14 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 5 DAY) + INTERVAL 11 HOUR),
    (24, 1, 2, 2, 2, 300, 12.50, 'Cancelled', 0, 'Duplicate request',
     DATE_SUB(DATE(NOW()), INTERVAL 26 DAY) + INTERVAL 8 HOUR, NULL, DATE_SUB(CURDATE(), INTERVAL 19 DAY), NULL, DATE_SUB(DATE(NOW()), INTERVAL 25 DAY) + INTERVAL 11 HOUR);

-- Deliveries: one per order that has been placed with a supplier
INSERT INTO deliveries (reference, order_id, vehicle_reg, eta, status, exception_note, delivered_at) VALUES
    ('DEL-1041', 4, 'GP 34-56 GH', DATE_ADD(DATE(NOW()), INTERVAL 5 DAY) + INTERVAL 10 HOUR, 'Scheduled', NULL, NULL),
    ('DEL-1042', 5, 'GP 71-20 JK', DATE_SUB(DATE(NOW()), INTERVAL 2 DAY) + INTERVAL 10 HOUR, 'In Transit', NULL, NULL),
    ('DEL-1043', 6, 'GP 45-09 LM', DATE_SUB(DATE(NOW()), INTERVAL 3 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 2 DAY) + INTERVAL 14 HOUR),
    ('DEL-1044', 7, 'GP 12-34 AB', DATE_ADD(DATE(NOW()), INTERVAL 2 DAY) + INTERVAL 10 HOUR, 'Delayed', 'Supplier stock shortage', NULL),
    ('DEL-1045', 8, 'GP 56-78 CD', DATE_ADD(DATE(NOW()), INTERVAL 2 DAY) + INTERVAL 10 HOUR, 'Delayed', 'Vehicle breakdown on N4', NULL),
    ('DEL-1046', 10, 'GP 90-12 EF', DATE_SUB(DATE(NOW()), INTERVAL 48 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 49 DAY) + INTERVAL 14 HOUR),
    ('DEL-1047', 11, 'GP 34-56 GH', DATE_SUB(DATE(NOW()), INTERVAL 38 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 39 DAY) + INTERVAL 14 HOUR),
    ('DEL-1048', 12, 'GP 71-20 JK', DATE_SUB(DATE(NOW()), INTERVAL 40 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 41 DAY) + INTERVAL 14 HOUR),
    ('DEL-1049', 13, 'GP 45-09 LM', DATE_SUB(DATE(NOW()), INTERVAL 31 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 29 DAY) + INTERVAL 14 HOUR),
    ('DEL-1050', 14, 'GP 12-34 AB', DATE_SUB(DATE(NOW()), INTERVAL 34 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 35 DAY) + INTERVAL 14 HOUR),
    ('DEL-1051', 15, 'GP 56-78 CD', DATE_SUB(DATE(NOW()), INTERVAL 18 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 16 DAY) + INTERVAL 14 HOUR),
    ('DEL-1052', 16, 'GP 90-12 EF', DATE_SUB(DATE(NOW()), INTERVAL 30 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 31 DAY) + INTERVAL 14 HOUR),
    ('DEL-1053', 17, 'GP 34-56 GH', DATE_SUB(DATE(NOW()), INTERVAL 13 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 14 DAY) + INTERVAL 14 HOUR),
    ('DEL-1054', 18, 'GP 71-20 JK', DATE_SUB(DATE(NOW()), INTERVAL 23 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 23 DAY) + INTERVAL 14 HOUR),
    ('DEL-1055', 19, 'GP 45-09 LM', DATE_SUB(DATE(NOW()), INTERVAL 12 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 13 DAY) + INTERVAL 14 HOUR),
    ('DEL-1056', 20, 'GP 12-34 AB', DATE_SUB(DATE(NOW()), INTERVAL 13 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 14 DAY) + INTERVAL 14 HOUR),
    ('DEL-1057', 21, 'GP 56-78 CD', DATE_SUB(DATE(NOW()), INTERVAL 6 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 6 DAY) + INTERVAL 14 HOUR),
    ('DEL-1058', 22, 'GP 90-12 EF', DATE_SUB(DATE(NOW()), INTERVAL 11 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 12 DAY) + INTERVAL 14 HOUR),
    ('DEL-1059', 23, 'GP 34-56 GH', DATE_SUB(DATE(NOW()), INTERVAL 6 DAY) + INTERVAL 10 HOUR, 'Delivered', NULL, DATE_SUB(DATE(NOW()), INTERVAL 5 DAY) + INTERVAL 14 HOUR);

-- Stockout events: 6 in the previous 30 days, 4 in the last 30 days (one still open)
INSERT INTO stockout_events (medicine_id, facility_id, occurred_at, resolved_at) VALUES
    (3, 1, DATE_SUB(DATE(NOW()), INTERVAL 52 DAY) + INTERVAL 7 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 49 DAY) + INTERVAL 15 HOUR),
    (5, 2, DATE_SUB(DATE(NOW()), INTERVAL 50 DAY) + INTERVAL 7 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 46 DAY) + INTERVAL 15 HOUR),
    (1, 3, DATE_SUB(DATE(NOW()), INTERVAL 47 DAY) + INTERVAL 7 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 45 DAY) + INTERVAL 15 HOUR),
    (7, 2, DATE_SUB(DATE(NOW()), INTERVAL 41 DAY) + INTERVAL 7 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 38 DAY) + INTERVAL 15 HOUR),
    (8, 3, DATE_SUB(DATE(NOW()), INTERVAL 37 DAY) + INTERVAL 7 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 33 DAY) + INTERVAL 15 HOUR),
    (5, 1, DATE_SUB(DATE(NOW()), INTERVAL 33 DAY) + INTERVAL 7 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 31 DAY) + INTERVAL 15 HOUR),
    (3, 1, DATE_SUB(DATE(NOW()), INTERVAL 25 DAY) + INTERVAL 7 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 22 DAY) + INTERVAL 15 HOUR),
    (2, 3, DATE_SUB(DATE(NOW()), INTERVAL 17 DAY) + INTERVAL 7 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 15 DAY) + INTERVAL 15 HOUR),
    (5, 1, DATE_SUB(DATE(NOW()), INTERVAL 9 DAY) + INTERVAL 7 HOUR, DATE_SUB(DATE(NOW()), INTERVAL 6 DAY) + INTERVAL 15 HOUR),
    (3, 1, DATE_SUB(DATE(NOW()), INTERVAL 3 DAY) + INTERVAL 7 HOUR, NULL);

-- Stock counts: physical counts compared with the system quantity
INSERT INTO stock_counts (inventory_id, system_quantity, counted_quantity, counted_at) VALUES
    (2, 160, 159, DATE_SUB(DATE(NOW()), INTERVAL 13 DAY) + INTERVAL 16 HOUR),
    (4, 140, 140, DATE_SUB(DATE(NOW()), INTERVAL 12 DAY) + INTERVAL 16 HOUR),
    (6, 70, 67, DATE_SUB(DATE(NOW()), INTERVAL 11 DAY) + INTERVAL 16 HOUR),
    (8, 110, 110, DATE_SUB(DATE(NOW()), INTERVAL 20 DAY) + INTERVAL 16 HOUR),
    (10, 260, 257, DATE_SUB(DATE(NOW()), INTERVAL 14 DAY) + INTERVAL 16 HOUR),
    (12, 150, 151, DATE_SUB(DATE(NOW()), INTERVAL 15 DAY) + INTERVAL 16 HOUR),
    (14, 48, 48, DATE_SUB(DATE(NOW()), INTERVAL 1 DAY) + INTERVAL 16 HOUR),
    (16, 58, 57, DATE_SUB(DATE(NOW()), INTERVAL 14 DAY) + INTERVAL 16 HOUR),
    (18, 22, 22, DATE_SUB(DATE(NOW()), INTERVAL 13 DAY) + INTERVAL 16 HOUR),
    (20, 175, 172, DATE_SUB(DATE(NOW()), INTERVAL 7 DAY) + INTERVAL 16 HOUR),
    (22, 70, 70, DATE_SUB(DATE(NOW()), INTERVAL 8 DAY) + INTERVAL 16 HOUR),
    (24, 18, 18, DATE_SUB(DATE(NOW()), INTERVAL 12 DAY) + INTERVAL 16 HOUR);
