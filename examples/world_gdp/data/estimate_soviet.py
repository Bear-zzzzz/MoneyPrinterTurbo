import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ANCHOR_YEAR = 1970


def positive(value):
    return isinstance(value, (int, float)) and math.isfinite(value) and value > 0


def backcast(anchor_usd, real_output, dollar_price_proxy):
    if not positive(anchor_usd):
        raise ValueError("Anchor must be a finite positive dollar value")
    if ANCHOR_YEAR not in real_output or ANCHOR_YEAR not in dollar_price_proxy:
        raise ValueError("Missing anchor-year inputs")
    for year, value in real_output.items():
        if year > ANCHOR_YEAR or not positive(value) or not positive(dollar_price_proxy.get(year)):
            raise ValueError(f"Invalid or missing inputs for {year}")
    real_anchor = real_output[ANCHOR_YEAR]
    price_anchor = dollar_price_proxy[ANCHOR_YEAR]
    rows = []
    for year in sorted(real_output):
        real_ratio = real_output[year] / real_anchor
        price_ratio = dollar_price_proxy[year] / price_anchor
        fixed_price = anchor_usd * real_ratio
        estimate = anchor_usd if year == ANCHOR_YEAR else fixed_price * price_ratio
        rows.append({
            "year": year,
            "value_usd": estimate,
            "display_billion_usd": round(estimate / 1e9, 1),
            "constant_price_proxy_usd": fixed_price,
            "real_output_ratio": real_ratio,
            "dollar_price_proxy_ratio": price_ratio,
            "status": "source_published" if year == ANCHOR_YEAR else "estimated",
        })
    return rows


def load_inputs():
    historical = json.loads((ROOT / "un-historical-gdp.json").read_text())
    soviet = next(row for row in historical["records"] if row["country"] == "USSR (Former)")
    anchor_usd = soviet["values_usd"][str(ANCHOR_YEAR)]
    real_output = {}
    with (ROOT / "raw/maddison-owid-gdp.csv").open(newline="") as source:
        for row in csv.DictReader(source):
            year = int(row["Year"])
            if row["Entity"] == "USSR" and 1960 <= year <= ANCHOR_YEAR:
                real_output[year] = float(row["GDP"])
    quarterly_prices = {}
    with (ROOT / "raw/fred-gdpdef-1960-1970.csv").open(newline="") as source:
        for row in csv.DictReader(source):
            date = row["observation_date"]
            year = int(date[:4])
            value = float(row["GDPDEF"])
            if not positive(value):
                raise ValueError(f"Invalid price observation for {date}")
            quarterly_prices.setdefault(year, {})[date] = value
    expected = set(range(1960, ANCHOR_YEAR + 1))
    if set(real_output) != expected or set(quarterly_prices) != expected:
        raise ValueError("Every input series must contain all eleven requested years")
    price_proxy = {}
    for year in sorted(expected):
        dates = {f"{year}-{month:02d}-01" for month in (1, 4, 7, 10)}
        if set(quarterly_prices[year]) != dates:
            raise ValueError(f"Four quarterly price observations required for {year}")
        price_proxy[year] = sum(quarterly_prices[year].values()) / 4
    return anchor_usd, real_output, price_proxy


def main():
    anchor_usd, real_output, price_proxy = load_inputs()
    rows = backcast(anchor_usd, real_output, price_proxy)
    fields = list(rows[0])
    with (ROOT / "soviet-gdp-1960-1970-estimates.csv").open("w", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    inputs = [{"year": year, "soviet_real_output_international_dollars": real_output[year],
               "us_deflator_proxy_quarterly_mean": price_proxy[year]} for year in sorted(real_output)]
    files = ["un-historical-gdp.json", "raw/maddison-owid-gdp.csv",
             "raw/maddison-owid-gdp.metadata.json", "raw/fred-gdpdef-1960-1970.csv"]
    metadata = {
        "country": "苏联 / USSR",
        "estimated_years": [1960, 1969],
        "source_anchor_year": ANCHOR_YEAR,
        "anchor_usd": anchor_usd,
        "created_on": "2026-11-17",
        "user_authorized_estimation": True,
        "method": "UN 1970 dollar anchor × USSR real-output ratio × assumed US dollar-price-deflator ratio",
        "formula": "E_t = UN_USD_1970 * (Q_t/Q_1970) * (mean_GDPDEF_t/mean_GDPDEF_1970)",
        "display_label": "苏联 GDP ≈；1960—1969 为模型估算",
        "sources": [
            {"name": "UN National Accounts Main Aggregates, USSR (Former), current USD",
             "url": "https://unstats.un.org/unsd/amaapi/api/file/2"},
            {"name": "Maddison Project Database 2023, processed by OWID, USSR real-output growth proxy",
             "url": "https://ourworldindata.org/grapher/gdp-maddison-project-database",
             "unit": "international dollars at 2011 prices; used only as within-country ratios, never directly as market USD"},
            {"name": "BEA US GDP implicit price deflator, GDPDEF via FRED",
             "annual_aggregation": "Arithmetic mean of four quarterly GDPDEF observations; proxy, not a separately downloaded annual BEA series",
             "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDPDEF&cosd=1960-01-01&coed=1970-12-31"},
        ],
        "limitations": [
            "1960-1969 values are illustrative model backcasts, not observed Soviet nominal GDP or historically reconstructed ruble-to-dollar conversions.",
            "US price changes are an explicit proxy assumption; Soviet relative prices and exchange rates are not recovered by this model.",
            "Maddison real-output ratios are themselves historical estimates and depend on the dataset vintage.",
            "1970 anchor is the UN-published historical USD conversion; it is not assumed to equal other research databases' estimates.",
            "Do not claim precise ranking for closely sized economies without sensitivity review.",
            "constant_price_proxy_usd is a flat-price alternative for sensitivity, not another observed nominal series or a statistical confidence interval.",
            "The global ranking files are not modified by this estimator; any later integration must preserve estimated status.",
        ],
        "input_sha256": {file: hashlib.sha256((ROOT / file).read_bytes()).hexdigest() for file in files},
        "inputs": inputs,
        "estimates": rows,
    }
    (ROOT / "soviet-gdp-1960-1970-method.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
    for row in rows:
        print(row["year"], f'{row["value_usd"] / 1e9:.1f}', row["status"])
    print("Saved separate model backcast; no global ranking or existing source data overwritten.")


if __name__ == "__main__":
    main()
