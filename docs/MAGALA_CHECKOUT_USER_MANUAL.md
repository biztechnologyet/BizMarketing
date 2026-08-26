# Magala Checkout — User Manual

**Site:** https://ethiobiz.et  
**Date:** 2026-08-27  
**Audience:** Shoppers, merchants, and Desk operators who take Magala orders  
**BISMALLAH. INSHA'ALLAH.**

This manual explains how buyers pay for Magala marketplace items using **AddisPay**, **Bank Transfer**, and **Cash upon Delivery**, and how EthioBiz staff confirm those payments.

---

## 1. What Magala Checkout is

Magala Checkout is the payment panel on **https://ethiobiz.et/cart**. It is separate from the older webshop “quotation” cart.

| You want to… | Use |
|---|---|
| Buy a product, food, service, or booking item | **Add to Cart** on Magala, then pay on `/cart` |
| Apply for a job | **Apply Now** (jobs are not sold through cart) |
| Pay a DOBiz ERP subscription | `/dobiz-payment` (not Magala Checkout) |

The Magala cart is stored in your browser session (and your login if you are signed in). The empty picture on `/cart` that says “See past quotations” is the old webshop cart. **Scroll to / look for “Magala Checkout”** on the same page.

---

## 2. How to shop (buyers)

### Step 1 — Browse

Open either:

- https://ethiobiz.et/all-products (Magala Market)
- https://ethiobiz.et/shop (EthioBiz Shop)

Use search, company filter, category chips, grid/list/map as usual.

### Step 2 — Add to Cart

On a product or food card, click **Add to Cart**.  
Jobs show **Apply Now** instead of Add to Cart.

A cart badge (**Cart N**) appears in the header. Click it, or go to https://ethiobiz.et/cart.

### Step 3 — Fill Magala Checkout

On `/cart`, in the **Magala Checkout** box:

1. Confirm your lines and total (ETB).
2. Enter **Full name**, **Email**, and **Phone** (`09…` or `251…`).
3. For Cash upon Delivery, enter a **delivery address**.
4. Choose one payment method (below).
5. Click **Place Order**.

---

## 3. Payment options

### 3.1 AddisPay Payment (cards, Telebirr, CBE Birr, bank apps)

1. Select **AddisPay Payment**.
2. Click **Place Order**.
3. You are sent to the official AddisPay hosted page.
4. Pay with the method AddisPay offers (card, Telebirr, CBE Birr, bank app, etc.).
5. Success returns you to **https://ethiobiz.et/magala-payment-success**.  
   Failure/cancel returns **https://ethiobiz.et/magala-payment-failed**.
6. Keep the on-screen **reference** (`MAGALA-…`). That is your receipt ID.

**UAT / test mode:** the cart may show an **AddisPay UAT** badge. That means EthioBiz is still using AddisPay’s test environment. Do not send real money until staff turn UAT off.

### 3.2 Bank Transfer

1. Select **Bank Transfer**. Settlement accounts (bank name, holder, account number) appear.
2. Click **Place Order**. You receive a **MAGALA-…** reference and the amount to pay.
3. Transfer the **exact amount** to one of the listed accounts. Put the Magala reference in the transfer remark if the bank allows it.
4. On the same cart result screen, enter your **bank slip / reference ID** and click **Submit bank reference**.
5. Wait for EthioBiz accounts staff to **Approve** the payment in Desk. You will not be marked Paid until that confirmation.

Default settlement accounts (can be changed by administrators):

| Bank / wallet | Account | Holder |
|---|---|---|
| Commercial Bank of Ethiopia | 1000236131606 | Hadi Awad |
| Telebirr SuperApp | +251 98 676 7576 | Hadi Awad |
| Bank of Abyssinia | 94784891 | Hadi Awad |

### 3.3 Cash upon Delivery (COD)

1. COD is offered only when **every** cart line is a **product or food** style item (item group names that include fragments such as Products, Food, Dining, Goods). Mixed carts that include services, hotel rooms, courses, or jobs **disable COD**.
2. Enter a **delivery address**.
3. Select **Cash upon Delivery** and **Place Order**.
4. Pay the courier in cash when the goods arrive. The Magala payment stays **Pending / Unpaid** until staff mark it collected if they use Desk follow-up.

---

## 4. After you order

| Method | What you should see | When it is “paid” |
|---|---|---|
| AddisPay | Redirect to AddisPay, then success or failed page | Automatically when AddisPay reports success (webhook or return URL) |
| Bank Transfer | `MAGALA-…` + bank list + slip box | When a Desk user clicks **Approve Payment** |
| COD | Confirmation + `MAGALA-…` | On delivery (cash to courier) |

If AddisPay succeeds but the success page is slow, wait and refresh once. Do not pay twice. The same `tx_ref` is not charged again.

---

## 5. Staff: confirm Bank Transfer (Desk)

1. Sign in to https://ethiobiz.et/app as Accounts Manager, Sales Manager, or System Manager.
2. Awesome Bar: **Magala Shop Payment**.
3. Open the document whose **Tx Ref** matches the buyer’s `MAGALA-…`.
4. Check **bank name**, **reference no**, amount, and the bank statement.
5. **Actions → Approve Payment** (or **Reject Payment** with a reason).

Approve only after money is on the EthioBiz account. Reject if the slip is fake or the amount is wrong.

---

## 6. Staff: Magala Checkout Settings (what buyers see)

Awesome Bar: **Magala Checkout Settings** (single form).

Typical buyer-facing changes:

- Turn **Enable AddisPay / Bank Transfer / Cash upon Delivery** on or off.
- Change labels and descriptions shown on `/cart`.
- Edit the **Bank Accounts** table (bank, account, holder, instructions).
- Change **COD Item Groups** (comma-separated fragments) if more groups should allow COD.
- Change **Job Item Groups** so those listings stay Apply Now.

Save the form. Buyers see the new labels on the next cart load (hard-refresh if needed).

---

## 7. Troubleshooting (buyers)

| Symptom | What to do |
|---|---|
| `/cart` looks empty (white card, “See past quotations”) | Hard-refresh (`Ctrl+F5`). Look for **Magala Checkout** on the same page. Add items via **Add to Cart**, not only “View”. |
| No payment radios | Hard-refresh. If still missing, tell support; staff will check Magala Checkout Settings (all methods may be disabled). |
| COD is greyed out | Remove services/jobs from the Magala cart, or pay with AddisPay / Bank Transfer. |
| AddisPay page error | Check phone format and that a UAT/live key is configured. Try again once. |
| Paid on AddisPay but cart still empty | That is expected: the Magala cart is cleared after a successful place-order. Keep `MAGALA-…`. |
| Job has no Add to Cart | Intended. Use **Apply Now**. |

---

## 8. Support

- Website: https://ethiobiz.et  
- Helpdesk / Walta: https://ethiobiz.et/helpdesk  
- Quote a **MAGALA-…** reference in every ticket.

BISMALLAH. INSHA'ALLAH.
