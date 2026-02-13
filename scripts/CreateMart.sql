CREATE OR REPLACE TABLE `mart.dim_customer` AS
SELECT
  customer_id,
  age_band,
  residency,
  segment,
  created_date
FROM `raw.raw_customers`;


CREATE OR REPLACE TABLE `mart.dim_campaign` AS
SELECT
  campaign_id,
  ANY_VALUE(source) AS source
FROM `raw.raw_marketing_events`
GROUP BY campaign_id;

CREATE OR REPLACE TABLE `mart.dim_channel` AS
SELECT
  CONCAT('ch_', channel) AS channel_id,
  channel
FROM (
  SELECT DISTINCT channel
  FROM `raw.raw_marketing_events`
);

CREATE OR REPLACE TABLE `mart.dim_product` AS
SELECT
  CONCAT('p_', product_family) AS product_id,
  product_family
FROM (
  SELECT DISTINCT product_family
  FROM `raw.raw_product_events`
);

CREATE OR REPLACE TABLE `mart.dim_date` AS
WITH d AS (
  SELECT DATE(event_ts) AS dt FROM `raw.raw_marketing_events`
  UNION DISTINCT
  SELECT DATE(event_ts) AS dt FROM `raw.raw_product_events`
  UNION DISTINCT
  SELECT created_date AS dt FROM `raw.raw_customers`
)
SELECT
  FORMAT_DATE('%Y%m%d', dt) AS date_id,
  dt AS date,
  EXTRACT(MONTH FROM dt) AS month,
  EXTRACT(YEAR FROM dt) AS year,
  EXTRACT(WEEK FROM dt) AS week
FROM d;


CREATE OR REPLACE TABLE `mart.fact_marketing_daily` AS
WITH base AS (
  SELECT
    FORMAT_DATE('%Y%m%d', DATE(event_ts)) AS date_id,
    campaign_id,
    CONCAT('ch_', channel) AS channel_id,
    event_type,
    cost
  FROM `raw.raw_marketing_events`
)
SELECT
  date_id,
  campaign_id,
  channel_id,
  COUNTIF(event_type = 'impression') AS impressions,
  COUNTIF(event_type = 'click') AS clicks,
  COUNTIF(event_type = 'lead') AS leads,
  SUM(COALESCE(cost, 0)) AS cost
FROM base
GROUP BY 1,2,3;


CREATE OR REPLACE TABLE `mart.fact_funnel_customer` AS
WITH first_lead AS (
  SELECT
    customer_id,
    MIN(event_ts) AS first_lead_ts
  FROM `raw.raw_marketing_events`
  WHERE event_type = 'lead'
  GROUP BY customer_id
),
first_touch AS (
  SELECT
    m.customer_id,
    ANY_VALUE(m.campaign_id) AS first_campaign_id,
    ANY_VALUE(CONCAT('ch_', m.channel)) AS first_channel_id,
    FORMAT_DATE('%Y%m%d', DATE(fl.first_lead_ts)) AS lead_date_id
  FROM `raw.raw_marketing_events` m
  JOIN first_lead fl
    ON m.customer_id = fl.customer_id
   AND m.event_ts = fl.first_lead_ts
  GROUP BY m.customer_id, fl.first_lead_ts
),
prod AS (
  SELECT
    customer_id,
    FORMAT_DATE('%Y%m%d', DATE(MIN(IF(product_family='account' AND event_type='opened', event_ts, NULL)))) AS account_opened_date_id,
    FORMAT_DATE('%Y%m%d', DATE(MIN(IF(product_family='card' AND event_type='opened', event_ts, NULL)))) AS card_opened_date_id,

    FORMAT_DATE('%Y%m%d', DATE(MIN(IF(product_family='loan' AND event_type='applied', event_ts, NULL)))) AS loan_applied_date_id,
    FORMAT_DATE('%Y%m%d', DATE(MIN(IF(product_family='loan' AND event_type='approved', event_ts, NULL)))) AS loan_approved_date_id,

    FORMAT_DATE('%Y%m%d', DATE(MIN(IF(product_family='mortgage' AND event_type='applied', event_ts, NULL)))) AS mortgage_applied_date_id,
    FORMAT_DATE('%Y%m%d', DATE(MIN(IF(product_family='mortgage' AND event_type='approved', event_ts, NULL)))) AS mortgage_approved_date_id
  FROM `raw.raw_product_events`
  GROUP BY customer_id
)
SELECT
  c.customer_id,

  ft.lead_date_id,
  p.account_opened_date_id,
  p.card_opened_date_id,

  p.loan_applied_date_id,
  p.loan_approved_date_id,

  p.mortgage_applied_date_id,
  p.mortgage_approved_date_id,

  ft.first_campaign_id,
  ft.first_channel_id
FROM `mart.dim_customer` c
LEFT JOIN first_touch ft ON c.customer_id = ft.customer_id
LEFT JOIN prod p ON c.customer_id = p.customer_id;




CREATE OR REPLACE TABLE `mart.funnel_kpis_daily` AS
SELECT
  lead_date_id AS date_id,
  first_campaign_id AS campaign_id,
  first_channel_id AS channel_id,

  COUNTIF(lead_date_id IS NOT NULL) AS leads,
  COUNTIF(account_opened_date_id IS NOT NULL) AS accounts_opened,
  COUNTIF(card_opened_date_id IS NOT NULL) AS cards_opened,
  COUNTIF(loan_applied_date_id IS NOT NULL) AS loans_applied,
  COUNTIF(loan_approved_date_id IS NOT NULL) AS loans_approved,
  COUNTIF(mortgage_applied_date_id IS NOT NULL) AS mortgages_applied,
  COUNTIF(mortgage_approved_date_id IS NOT NULL) AS mortgages_approved
FROM `mart.fact_funnel_customer`
GROUP BY 1,2,3;



