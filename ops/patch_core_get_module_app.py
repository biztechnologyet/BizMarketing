import re
import shutil
import time

P = "/home/frappe/frappe-bench/apps/frappe/frappe/modules/utils.py"
src = open(P).read()

if "ETHIOBIZ HOTFIX" in src:
    print("ALREADY_PATCHED")
else:
    old = '''def get_module_app(module: str) -> str:
	app = frappe.local.module_app.get(scrub(module))
	if app is None:
		frappe.throw(_("Module {} not found").format(module), exc=frappe.DoesNotExistError)
	return app
'''
    new = '''def get_module_app(module: str) -> str:
	app = frappe.local.module_app.get(scrub(module))
	if app is None:
		# ETHIOBIZ HOTFIX (ANFRG-26-00063 follow-up): poisoned/stale
		# global module-map cache made valid modules vanish mid-boot,
		# breaking Company/trial provisioning ("Module Healthcare not
		# found"). Fall back to the authoritative Module Def record.
		try:
			app = frappe.db.get_value("Module Def", scrub(module), "app_name") \
				or frappe.db.get_value("Module Def", {"module_name": module}, "app_name")
			if app:
				frappe.local.module_app[scrub(module)] = app
		except Exception:
			app = None
	if app is None:
		frappe.throw(_("Module {} not found").format(module), exc=frappe.DoesNotExistError)
	return app
'''
    assert old in src, "target block not found - aborting"
    ts = time.strftime("%Y%m%d-%H%M%S")
    shutil.copy(P, P + ".bak." + ts)
    open(P, "w").write(src.replace(old, new))
    print("PATCHED, backup:", P + ".bak." + ts)

import py_compile

py_compile.compile(P, doraise=True)
print("COMPILE_OK")
