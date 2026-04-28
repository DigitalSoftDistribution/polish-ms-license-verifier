"""Tests for the Polish Microsoft License Verifier."""
from cli.verify import analyze_key, analyze_listing, analyze_legality


def test_valid_key_format():
    a = analyze_key("ABCDE-12345-FGHIJ-67890-KLMNO")
    assert a.valid_format is True


def test_invalid_key_too_short():
    a = analyze_key("ABCDE-12345-FGHIJ")
    assert a.valid_format is False


def test_invalid_key_lowercase_normalized():
    a = analyze_key("abcde-12345-fghij-67890-klmno")
    assert a.valid_format is True


def test_known_gvlk_classified():
    a = analyze_key("VK7JG-NPHTM-C97JM-9MPGT-3V66T")
    assert "Volume" in a.key_type_likely or "GVLK" in a.key_type_likely


def test_listing_high_discount_flagged():
    a = analyze_listing("Office 2024 Pro Plus", 49.0)
    assert a.risk_level in ("high", "very_high")
    assert a.discount_pct >= 80


def test_listing_normal_price_low_risk():
    a = analyze_listing("Office 2024 Pro Plus", 559.0)
    assert a.risk_level == "low"


def test_listing_unknown_product():
    a = analyze_listing("Quirky Custom Software 9000", 100.0)
    assert a.rrp_pln is None


def test_listing_known_grey_seller():
    a = analyze_listing("Windows 11 Pro", 49.0, seller="g2deal.com")
    assert a.risk_level == "very_high"


def test_legality_subscription_blocked():
    listing = analyze_listing("Microsoft 365 Family", 99.0)
    key = analyze_key("ABCDE-12345-FGHIJ-67890-KLMNO")
    leg = analyze_legality(key, listing)
    assert leg.can_legally_resell_eu is False
    assert any("365" in m or "subscription" in m.lower() for m in leg.requirements_missing)


def test_legality_perpetual_normal_pass():
    listing = analyze_listing("Office 2021 Pro Plus", 359.0)
    key = analyze_key("ABCDE-12345-FGHIJ-67890-KLMNO")
    leg = analyze_legality(key, listing)
    # Should not be flagged on requirements_missing for the price
    assert listing.risk_level == "low"
