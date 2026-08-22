from frappe.cache_manager import global_cache_keys, bench_cache_keys

import frappe

frappe.init(site="ethiobiz.et", sites_path="/home/frappe/frappe-bench/sites")
frappe.set_user("Administrator")
frappe.connect()

print("purging", len(global_cache_keys), "global +", len(bench_cache_keys),
      "bench keys")
for k in list(global_cache_keys) + list(bench_cache_keys):
    try:
        frappe.cache.delete_value(k)
    except Exception:
        pass
print("PURGED")

frappe.setup_module_map(include_all_apps=True)
ma_t = dict(frappe.local.module_app or {})
print("TRUE map:", len(ma_t), "| healthcare:", ma_t.get("healthcare"),
      "| ethiobiz_theme:", ma_t.get("ethiobiz_theme"))

frappe.setup_module_map(include_all_apps=False)
ma_f = dict(frappe.local.module_app or {})
print("FALSE map:", len(ma_f), "| healthcare:", ma_f.get("healthcare"))

assert ma_t.get("healthcare") == "healthcare", "TRUE map broken"
assert ma_f.get("healthcare") == "healthcare", "FALSE map broken"
print("BOTH_MAPS_OK")

from frappe.model.base_document import get_controller

get_controller("Healthcare Service Unit")
print("CONTROLLER_OK")
frappe.db.commit()
