frappe.ui.form.on("Magala Checkout Settings", {
    refresh(frm) {
        frm.add_custom_button(__("Test AddisPay Connection"), () => {
            frappe.call({
                method: "bizmarketing.api.addispay.test_connection",
                freeze: true,
                freeze_message: __("Calling AddisPay UAT/Prod…"),
                callback(r) {
                    const m = r.message || {};
                    frappe.msgprint({
                        title: __("AddisPay"),
                        indicator: m.ok ? "green" : "orange",
                        message: __(m.message || JSON.stringify(m)),
                    });
                },
            });
        });
        frm.add_custom_button(__("Open Magala Cart"), () => {
            window.open("/cart", "_blank");
        });
    },
});
