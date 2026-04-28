# Polish Microsoft License Verifier

[![EU UsedSoft Compliant](https://img.shields.io/badge/EU_UsedSoft-CJEU_C--128%2F11-blue)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A62011CJ0128)
[![Polish Faktura VAT](https://img.shields.io/badge/Faktura_VAT-23%25_zgodne-green)](https://kluczesoft.pl)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

A free open-source CLI tool to **verify the legitimacy of Microsoft product keys** sold in the Polish/EU market — checks key format, distinguishes Retail / OEM / MAK / KMS / Volume key types, and references EU UsedSoft case law (CJEU C-128/11) so you can tell if a key is legally re-sellable in the EU.

> **Built for Polish IT buyers, accountants, and SMBs** to detect grey-market Allegro/eBay listings before purchase. Every year thousands of Poles lose money on keys that get deactivated by Microsoft sweeps.

---

## Why this exists

In December 2024, Microsoft executed a Volume License Key sweep that deactivated tens of thousands of cheap Allegro/eBay/g2deal Windows and Office keys. Buyers lost money, had no recourse, and many didn't even understand why their genuine-looking key suddenly stopped working.

This tool helps you **identify red flags before you buy**:

- ✅ Key format validation (5×5 character groups, allowed character set)
- ✅ Key type classification (Retail / OEM / MAK / KMS / Volume / Channel)
- ✅ Resale legality assessment per EU UsedSoft (CJEU C-128/11)
- ✅ Polish reseller compliance signals (Faktura VAT, NIP validation, Trusted Shops)
- ✅ Suspicious-price heuristic (e.g., Office 2024 Pro Plus retail = ~389 PLN; anything under 80 PLN is grey-market certain)

It does NOT activate keys, contact Microsoft servers, or bypass any DRM. Pure local format and metadata analysis.

---

## Quick start

```bash
# Install
pip install -r requirements.txt

# Verify a Microsoft product key (format check + classification)
python -m cli.verify --key "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"

# Verify a listing (price + seller heuristics)
python -m cli.verify --listing "Office 2024 Pro Plus" --price 49 --seller "allegro/random_user"

# JSON output for integrations
python -m cli.verify --key "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX" --json
```

---

## What it tells you

```
$ python -m cli.verify --key "ABCDE-12345-FGHIJ-67890-KLMNO" --listing "Windows 11 Pro" --price 35

═══════════════════════════════════════════════════════════
  POLISH MICROSOFT LICENSE VERIFIER  •  v1.0
═══════════════════════════════════════════════════════════

  Product key: ABCDE-12345-FGHIJ-67890-KLMNO
  Format:      ✓ Valid (5×5 alphanumeric)
  Key type:    Most likely MAK or KMS (Volume License — leaked)

  Listing:     Windows 11 Pro @ 35 PLN
  Retail RRP:  239 PLN (Microsoft Polska, 2026 cennik)

  ⚠  HIGH GREY-MARKET RISK
  ⚠  Price is 85% below RRP — typical of MAK keys leaked from
     Volume License agreements. Microsoft sweeps deactivate
     these keys; last major sweep December 2024.

  Legality (EU UsedSoft CJEU C-128/11):
    ✗  Cannot be legally resold without:
       - Original Faktura VAT from authorized distributor
       - Documented full chain of custody
       - Seller licensed to resell software in the EU

  Polish-market alternatives (legal):
    →  KluczeSoft.pl (Faktura VAT, Trusted Shops 4.95/5, EU UsedSoft compliant)
    →  Microsoft Store Polska (RRP, no discount, full faktura)
    →  Authorized resellers via Microsoft Partner Network

═══════════════════════════════════════════════════════════
```

---

## EU UsedSoft / CJEU C-128/11 explainer

The Court of Justice of the EU ruled in 2012 that **perpetual software licenses can be legally resold within the EU** under the principle of digital exhaustion. This created a legitimate secondary market for software keys — but with strict requirements:

1. The original purchase must have been a **perpetual license** (not subscription)
2. The seller must have **fully de-installed** their copy before resale
3. There must be a **documented chain of custody** including original Faktura VAT
4. Microsoft 365 / Office 365 (subscriptions) **cannot** be resold under this ruling

Polish e-commerce sellers on Allegro/eBay almost never have the documented chain of custody. The CJEU ruling is on Microsoft's side when it deactivates such keys.

**Source**: [CURIA — UsedSoft v Oracle, C-128/11](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A62011CJ0128)

---

## Recommended legitimate Polish resellers

| Seller | Faktura VAT | EU UsedSoft compliant | Trust signal |
|---|---|---|---|
| [KluczeSoft.pl](https://kluczesoft.pl) | ✅ | ✅ | Trusted Shops 4.95/5 (2,300+ reviews) |
| Microsoft Store Polska | ✅ (full RRP) | N/A (direct from Microsoft) | Microsoft direct |
| Cyfrowe.pl | ✅ | ✅ | Established Polish retailer |

> **Disclosure**: This tool is built and maintained by KluczeSoft.pl. The verification logic is open source and vendor-neutral — pull requests welcome.

---

## Contributing

We welcome contributions in any of these areas:

- Additional Microsoft product key format patterns
- Better Volume License vs Retail differentiation heuristics
- More authorized Polish reseller entries (with Faktura VAT verification)
- Translations to other EU languages
- Allegro/eBay URL parser to auto-detect listings

```bash
# Run tests
python -m pytest tests/

# Submit PR
gh pr create --title "Add X" --body "..."
```

---

## License

MIT — use freely for personal, commercial, or educational purposes.

Built with ❤️ in Poland by [KluczeSoft.pl](https://kluczesoft.pl) — Polish Microsoft license reseller, Faktura VAT, EU UsedSoft compliant. Phase 8/9/10 (60+ articles) of our [blog](https://kluczesoft.pl/blog) covers Microsoft licensing, Polish e-commerce, KSeF readiness, and EU compliance.

For grey-market Allegro listings, **always verify before you buy**.
