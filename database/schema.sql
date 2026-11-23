-- =============================================================================
-- MedSync database schema (MySQL 8.0.16+)
--
-- Run:  mysql -u root -p < database/schema.sql
--
-- Design notes
--   * 3NF: every non-key column depends only on its table's primary key.
--     Medicine, facility and supplier details are stored once and referenced
--     by foreign key everywhere else.
--   * orders.unit_cost is deliberately copied from medicines at order time:
--     it records the price actually paid, which must not change when the
--     catalogue price changes later.
--   * Money uses DECIMAL (never FLOAT) so rand values are exact.
--   * Every table has created_at / updated_at audit fields.
-- =============================================================================

CREATE DATABASE IF NOT EXISTS medsync
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE medsync;

-- Drop in reverse dependency order so the script can be re-run
DROP TABLE IF EXISTS stock_counts;
DROP TABLE IF EXISTS stockout_events;
DROP TABLE IF EXISTS deliveries;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS medicines;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS facilities;

-- -----------------------------------------------------------------------------
-- Facilities: hospitals and clinics that hold stock
-- -----------------------------------------------------------------------------
CREATE TABLE facilities (
    facility_id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(120) NOT NULL,
    district      VARCHAR(80)  NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_facilities_name UNIQUE (name)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- Users: staff who sign in. Facility staff belong to one facility;
-- depot-level procurement officers and admins have facility_id NULL.
-- Passwords are stored only as Werkzeug hashes, never in plain text.
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    user_id       INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(120) NOT NULL,
    email         VARCHAR(160) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('admin', 'procurement_officer', 'pharmacist') NOT NULL,
    facility_id   INT UNSIGNED NULL,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT fk_users_facility FOREIGN KEY (facility_id)
        REFERENCES facilities (facility_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- Suppliers: pharmaceutical wholesalers and distributors
-- -----------------------------------------------------------------------------
CREATE TABLE suppliers (
    supplier_id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(120) NOT NULL,
    contact_email VARCHAR(160) NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_suppliers_name UNIQUE (name)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- Medicines: the catalogue, with the inputs the EOQ model needs
--   annual demand        = avg_daily_demand * 365
--   order cost (S)       = order_cost
--   holding cost (H)     = unit_cost * holding_rate
-- -----------------------------------------------------------------------------
CREATE TABLE medicines (
    medicine_id      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(120)  NOT NULL,
    category         ENUM('analgesics', 'antibiotics', 'antidiabetics',
                          'antiretrovirals', 'respiratory', 'vaccines') NOT NULL,
    unit_cost        DECIMAL(10, 2) NOT NULL,
    order_cost       DECIMAL(10, 2) NOT NULL,
    holding_rate     DECIMAL(5, 4)  NOT NULL DEFAULT 0.2000,
    avg_daily_demand DECIMAL(10, 2) NOT NULL,
    demand_std_dev   DECIMAL(10, 2) NOT NULL,
    lead_time_days   SMALLINT UNSIGNED NOT NULL,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_medicines_name    UNIQUE (name),
    CONSTRAINT ck_medicines_cost    CHECK (unit_cost > 0 AND order_cost > 0),
    CONSTRAINT ck_medicines_rate    CHECK (holding_rate > 0 AND holding_rate <= 1),
    CONSTRAINT ck_medicines_demand  CHECK (avg_daily_demand >= 0 AND demand_std_dev >= 0),
    CONSTRAINT ck_medicines_lead    CHECK (lead_time_days > 0)
) ENGINE=InnoDB;

CREATE INDEX ix_medicines_category ON medicines (category);

-- -----------------------------------------------------------------------------
-- Inventory: stock on hand of one medicine at one facility
-- -----------------------------------------------------------------------------
CREATE TABLE inventory (
    inventory_id     INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    medicine_id      INT UNSIGNED NOT NULL,
    facility_id      INT UNSIGNED NOT NULL,
    quantity_on_hand INT UNSIGNED NOT NULL DEFAULT 0,
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_inventory_medicine_facility UNIQUE (medicine_id, facility_id),
    CONSTRAINT fk_inventory_medicine FOREIGN KEY (medicine_id)
        REFERENCES medicines (medicine_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_inventory_facility FOREIGN KEY (facility_id)
        REFERENCES facilities (facility_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE INDEX ix_inventory_facility ON inventory (facility_id);

-- -----------------------------------------------------------------------------
-- Orders: reorder requests and their progress
--   Awaiting Approval -> Approved -> Ordered -> In Transit -> Delivered
--   (Delayed can occur once the order has been placed; Cancelled before delivery)
-- -----------------------------------------------------------------------------
CREATE TABLE orders (
    order_id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    medicine_id       INT UNSIGNED NOT NULL,
    facility_id       INT UNSIGNED NOT NULL,
    supplier_id       INT UNSIGNED NOT NULL,
    requested_by      INT UNSIGNED NULL,
    quantity          INT UNSIGNED NOT NULL,
    unit_cost         DECIMAL(10, 2) NOT NULL,
    status            ENUM('Awaiting Approval', 'Approved', 'Ordered', 'In Transit',
                           'Delivered', 'Delayed', 'Cancelled')
                      NOT NULL DEFAULT 'Awaiting Approval',
    is_emergency      BOOLEAN NOT NULL DEFAULT FALSE,
    notes             VARCHAR(500) NULL,
    requested_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at       DATETIME NULL,
    expected_delivery DATE NOT NULL,
    delivered_at      DATETIME NULL,
    status_changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT ck_orders_quantity CHECK (quantity BETWEEN 1 AND 100000),
    CONSTRAINT ck_orders_cost     CHECK (unit_cost > 0),
    CONSTRAINT fk_orders_medicine FOREIGN KEY (medicine_id)
        REFERENCES medicines (medicine_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_orders_facility FOREIGN KEY (facility_id)
        REFERENCES facilities (facility_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_orders_supplier FOREIGN KEY (supplier_id)
        REFERENCES suppliers (supplier_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_orders_requested_by FOREIGN KEY (requested_by)
        REFERENCES users (user_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE INDEX ix_orders_medicine_facility ON orders (medicine_id, facility_id);
CREATE INDEX ix_orders_status            ON orders (status);
CREATE INDEX ix_orders_requested_at      ON orders (requested_at);

-- -----------------------------------------------------------------------------
-- Deliveries: the shipment that fulfils an order (one delivery per order)
-- -----------------------------------------------------------------------------
CREATE TABLE deliveries (
    delivery_id    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    reference      VARCHAR(20) NOT NULL,
    order_id       INT UNSIGNED NOT NULL,
    vehicle_reg    VARCHAR(20) NULL,
    eta            DATETIME NOT NULL,
    status         ENUM('Scheduled', 'In Transit', 'Delayed', 'Delivered', 'Failed')
                   NOT NULL DEFAULT 'Scheduled',
    exception_note VARCHAR(255) NULL,
    delivered_at   DATETIME NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_deliveries_reference UNIQUE (reference),
    CONSTRAINT uq_deliveries_order     UNIQUE (order_id),
    CONSTRAINT fk_deliveries_order FOREIGN KEY (order_id)
        REFERENCES orders (order_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE INDEX ix_deliveries_status ON deliveries (status);

-- -----------------------------------------------------------------------------
-- Stockout events: a medicine ran out at a facility (drives the stockout KPI)
-- -----------------------------------------------------------------------------
CREATE TABLE stockout_events (
    stockout_id  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    medicine_id  INT UNSIGNED NOT NULL,
    facility_id  INT UNSIGNED NOT NULL,
    occurred_at  DATETIME NOT NULL,
    resolved_at  DATETIME NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT ck_stockout_resolved CHECK (resolved_at IS NULL OR resolved_at >= occurred_at),
    CONSTRAINT fk_stockout_medicine FOREIGN KEY (medicine_id)
        REFERENCES medicines (medicine_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_stockout_facility FOREIGN KEY (facility_id)
        REFERENCES facilities (facility_id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE INDEX ix_stockout_medicine_facility ON stockout_events (medicine_id, facility_id);
CREATE INDEX ix_stockout_occurred_at       ON stockout_events (occurred_at);

-- -----------------------------------------------------------------------------
-- Stock counts: physical count vs system quantity (drives record accuracy KPI)
-- -----------------------------------------------------------------------------
CREATE TABLE stock_counts (
    count_id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    inventory_id     INT UNSIGNED NOT NULL,
    system_quantity  INT UNSIGNED NOT NULL,
    counted_quantity INT UNSIGNED NOT NULL,
    counted_at       DATETIME NOT NULL,
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_counts_inventory FOREIGN KEY (inventory_id)
        REFERENCES inventory (inventory_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE INDEX ix_counts_counted_at ON stock_counts (counted_at);
