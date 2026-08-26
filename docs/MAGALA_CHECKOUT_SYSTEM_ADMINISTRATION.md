# Magala Checkout — System Administration

**Site:** https://ethiobiz.et  
**Date:** 2026-08-27  
**Audience:** System administrators, DevOps, and implementers deploying EthioBiz on this server or a new server  
**BISMALLAH. INSHA'ALLAH.**

Companion document: [MAGALA_CHECKOUT_USER_MANUAL_2026-08-26.md](./MAGALA_CHECKOUT_USER_MANUAL_2026-08-26.md).

---

## 1. Purpose

Magala Checkout adds three storefront payment methods on `/cart`:

1. **AddisPay** — official hosted checkout (`POST {base}/checkout-api/v1/create-order`, header `Auth: {API_KEY}`).
2. **Bank Transfer** — Magala Shop Payment stays Pending until Desk **Approve Payment**.
3. **Cash upon Delivery** — only for configurable product/food item-group fragments.

EthioBiz is the **platform merchant**. One Magala Shop Payment can split into **one Sales Order per seller company**.

This is **not** the DOBiz subscription checkout (`/dobiz-payment`). Magala `tx_ref` values start with `MAGALA-`. DOBiz wrappers keep using the shared AddisPay client in `bizmarketing.api.addispay`.

---

## 2. Production constants

| Item | Value |
|---|---|
| URL | https://ethiobiz.et |
| SSH | `root@128.140.82.215` |
| Site | `ethiobiz.et` |
| Bench (in container) | `/home/frappe/frappe-bench` |
| Image | `ethiobiz-custom:latest` |
| Backend | `bismallah_ethiobiz_inshaallah-backend-1` |
| Frontend | `bismallah_ethiobiz_inshaallah-frontend-1` |
| DB | `bismallah_ethiobiz_inshaallah-db-1` |
| Proxy | `nginx-proxy` |
| Compose | `/root/ethiobiz_deployment/BISMALLAH_ETHIOBIZ_INSHA'ALLAH/pwd-cloud-existing.yml` |
| Git (theme) | `BizTechnologyet/bismillah_ethiobiz_ethiobiz` |
| Git (marketing) | `BizTechnologyet/BizMarketing` |

**Never** `docker compose down` the whole host stack (protects n8n / Postgres / MCP).  
**Never** `cd` on Windows into paths that contain `INSHA'ALLAH` (PowerShell quoting). Use `python3.11 C:\Users\bizit\tmp_magala\…`.  
**Disk** must be **under 85%** before `docker commit` or large builds.

There is **no bench CLI** in this production image. Use `/home/frappe/frappe-bench/env/bin/python` and Frappe APIs (`import_file_by_path`, not a full `SiteMigration` if unrelated apps fail).

---

## 3. Git repositories (permanence for a new server)

| App | What Magala lives in |
|---|---|
| `bizmarketing` | AddisPay client, DocTypes (Magala Checkout Settings, Magala Shop Payment, Magala Shop Payment Order, Magala Bank Account), `magala_setup.ensure_magala_checkout` (`after_migrate`) |
| `bismillah_ethiobiz` | `magala_checkout.py`, `public/js/magala_checkout.js`, `public/css/magala_checkout.css`, `www/magala-payment-success.html`, `www/magala-payment-failed.html`, website includes in `hooks.py` / `api.update_website_context` |
| Tests | `tests/suites/suite_41_magala_checkout_payments.py` (copy onto the bench `tests/suites/` path used in production) |

A new server is **not** updated by host `git pull` of a compose folder alone. Apps are **inside the image** and/or cloned under `apps/`. After git pull of the two apps:

1. Install/migrate the site (Python `SiteMigration` **or** targeted `import_file_by_path` for Magala JSON if full migrate fails).
2. `after_migrate` runs `bizmarketing.magala_setup.ensure_magala_checkout`.
3. Flatten `sites/assets` and copy into the **frontend** container (frontend cannot follow `apps/` symlinks).
4. Restart **backend**, wait ~8–10s, restart **frontend** (nginx upstream DNS) **or** `nginx -s reload` if IPs did not change.
5. `docker commit bismallah_ethiobiz_inshaallah-backend-1 ethiobiz-custom:latest` when disk &lt; 85%.

### 3.1 New-server git sequence (container)

```bash
BACKEND=bismallah_ethiobiz_inshaallah-backend-1
BENCH=/home/frappe/frappe-bench

docker exec $BACKEND bash -lc "cd $BENCH/apps/bizmarketing && git fetch && git checkout main && git pull"
docker exec $BACKEND bash -lc "cd $BENCH/apps/bismillah_ethiobiz && git fetch && git checkout main && git pull"
docker exec $BACKEND $BENCH/env/bin/pip install -e $BENCH/apps/bizmarketing --no-build-isolation
docker exec $BACKEND $BENCH/env/bin/pip install -e $BENCH/apps/bismillah_ethiobiz --no-build-isolation
```

