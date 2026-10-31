-- KeyProse — Demo Seed Data
-- Run with: sqlite3 listing_pilot.db < backend/data/seed_demo_data.sql

CREATE TABLE IF NOT EXISTS properties (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    address     TEXT NOT NULL,
    city        TEXT,
    state       TEXT DEFAULT 'TX',
    zip         TEXT,
    beds        INTEGER,
    baths       REAL,
    sqft        INTEGER,
    lot_size    TEXT,
    year_built  INTEGER,
    price       REAL,
    status      TEXT DEFAULT 'active',  -- active | pending | sold
    features    TEXT,  -- JSON array
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comps (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id     INTEGER REFERENCES properties(id),
    address         TEXT NOT NULL,
    price           REAL,
    sqft            INTEGER,
    beds            INTEGER,
    baths           REAL,
    sold_date       TEXT,
    distance_miles  REAL
);

CREATE TABLE IF NOT EXISTS contacts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    email       TEXT,
    phone       TEXT,
    type        TEXT DEFAULT 'lead',  -- buyer | seller | investor | past_client | cold_lead
    notes       TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campaigns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT,
    template        TEXT,
    status          TEXT DEFAULT 'draft',
    contacts_count  INTEGER DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── Sample Properties ────────────────────────────────────────────────────────

INSERT INTO properties (address, city, zip, beds, baths, sqft, lot_size, year_built, price, features) VALUES
('123 Maple Street', 'Austin', '78701', 4, 3, 2400, '0.25 acres', 2018, 650000,
 '["open floor plan","chef kitchen","pool","3-car garage","smart home"]'),

('456 Oak Avenue', 'Austin', '78702', 3, 2, 1850, '0.18 acres', 2015, 485000,
 '["updated kitchen","hardwood floors","covered patio","2-car garage"]'),

('789 Pine Drive', 'Austin', '78703', 5, 4, 3200, '0.40 acres', 2020, 895000,
 '["luxury finishes","home office","media room","outdoor kitchen","pool spa"]'),

('321 Cedar Lane', 'Austin', '78704', 2, 1, 1100, '0.10 acres', 1985, 325000,
 '["investment property","updated HVAC","new roof","near UT campus"]'),

('654 Elm Court', 'Austin', '78705', 4, 3.5, 2800, '0.30 acres', 2019, 750000,
 '["corner lot","gourmet kitchen","primary suite","3-car garage","solar panels"]');

-- ─── Sample Comps ─────────────────────────────────────────────────────────────

INSERT INTO comps (property_id, address, price, sqft, beds, baths, sold_date, distance_miles) VALUES
(1, '100 Maple St, Austin TX', 635000, 2350, 4, 3, '2025-05-15', 0.2),
(1, '200 Oak Ave, Austin TX', 660000, 2450, 4, 3, '2025-04-28', 0.4),
(1, '300 Pine Dr, Austin TX', 645000, 2380, 4, 2.5, '2025-06-01', 0.6),

(2, '400 Oak Ave, Austin TX', 475000, 1800, 3, 2, '2025-05-20', 0.3),
(2, '500 Elm St, Austin TX', 495000, 1900, 3, 2, '2025-04-15', 0.5),

(3, '600 Pine Dr, Austin TX', 880000, 3100, 5, 4, '2025-06-10', 0.3),
(3, '700 Cedar Ln, Austin TX', 910000, 3300, 5, 4, '2025-05-05', 0.7);

-- ─── Sample Contacts ──────────────────────────────────────────────────────────

INSERT INTO contacts (name, email, phone, type, notes) VALUES
('John Smith', 'john.smith@email.com', '512-555-0101', 'buyer', 'Looking for 3-4 bed in 78701-78705, budget $500-700k'),
('Sarah Johnson', 'sarah.j@email.com', '512-555-0102', 'seller', 'Thinking about selling in 6 months, owns 456 Oak Ave'),
('Mike Chen', 'mchen@invest.com', '512-555-0103', 'investor', 'Wants 6%+ cap rate, prefers multi-family or SFR near UT'),
('Emily Davis', 'emily.d@email.com', '512-555-0104', 'past_client', 'Bought 123 Maple in 2022, may refer friends'),
('Robert Wilson', 'rwilson@corp.com', '512-555-0105', 'cold_lead', 'Downloaded market report, no response yet'),
('Lisa Martinez', 'lmartinez@email.com', '512-555-0106', 'buyer', 'First-time buyer, pre-approved $425k, wants South Austin'),
('David Brown', 'dbrown@email.com', '512-555-0107', 'seller', 'Relocating to Dallas, needs to sell by September'),
('Jennifer Lee', 'jlee@realty.com', '512-555-0108', 'investor', 'Portfolio of 8 SFRs, looking to add 2-3 more this year');

-- ─── Sample Campaigns ─────────────────────────────────────────────────────────

INSERT INTO campaigns (name, template, status, contacts_count) VALUES
('July New Listings Blast', 'new_listing', 'active', 45),
('Price Reduction — 456 Oak Ave', 'price_drop', 'draft', 12),
('Open House — 789 Pine Drive', 'open_house', 'scheduled', 28),
('Q3 Investor Outreach', 'follow_up', 'active', 15);
