-- =========================
-- 1) RAW CUSTOMERS
-- =========================
CREATE OR REPLACE TABLE `raw.raw_customers` (
  customer_id   STRING NOT NULL,
  created_date  DATE   NOT NULL,
  age_band      STRING NOT NULL,   -- '18-25','26-35','36-45','46-60','60+'
  residency     STRING NOT NULL,   -- 'AD','ES','FR'
  segment       STRING NOT NULL    -- 'mass','affluent'
);

-- =========================
-- 2) RAW MARKETING EVENTS
-- =========================
CREATE OR REPLACE TABLE `raw.raw_marketing_events` (
  event_ts    TIMESTAMP NOT NULL,
  customer_id STRING    NOT NULL,
  campaign_id STRING    NOT NULL,
  source      STRING    NOT NULL,   -- 'google','meta','email','seo','branch_referral'
  channel     STRING    NOT NULL,   -- 'web','app','branch'
  device      STRING    NOT NULL,   -- 'mobile','desktop'
  event_type  STRING    NOT NULL,   -- 'impression','click','lead'
  cost        NUMERIC               -- costo asignado al evento (puede ser 0 o NULL)
)
PARTITION BY DATE(event_ts)
CLUSTER BY campaign_id, channel, event_type;

-- =========================
-- 3) RAW PRODUCT EVENTS
-- =========================
CREATE OR REPLACE TABLE `raw.raw_product_events` (
  event_ts       TIMESTAMP NOT NULL,
  customer_id    STRING    NOT NULL,
  product_family STRING    NOT NULL, -- 'account','card','loan','mortgage'
  event_type     STRING    NOT NULL, -- 'opened','applied','approved','activated'
  amount         NUMERIC              -- solo para loan/mortgage (NULL para account/card)
)
PARTITION BY DATE(event_ts)
CLUSTER BY product_family, event_type;
