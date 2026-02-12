// InvestorLens Neo4j Schema
// Run this before loading data to set up constraints and indexes.

// ===== Constraints (ensure uniqueness) =====
CREATE CONSTRAINT company_id IF NOT EXISTS
FOR (c:Company) REQUIRE c.company_id IS UNIQUE;

CREATE CONSTRAINT segment_name IF NOT EXISTS
FOR (s:Segment) REQUIRE s.name IS UNIQUE;

CREATE CONSTRAINT theme_name IF NOT EXISTS
FOR (t:InvestmentTheme) REQUIRE t.name IS UNIQUE;

// ===== Indexes (speed up lookups) =====
CREATE INDEX company_ticker IF NOT EXISTS
FOR (c:Company) ON (c.ticker);

CREATE INDEX company_sector IF NOT EXISTS
FOR (c:Company) ON (c.sector);

CREATE INDEX company_status IF NOT EXISTS
FOR (c:Company) ON (c.status);
