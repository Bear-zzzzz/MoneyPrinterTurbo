import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def top_ten(records, eligible_codes):
    valid = [record for record in records
             if record["code"] in eligible_codes
             and isinstance(record.get("value"), (int, float))
             and math.isfinite(record["value"])
             and record["value"] > 0]
    return sorted(valid, key=lambda record: (-record["value"], record["code"]))[:10]


def animate_value(start, end, fraction):
    if fraction <= 0:
        return start
    if fraction >= 1:
        return end
    eased = fraction * fraction * (3 - 2 * fraction)
    return start + (end - start) * eased


def main():
    source = json.loads((ROOT / "raw/worldbank-gdp.json").read_text())
    country_source = json.loads((ROOT / "raw/worldbank-countries.json").read_text())
    countries = {country["id"]: country for country in country_source[1]
                 if country["region"]["id"] != "NA"}
    rows = [{"code": row["countryiso3code"], "year": int(row["date"]),
             "value": row["value"]} for row in source[1]
            if row["countryiso3code"] in countries]
    audit = []
    candidate_rankings = []
    for year in range(1960, 2026):
        annual = [row for row in rows if row["year"] == year]
        available = {row["code"] for row in annual if row["value"] is not None}
        missing = sorted(set(countries) - available)
        historical = []
        if year <= 1991:
            historical.append("SUN")
        if year <= 1989:
            historical.extend(["DDR", "DEU_WEST_BOUNDARY_REQUIRES_REVIEW"])
        if year <= 1992:
            historical.extend(["YUG", "CSK"])
        selected = top_ten(annual, set(countries))
        audit.append({"year": year, "available_economies": len(available),
                      "missing_economies": missing,
                      "historical_identities_requiring_review": historical,
                      "global_top10_certified": False})
        candidate_rankings.append({"year": year, "universe": "World Bank reported economies only",
                                   "global_top10_certified": False, "top10": selected})
    manifest = {"retrieved_on": "2026-11-17", "lastupdated": source[0]["lastupdated"],
                "indicator": "NY.GDP.MKTP.CD", "unit": "current US dollars",
                "years": audit,
                "status": "Final rendering blocked until historical-country coverage and identity review"}
    (ROOT / "coverage-audit.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    (ROOT / "worldbank-candidate-rankings.json").write_text(json.dumps(candidate_rankings, ensure_ascii=False, indent=2))
    with (ROOT / "worldbank-source-values.csv").open("w", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=["code", "year", "value"])
        writer.writeheader()
        writer.writerows(row for row in rows if row["value"] is not None)
    print(f"Saved {len(rows)} source records and {len(audit)} annual coverage checks; not a certified global ranking.")


if __name__ == "__main__":
    main()