Then import Magala DocTypes (safer than full migrate on this stack):

```python
# run with env/bin/python inside sites/
import os
os.chdir("/home/frappe/frappe-bench/sites")
import frappe
from frappe.modules.import_file import import_file_by_path
frappe.init("ethiobiz.et")
frappe.connect()
base = "/home/frappe/frappe-bench/apps/bizmarketing/bizmarketing/marketing/doctype"
for p in [
    base + "/magala_bank_account/magala_bank_account.json",
    base + "/magala_shop_payment_order/magala_shop_payment_order.json",
    base + "/magala_shop_payment/magala_shop_payment.json",
    base + "/magala_checkout_settings/magala_checkout_settings.json",
]:
    import_file_by_path(p, force=True, ignore_version=True)
    frappe.db.commit()
from bizmarketing.magala_setup import ensure_magala_checkout
ensure_magala_checkout()
frappe.clear_cache()
frappe.destroy()
```

**Do not** re-run full `SiteMigration().run('ethiobiz.et')` if restaurant_management (or another app) raises `NameError: Document is not defined`. That failure is unrelated to Magala.

### 3.2 Asset sync (mandatory for `/cart` UI)

Copy these into **both** backend `apps/…/public/` **and** frontend `sites/assets/bismillah_ethiobiz/`:

- `js/magala_checkout.js`
- `js/all_products_custom.js` (Add to Cart on `/all-products`)
- `css/magala_checkout.css`

Bump the query string in `bismillah_ethiobiz/hooks.py` and `api.py` (`magala_checkout.js?v=…`) after JS changes so browsers do not keep a stale file.

---

## 4. AddisPay configuration

Official docs: https://devportal.addispay.et/docs/get-started and Hosted Checkout.

| Mode | Base URL |
|---|---|
| UAT | `https://uat.api.addispay.et` |
| Production | `https://api.addispay.et` |

- Path: `/checkout-api/v1/create-order` (overridable in Magala Checkout Settings).
- Auth header: **`Auth: {API_KEY}`** (not Bearer).
- Redirect: `{checkout_url}/{uuid}`.
- Magala return pages: `/magala-payment-success`, `/magala-payment-failed` (`{tx_ref}` placeholder supported).

**Desk:** Magala Checkout Settings:

- **Use DOBiz SaaS AddisPay Credentials** — reuse **DOBiz SaaS Settings** key (recommended until Magala has its own merchant key).
- **Sandbox / UAT Mode** — leave ON until a live key is issued.
- **AddisPay API Key (override)** — Magala-only key if the DOBiz checkbox is off.
- **Test AddisPay Connection** (if the form button is present) calls `bizmarketing.api.addispay.test_connection`.

**Webhook (guest):**

`https://ethiobiz.et/api/method/bizmarketing.api.addispay.handle_webhook`

Configure this URL in the AddisPay merchant portal. Magala refs `MAGALA-…` are routed to Magala Shop Payment; other refs stay on the DOBiz subscription handler.

**Secrets:** store only in Desk Password fields. Do not commit live keys to git.

---

## 5. DocTypes and Desk objects

| DocType | Role |
|---|---|
| Magala Checkout Settings | Single: enable methods, labels, URLs, COD/job fragments, bank table, AddisPay endpoints |
| Magala Bank Account | Child table of settings |
| Magala Shop Payment | One checkout attempt (`tx_ref`, method, status, amount, customer) |
| Magala Shop Payment Order | Child: per-company sales order link |
| Mode of Payment | Seeded: Cash upon Delivery, Bank Transfer, AddisPay |
| Client Script | `Magala Shop Payment Admin Approval` — Approve / Reject buttons |

Statuses used in operations: **Pending**, **Approved**, **Rejected** / failed AddisPay. Idempotent webhooks do not double-pay the same `tx_ref`.

---

## 6. HTTP APIs (whitelist)

Guest (storefront):

- `bismillah_ethiobiz.magala_checkout.get_checkout_options`
- `bismillah_ethiobiz.magala_checkout.get_cart` / `add_to_cart` / `update_cart_qty` / `clear_cart`
- `bismillah_ethiobiz.magala_checkout.place_order`
- `bismillah_ethiobiz.magala_checkout.get_bank_accounts`
- `bismillah_ethiobiz.magala_checkout.submit_bank_reference`
- `bismillah_ethiobiz.magala_checkout.verify_return`
- `bizmarketing.api.addispay.handle_webhook`
- `bizmarketing.api.addispay.initiate_shop_payment` (server-side Magala/DOBiz)

