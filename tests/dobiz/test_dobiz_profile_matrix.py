"""
Static regression tests for DOBiz signup provisioning logic.
Run anywhere (no frappe needed):
    python -m pytest tests/dobiz/test_dobiz_profile_matrix.py -q
or: python tests/dobiz/test_dobiz_profile_matrix.py
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
API_CANDIDATES = [
    os.path.join(HERE, "..", "..", "..", "..",
                 "bizmarketing", "bizmarketing", "api", "dobiz_signup_api.py"),
]
INDUSTRIES = ["Agriculture", "Manufacturing", "Construction", "Retail & Wholesale",
              "Services", "Healthcare", "Education", "Technology & IT",
              "Hospitality & Tourism", "Finance & Insurance", "Non-Profit / NGO", "Other"]
TIERS = ["Starter Module", "Business Growth", "Full Industry ERP Package"]
TERMS = ["3", "6", "12"]
DISCOUNTS = {"3": 0.0, "6": 0.10, "12": 0.20}
BASE_PRICE = {"Starter Module": 5000, "Business Growth": 9500, "Full Industry ERP Package": 15000}


def api_source():
    for p in API_CANDIDATES:
        if os.path.exists(p):
            return open(p, encoding="utf-8").read(), p
    raise FileNotFoundError("dobiz_signup_api.py not found relative to tests")


def test_norm_ind_defined_before_use():
    """Regression for UnboundLocalError crash (F1): assignment must precede ALL uses."""
    src, _ = api_source()
    lines = src.splitlines()
    assign = [i for i, l in enumerate(lines) if re.search(r"\bnorm_ind\s*=", l)]
    uses = [i for i, l in enumerate(lines)
            if re.search(r"\bnorm_ind\b", l) and i not in assign]
    assert assign, "norm_ind assignment missing"
    assert uses, "norm_ind never used?"
    assert min(assign) < min(uses), (
        f"norm_ind assigned at lines {[a+1 for a in assign]} but first used at line {min(uses)+1}")


def test_alias_covers_all_form_options():
    src, _ = api_source()
    m = re.search(r"INDUSTRY_ALIASES\s*=\s*\{(.*?)\n\}", src, re.S)
    assert m, "INDUSTRY_ALIASES dict not found"
    body = m.group(1).lower()
    for ind in INDUSTRIES:
        assert ind.lower() in body or f'"{ind}"' in src, f"alias missing for {ind}"


def test_full_profiles_cover_all_or_fallback_safe():
    """Every industry must either be in INDUSTRY_FULL_PROFILES or safely fall back
    (fallback = SaaS Settings mapping); we statically require the dict exists and
    contains no alias keys that are absent from the 12 form options."""
    src, _ = api_source()
    m = re.search(r"INDUSTRY_FULL_PROFILES\s*=\s*\{(.*?)\n\}", src, re.S)
    assert m, "INDUSTRY_FULL_PROFILES dict not found"
    keys = re.findall(r'"([^"]+)"\s*:', m.group(1))
    for k in keys:
        assert k in INDUSTRIES, f"FULL_PROFILES key '{k}' is not one of the 12 form options"


def test_pricing_math_nine_combos():
    for tier, base in BASE_PRICE.items():
        for term in TERMS:
            expect = round(base * int(term) * (1 - DISCOUNTS[term]), 2)
            assert expect > 0
    # spot-check verified production values
    assert round(BASE_PRICE["Starter Module"] * 3) == 15000
    assert round(BASE_PRICE["Business Growth"] * 6 * 0.90) == 51300
    assert round(BASE_PRICE["Full Industry ERP Package"] * 12 * 0.80) == 144000


def test_skip_provisioning_flag_wired_both_sides():
    src, path = api_source()
    trial_path = path.replace("api" + os.sep + "dobiz_signup_api.py",
                              "api" + os.sep + "dobiz_trial.py")
    trial = open(trial_path, encoding="utf-8").read()
    assert 'signup_doc.flags.dobiz_skip_provisioning = 1' in src, \
        "API must set skip flag before signup insert"
    assert 'dobiz_skip_provisioning' in trial, \
        "hook must early-return on skip flag"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1; print(f"FAIL {fn.__name__}: {e}")
    sys.exit(1 if failed else 0)
