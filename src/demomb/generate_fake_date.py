#!/usr/bin/env python3
"""
generate_fake_data.py

Genera 3 CSVs coherentes para la demo (BigQuery RAW):
- raw_customers.csv
- raw_marketing_events.csv
- raw_product_events.csv

Diseñado para:
- 20,000 clientes
- eventos de marketing con funnel realista (impression -> click -> lead)
- eventos de producto (account/card/loan/mortgage) coherentes con los leads

Requisitos:
  pip install faker python-dateutil

Uso:
  python generate_fake_data.py --out ./exports --customers 20000 --seed 42

Salida:
  ./exports/raw_customers.csv
  ./exports/raw_marketing_events.csv
  ./exports/raw_product_events.csv
"""

import argparse
import csv
import os
import random
from datetime import datetime, timedelta, timezone, date
from faker import Faker


AGE_BANDS = ["18-25", "26-35", "36-45", "46-60", "60+"]
AGE_WEIGHTS = [0.18, 0.26, 0.22, 0.22, 0.12]

RESIDENCIES = ["AD", "ES", "FR"]
RES_WEIGHTS = [0.55, 0.30, 0.15]

SEGMENTS = ["mass", "affluent"]
SEG_WEIGHTS = [0.82, 0.18]

CHANNELS = ["web", "app", "branch"]
CHANNEL_WEIGHTS = [0.55, 0.25, 0.20]

DEVICES = ["mobile", "desktop"]
DEVICE_WEIGHTS = [0.72, 0.28]

SOURCES = ["google", "meta", "email", "seo", "branch_referral"]
SOURCE_WEIGHTS = [0.40, 0.28, 0.12, 0.12, 0.08]


def utc_ts(dt: datetime) -> str:
    """BigQuery-friendly timestamp string for CSV load (no timezone)."""
    # BigQuery CSV loader accepts 'YYYY-MM-DD HH:MM:SS' easily.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S")



