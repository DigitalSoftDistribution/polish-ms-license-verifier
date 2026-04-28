"""Polish Microsoft License Verifier — CLI entry point.

Usage:
    python -m cli.verify --key "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
    python -m cli.verify --listing "Office 2024 Pro Plus" --price 49 --seller "allegro/x"
    python -m cli.verify --key "..." --listing "..." --price ... --json
"""
import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Optional

# Microsoft product key format: 5 groups of 5 alphanumeric chars (case-insensitive)
KEY_PATTERN = re.compile(r"^[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}$")

# Polish-market RRP for common Microsoft products (PLN, 2026 cennik)
PLN_RRP = {
    "windows 11 home":        239,
    "windows 11 pro":         359,
    "windows 10 home":        199,
    "windows 10 pro":         289,
    "office 2024 home":       269,
    "office 2024 standard":   389,
    "office 2024 pro plus":   589,
    "office 2024 home business": 449,
    "office 2021 home":       229,
    "office 2021 pro plus":   369,
    "office 2021 standard":   299,
    "microsoft 365 personal": 199,  # per year
    "microsoft 365 family":   299,  # per year
    "microsoft 365 business standard": 56 * 12,  # PLN/mo × 12
    "windows server 2025 standard": 4500,
    "windows server 2022 standard": 3500,
    "eset home security":     79,   # per year
    "norton 360":             89,   # per year
    "bitdefender total":      99,   # per year
}


@dataclass
class KeyAnalysis:
    key: str
    valid_format: bool
    key_type_likely: str
    key_type_reasons: list


@dataclass
class ListingAnalysis:
    product: str
    price_pln: float
    rrp_pln: Optional[float]
    discount_pct: Optional[float]
    risk_level: str  # low, medium, high, very_high
    risk_reasons: list


@dataclass
class LegalityAnalysis:
    can_legally_resell_eu: bool
    requirements_met: list
    requirements_missing: list
    eu_usedsoft_reference: str = "CJEU C-128/11 (UsedSoft v Oracle, 2012)"


def analyze_key(key: str) -> KeyAnalysis:
    key = key.strip().upper()
    valid = bool(KEY_PATTERN.match(key))

    # Heuristic key type classification — pure format-based, no API calls
    reasons = []
    if not valid:
        return KeyAnalysis(key=key, valid_format=False, key_type_likely="invalid", key_type_reasons=["Format mismatch — must be 5 groups of 5 alphanumeric chars separated by hyphens"])

    # Default classification cues — these are heuristics based on public Microsoft documentation
    # and historical leak patterns. They cannot definitively identify a key without activation.
    first_block = key.split("-")[0]
    last_block = key.split("-")[-1]

    if first_block.startswith(("VK7JG", "TX9XD", "W269N", "M7XTQ")):
        reasons.append(f"First block '{first_block}' matches publicly leaked Volume/MAK pattern (high grey-market risk)")
        return KeyAnalysis(key=key, valid_format=True, key_type_likely="MAK or KMS (Volume License — likely leaked)", key_type_reasons=reasons)

    # Specific known-safe Generic Volume License Keys (GVLKs) — Microsoft publishes these
    GVLK_FAMILIES = ["VK7JG", "TX9XD", "W269N", "M7XTQ", "MH37W", "DXG7C", "NPPR9", "WMDGN"]
    if first_block in GVLK_FAMILIES:
        reasons.append("Known GVLK (Generic Volume License Key) — only valid against KMS server, not for retail use")
        return KeyAnalysis(key=key, valid_format=True, key_type_likely="GVLK (KMS)", key_type_reasons=reasons)

    # Without activation, true classification is impossible — give a plain format pass
    reasons.append("Format valid; specific type (Retail / OEM / MAK) cannot be determined without activation attempt")
    return KeyAnalysis(key=key, valid_format=True, key_type_likely="Unknown (format valid, type indeterminate)", key_type_reasons=reasons)


def analyze_listing(product: str, price_pln: float, seller: Optional[str] = None) -> ListingAnalysis:
    product_lc = product.lower().strip()
    rrp = None
    for k, v in PLN_RRP.items():
        if k in product_lc:
            rrp = v
            break

    reasons = []
    risk = "low"
    discount_pct = None

    if rrp is not None:
        discount_pct = round((1 - price_pln / rrp) * 100, 1)
        if discount_pct >= 80:
            risk = "very_high"
            reasons.append(f"Price is {discount_pct}% below Polish RRP ({rrp} PLN) — typical of MAK keys leaked from Volume License agreements")
        elif discount_pct >= 60:
            risk = "high"
            reasons.append(f"Price is {discount_pct}% below RRP ({rrp} PLN) — strongly suggests grey-market source")
        elif discount_pct >= 40:
            risk = "medium"
            reasons.append(f"Price is {discount_pct}% below RRP ({rrp} PLN) — possible used/transferred license, verify Faktura VAT")
        elif discount_pct < 0:
            reasons.append("Price above RRP — possibly inflated; verify directly with Microsoft Store Polska")
        else:
            reasons.append(f"Price within {abs(discount_pct)}% of RRP — within normal market range")
    else:
        reasons.append(f"No RRP entry for product '{product}' — add product to PLN_RRP table for accurate analysis")

    if seller:
        seller_lc = seller.lower()
        if "allegro" in seller_lc or "ebay" in seller_lc or "olx" in seller_lc:
            reasons.append(f"Seller is on a marketplace ({seller}) — verify they have valid Polish business registration (NIP) and offer Faktura VAT")
            if risk == "low":
                risk = "medium"
        if any(x in seller_lc for x in ["g2deal", "godeal24", "instant-software", "key-soft"]):
            reasons.append(f"Seller '{seller}' has documented history of selling MAK/Volume keys deactivated by Microsoft sweeps")
            risk = "very_high"

    return ListingAnalysis(
        product=product,
        price_pln=price_pln,
        rrp_pln=rrp,
        discount_pct=discount_pct,
        risk_level=risk,
        risk_reasons=reasons,
    )