Staff (login):

- `bismillah_ethiobiz.magala_checkout.approve_bank_payment`
- `bismillah_ethiobiz.magala_checkout.reject_bank_payment`

Cart host selector (JS): inject into `#page-cart .page_content`, **never** `li.shopping-cart` (navbar icon is `display:none`). That bug hid payment radios on `/cart`.

---

## 7. Going live (UAT → production AddisPay)

1. Obtain a **production** API key from AddisPay.
2. Magala Checkout Settings: uncheck **Sandbox / UAT Mode**, set **Production Base URL**, paste the live key (or put it on DOBiz SaaS Settings if Magala reuses it).
3. Set webhook URL on the live AddisPay app.
4. Place a **small real** Magala AddisPay order and confirm Magala Shop Payment becomes Approved and Sales Orders exist.
5. Keep a DB backup before the first live cutover (`BackupGenerator`, ignore_files OK).

---

## 8. Persistence checklist (this production)

| Layer | How it survives |
|---|---|
| MariaDB | Magala DocTypes + Settings + Shop Payments (volume on `db-1`) |
| App Python/JS | Git on `BizMarketing` + `bismillah_ethiobiz_ethiobiz` **and** files inside `ethiobiz-custom:latest` |
| Website assets on frontend | Copied to `sites/assets/bismillah_ethiobiz/`; **re-copy after frontend recreate** |
| Container restart | Backend image/apps persist if committed; gunicorn reload on restart is required after `docker cp` |
| New server | Git pull both apps → import DocTypes → `ensure_magala_checkout` → asset flatten → restart backend+frontend → docker commit |

After every Magala hotfix: **git commit + git push** both apps, copy JS/CSS to frontend assets, restart backend, then **docker commit** only when disk &lt; 85%.

If disk is ≥ 85%, **do not commit**. Prune dangling images (`docker image prune`) without deleting n8n/Postgres volumes. Magala code still survives in git even if the image is stale.

---

## 9. Tests

On backend:

```bash
docker exec bismallah_ethiobiz_inshaallah-backend-1 \
  /home/frappe/frappe-bench/env/bin/python \
  /home/frappe/frappe-bench/tests/suites/suite_41_magala_checkout_payments.py
```

Expect **30/30**. Suite 41 covers UAT URLs, DocTypes, COD eligibility, bank approve idempotency, AddisPay webhook helper, success page.

Browser smoke:

1. https://ethiobiz.et/all-products — Add to Cart on a **Products** item (e.g. Enjera).
2. https://ethiobiz.et/cart — Magala Checkout shows AddisPay, Bank Transfer, Cash upon Delivery.
3. https://ethiobiz.et/shop — Add to Cart still works.
4. Desk: Magala Checkout Settings loads; Magala Shop Payment list works.

---

## 10. Incident notes

| Symptom | Likely cause | Fix |
|---|---|---|
| 504 Gateway Time-out | Backend restart / `docker commit` freeze / disk full | Wait for gunicorn; `curl /login`; never commit at 93% disk |
| Payment radios missing on `/cart` | JS mounted on navbar `.shopping-cart` | Use `#page-cart .page_content` (fixed in `magala_checkout.js` v1.1.2+) |
| Empty Magala cart | Buyer used View Details only, or old webshop cart | Use Add to Cart; Magala session cart is independent |
| Full migrate fails | Unrelated app `Document` NameError | Targeted JSON import only |
| Frontend has old JS | Assets not copied / cache | docker cp to frontend `sites/assets/…`, bump `?v=` |

---

## 11. File map

**bizmarketing**

- `bizmarketing/api/addispay.py`
- `bizmarketing/magala_setup.py`
- `bizmarketing/hooks.py` (`after_migrate`)
- `bizmarketing/marketing/doctype/magala_*/`

**bismillah_ethiobiz**

- `bismillah_ethiobiz/magala_checkout.py`
- `bismillah_ethiobiz/public/js/magala_checkout.js`
- `bismillah_ethiobiz/public/css/magala_checkout.css`
- `bismillah_ethiobiz/public/js/all_products_custom.js`
- `bismillah_ethiobiz/www/magala-payment-success.html`
- `bismillah_ethiobiz/www/magala-payment-failed.html`
- `bismillah_ethiobiz/hooks.py`, `api.py`

**Workspace archive**

- `BISMALLAH_Plans_INSHAALLAH/2026-08-26/` (this file + user manual + implementation plan)

---

BISMALLAH. INSHA'ALLAH.