def pick_weighted(rng: random.Random, items, weights):
    return rng.choices(items, weights=weights, k=1)[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="./exports", help="Directorio de salida")
    parser.add_argument("--customers", type=int, default=20000, help="Número de clientes")
    parser.add_argument("--days", type=int, default=120, help="Ventana temporal hacia atrás (días)")
    parser.add_argument("--seed", type=int, default=42, help="Seed para reproducibilidad")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    rng = random.Random(args.seed)
    fake = Faker()
    Faker.seed(args.seed)

    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(days=args.days)

    # -----------------------------
    # Definición de campañas
    # -----------------------------
    # 12 campañas, con source asociado (lo guardas también en raw_marketing_events)
    campaigns = []
    for i in range(1, 13):
        source = pick_weighted(rng, SOURCES, SOURCE_WEIGHTS)
        campaigns.append((f"CMP{i:02d}", source))

    # helper: escoger campaña con preferencia por el source elegido
    def pick_campaign(preferred_source: str) -> tuple[str, str]:
        # 70% del tiempo: campaña del mismo source; si no, cualquiera
        if rng.random() < 0.70:
            same = [c for c in campaigns if c[1] == preferred_source]
            if same:
                return rng.choice(same)
        return rng.choice(campaigns)

    # -----------------------------
    # Salidas CSV
    # -----------------------------
    customers_path = os.path.join(args.out, "raw_customers.csv")
    marketing_path = os.path.join(args.out, "raw_marketing_events.csv")
    product_path = os.path.join(args.out, "raw_product_events.csv")

    # En memoria: atributos clave por customer (para generar producto coherente)
    customers = []  # list of dicts

    # -----------------------------
    # 1) Generar CUSTOMERS
    # -----------------------------
    with open(customers_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["customer_id", "created_date", "age_band", "residency", "segment"])

        for i in range(1, args.customers + 1):
            customer_id = f"CUST{i:05d}"

            created_date = (start_dt + timedelta(days=rng.randint(0, args.days - 1))).date()
            age_band = pick_weighted(rng, AGE_BANDS, AGE_WEIGHTS)
            residency = pick_weighted(rng, RESIDENCIES, RES_WEIGHTS)
            segment = pick_weighted(rng, SEGMENTS, SEG_WEIGHTS)

            customers.append(
                {
                    "customer_id": customer_id,
                    "created_date": created_date,
                    "age_band": age_band,
                    "residency": residency,
                    "segment": segment,
                }
            )
            w.writerow([customer_id, created_date.isoformat(), age_band, residency, segment])

    # -----------------------------
    # 2) Generar MARKETING EVENTS
    # -----------------------------
    # Estrategia:
    # - Para cada customer, generamos 3–12 impressions
    # - clicks ~ Binomial(impressions, CTR) con CTR 10%–22% según source/canal
    # - lead ocurre con prob 20%–40% si hubo clicks
    # Resultado esperado:
    # - ~120k–200k impressions
    # - ~15k–35k clicks
    # - ~4k–10k leads (suficiente para funnel)
    #
    # Costs:
    # - paid channels (google/meta/email): impression 0.002, click 0.25, lead 2.50
    # - seo/branch_referral: costo 0 (NULL)
    paid_sources = {"google", "meta", "email"}

    # Guardamos primer lead para construir coherencia en producto (atribución primera)
    first_lead_by_customer: dict[str, dict] = {}

    with open(marketing_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["event_ts", "customer_id", "campaign_id", "source", "channel", "device", "event_type", "cost"])

        for c in customers:
            customer_id = c["customer_id"]

            # preferencias por customer (para segmentación)
            channel = pick_weighted(rng, CHANNELS, CHANNEL_WEIGHTS)
            device = pick_weighted(rng, DEVICES, DEVICE_WEIGHTS)

            # source principal (afecta CTR y probabilidades)
            source = pick_weighted(rng, SOURCES, SOURCE_WEIGHTS)
            campaign_id, campaign_source = pick_campaign(source)
            # aseguramos consistencia del source guardado con campaña escogida
            source = campaign_source

            # ventana temporal de marketing alrededor de created_date
            base_date = datetime.combine(c["created_date"], datetime.min.time(), tzinfo=timezone.utc)
            base_date = base_date + timedelta(days=rng.randint(0, 10))  # unos días después del alta

            impressions = rng.randint(3, 12)

            # CTR según source/canal (muy simple pero coherente)
            ctr = 0.14
            if source in {"google", "meta"}:
                ctr += 0.04
            if channel == "branch":
                ctr -= 0.05
            if source in {"seo", "branch_referral"}:
                ctr -= 0.03
            ctr = max(0.04, min(0.24, ctr))

            # Generar impressions (como eventos) con timestamps repartidos
            impression_times = []
            for _ in range(impressions):
                dt = base_date + timedelta(hours=rng.randint(0, 240), minutes=rng.randint(0, 59))
                impression_times.append(dt)
                cost = 0.002 if source in paid_sources else None
                w.writerow([utc_ts(dt), customer_id, campaign_id, source, channel, device, "impression", cost])

            # clicks
            clicks = 0
            for dt in impression_times:
                if rng.random() < ctr:
                    clicks += 1
                    click_dt = dt + timedelta(minutes=rng.randint(1, 120))
                    cost = 0.25 if source in paid_sources else None
                    w.writerow([utc_ts(click_dt), customer_id, campaign_id, source, channel, device, "click", cost])

            # lead (si hubo clicks)
            if clicks > 0:
                # tasa lead: 20%–40% (sube para email / branch_referral)
                lead_rate = 0.24
                if source == "email":
                    lead_rate += 0.10
                if source == "branch_referral":
                    lead_rate += 0.12
                if channel == "branch":
                    lead_rate += 0.08
                lead_rate = min(0.55, lead_rate)

                if rng.random() < lead_rate:
                    # lead ocurre después del primer click (aprox)
                    lead_dt = base_date + timedelta(hours=rng.randint(1, 360), minutes=rng.randint(0, 59))
                    cost = 2.50 if source in paid_sources else None
                    w.writerow([utc_ts(lead_dt), customer_id, campaign_id, source, channel, device, "lead", cost])

                    # guardar primer lead si no existe
                    if customer_id not in first_lead_by_customer:
                        first_lead_by_customer[customer_id] = {
                            "lead_dt": lead_dt,
                            "campaign_id": campaign_id,
                            "source": source,
                            "channel": channel,
                            "device": device,
                        }

    # -----------------------------
    # 3) Generar PRODUCT EVENTS
    # -----------------------------
    # Coherencia:
    # - Account opened: mayor prob si tuvo lead; algunos sin lead (walk-in)
    # - Card: depende de account y segmento
    # - Loan/Mortgage: applied y luego approved con prob.
    #
    with open(product_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["event_ts", "customer_id", "product_family", "event_type", "amount"])

        for c in customers:
            customer_id = c["customer_id"]
            segment = c["segment"]
            created_date = c["created_date"]
            base_date = datetime.combine(created_date, datetime.min.time(), tzinfo=timezone.utc)

            has_lead = customer_id in first_lead_by_customer

            # Probabilidad de apertura de cuenta
            p_account = 0.06  # sin lead (walk-in)
            if has_lead:
                p_account = 0.68  # bastante alta si hay lead

            # segmento affluent un poco más propenso
            if segment == "affluent":
                p_account += 0.05

            if rng.random() >= p_account:
                continue  # sin cuenta, no generamos productos

            # account opened (después del lead si existe)
            if has_lead:
                open_dt = first_lead_by_customer[customer_id]["lead_dt"] + timedelta(days=rng.randint(1, 14), hours=rng.randint(0, 12))
            else:
                open_dt = base_date + timedelta(days=rng.randint(0, 30), hours=rng.randint(0, 12))

            w.writerow([utc_ts(open_dt), customer_id, "account", "opened", None])

            # tarjeta (depende de segmento)
            p_card = 0.42 if segment == "mass" else 0.58
            # canal branch tiende a cross-sell un poco más
            if has_lead and first_lead_by_customer[customer_id]["channel"] == "branch":
                p_card += 0.05

            if rng.random() < p_card:
                card_dt = open_dt + timedelta(days=rng.randint(0, 20), hours=rng.randint(0, 10))
                w.writerow([utc_ts(card_dt), customer_id, "card", "opened", None])

            # préstamo (menos frecuente)
            p_loan_apply = 0.10 if segment == "mass" else 0.18
            # hipoteca aún menos frecuente
            p_mort_apply = 0.02 if segment == "mass" else 0.05

            # Loan applied/approved
            if rng.random() < p_loan_apply:
                applied_dt = open_dt + timedelta(days=rng.randint(7, 60), hours=rng.randint(0, 10))
                amount = rng.randint(2000, 25000) if segment == "mass" else rng.randint(5000, 50000)
                w.writerow([utc_ts(applied_dt), customer_id, "loan", "applied", amount])

                # prob aprobación (affluent mayor)
                p_approve = 0.58 if segment == "mass" else 0.72
                if rng.random() < p_approve:
                    approved_dt = applied_dt + timedelta(days=rng.randint(1, 10), hours=rng.randint(0, 6))
                    w.writerow([utc_ts(approved_dt), customer_id, "loan", "approved", amount])

            # Mortgage applied/approved
            if rng.random() < p_mort_apply:
                applied_dt = open_dt + timedelta(days=rng.randint(15, 120), hours=rng.randint(0, 10))
                amount = rng.randint(80000, 250000) if segment == "mass" else rng.randint(120000, 500000)
                w.writerow([utc_ts(applied_dt), customer_id, "mortgage", "applied", amount])

                p_approve = 0.52 if segment == "mass" else 0.66
                if rng.random() < p_approve:
                    approved_dt = applied_dt + timedelta(days=rng.randint(3, 15), hours=rng.randint(0, 6))
                    w.writerow([utc_ts(approved_dt), customer_id, "mortgage", "approved", amount])

    print("✅ CSVs generados:")
    print(f" - {customers_path}")
    print(f" - {marketing_path}")
    print(f" - {product_path}")
    print()
    print("Siguiente paso: cargar estos CSV a BigQuery en DemoMB.raw (raw_customers, raw_marketing_events, raw_product_events).")


if __name__ == "__main__":
    main()