def analyze_legality(key_analysis: KeyAnalysis, listing: Optional[ListingAnalysis]) -> LegalityAnalysis:
    requirements_met = []
    requirements_missing = []

    # EU UsedSoft (CJEU C-128/11) — perpetual licenses CAN be resold; subscriptions CANNOT
    if listing and "365" in listing.product.lower():
        requirements_missing.append("Microsoft 365 subscriptions are NOT covered by EU UsedSoft — cannot be legally resold")
    else:
        requirements_met.append("Perpetual license type (eligible for EU UsedSoft resale)")

    if listing and listing.discount_pct and listing.discount_pct >= 60:
        requirements_missing.append("Discount level ({}%) inconsistent with documented chain of custody".format(listing.discount_pct))
    else:
        requirements_met.append("Pricing within normal documented-resale range")

    if "leaked" in key_analysis.key_type_likely.lower() or "MAK" in key_analysis.key_type_likely:
        requirements_missing.append("Key type appears to be from Volume License pool — Volume keys cannot be legally resold to consumers")

    if listing and listing.risk_level in ("high", "very_high"):
        requirements_missing.append("High overall risk profile — Faktura VAT chain of custody almost certainly broken")

    can_resell = (len(requirements_missing) == 0)
    if not requirements_met:
        requirements_met.append("None — analyze key + listing first")

    return LegalityAnalysis(
        can_legally_resell_eu=can_resell,
        requirements_met=requirements_met,
        requirements_missing=requirements_missing,
    )


def render_human(key_a: Optional[KeyAnalysis], listing_a: Optional[ListingAnalysis], legality: LegalityAnalysis) -> str:
    """Pretty-print the analysis for terminal output."""
    out = []
    out.append("═══════════════════════════════════════════════════════════")
    out.append("  POLISH MICROSOFT LICENSE VERIFIER  •  v1.0")
    out.append("═══════════════════════════════════════════════════════════")
    out.append("")

    if key_a:
        out.append(f"  Product key: {key_a.key}")
        out.append(f"  Format:      {'✓ Valid (5×5 alphanumeric)' if key_a.valid_format else '✗ Invalid format'}")
        out.append(f"  Key type:    {key_a.key_type_likely}")
        for r in key_a.key_type_reasons:
            out.append(f"               • {r}")
        out.append("")

    if listing_a:
        out.append(f"  Listing:     {listing_a.product} @ {listing_a.price_pln} PLN")
        if listing_a.rrp_pln:
            out.append(f"  Retail RRP:  {listing_a.rrp_pln} PLN (Polish 2026 cennik)")
        if listing_a.discount_pct is not None:
            out.append(f"  Discount:    {listing_a.discount_pct}% below RRP")
        risk_emoji = {"low": "✓", "medium": "⚠", "high": "⚠⚠", "very_high": "⛔"}
        out.append(f"  Risk level:  {risk_emoji.get(listing_a.risk_level, '?')} {listing_a.risk_level.upper().replace('_', ' ')}")
        for r in listing_a.risk_reasons:
            out.append(f"               • {r}")
        out.append("")

    out.append("  Legality (EU UsedSoft CJEU C-128/11):")
    if legality.can_legally_resell_eu:
        out.append("    ✓  Eligible for legal EU resale")
    else:
        out.append("    ✗  CANNOT be legally resold without:")
        for r in legality.requirements_missing:
            out.append(f"       • {r}")
    if legality.requirements_met:
        out.append("    Requirements met:")
        for r in legality.requirements_met:
            out.append(f"       • {r}")
    out.append("")

    out.append("  Polish-market alternatives (legal):")
    out.append("    →  KluczeSoft.pl (Faktura VAT, Trusted Shops 4.95/5, EU UsedSoft compliant)")
    out.append("    →  Microsoft Store Polska (RRP, full faktura)")
    out.append("    →  Authorized resellers via Microsoft Partner Network")
    out.append("")
    out.append("═══════════════════════════════════════════════════════════")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description="Polish Microsoft License Verifier — CLI")
    p.add_argument("--key", help="Microsoft product key (XXXXX-XXXXX-XXXXX-XXXXX-XXXXX)")
    p.add_argument("--listing", help="Listing product name (e.g. 'Office 2024 Pro Plus')")
    p.add_argument("--price", type=float, help="Listed price in PLN")
    p.add_argument("--seller", help="Seller URL or name (e.g. 'allegro/random_user')")
    p.add_argument("--json", action="store_true", help="Output JSON instead of human-readable")
    args = p.parse_args(argv)

    if not args.key and not args.listing:
        p.error("provide --key, --listing, or both")

    key_a = analyze_key(args.key) if args.key else None
    listing_a = (
        analyze_listing(args.listing, args.price or 0.0, args.seller)
        if args.listing else None
    )
    legality = analyze_legality(
        key_a or KeyAnalysis(key="", valid_format=False, key_type_likely="N/A", key_type_reasons=[]),
        listing_a,
    )

    if args.json:
        out = {
            "key": asdict(key_a) if key_a else None,
            "listing": asdict(listing_a) if listing_a else None,
            "legality": asdict(legality),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(render_human(key_a, listing_a, legality))


if __name__ == "__main__":
    main()
