// Copyright (c) 2022, Navari Limited and contributors
// For license information, please see license.txt

//Issue Allocation
frappe.ui.form.on('Issue Allocation', {
	onload: function (frm) {
        cur_frm.set_query("issue_type", "items", function(doc, cdt, cdn) {
            var d = locals[cdt][cdn];
            return {
                "filters": {
                    "department": d.department
                }
            };
        });
    },
    after_submit: function (frm) {
        send_sms(frm);
    }
})

//For Childdoctype
frappe.ui.form.on("Issue Allocation Item", "department", function (frm, cdt, cdn) {
    var d = locals[cdt][cdn];
    frappe.db.get_value("Department", { "name": d.department }, "hod", function (value) {
        d.hod = value.hod;
        if (d.hod)
            frappe.model.with_doc('Employee', d.hod, function () {
                let emp = frappe.model.get_doc('Employee', d.hod);
                d.hod_user_id = emp.user_id;
                d.mobile_no = emp.cell_number;
            });
    });
})

var send_sms = function (frm) {
    $.each(frm.doc.items, function (i, row) {
        if (row.mobile_no) {
            var message = ' Issue Type: ' + row.issue_type + ' @ ' + frm.doc.location + ' -Priority: ' + row.priority;
            frappe.call({
                method: "frappe.core.doctype.sms_settings.sms_settings.send_sms",
                args: {
                    receiver_list: [row.mobile_no],
                    msg: message,
                },
                callback: function (r) {
                    if (r.exc) {
                        msgprint(r.exc);
                        return;
                    }
                }
            });
        }
    });
};
