//End date validation on End date change
var end_date_start_date_validation = function (frm, cdt, cdn) {
    var d = locals[cdt][cdn];
    if (d.end_date && d.start_date) {
        if (d.end_date < d.start_date) {
            msgprint('End date is before Start date, please amend to continue');
            frappe.validated = false;
        }
    } else if (d.days && !d.end_date && !d.start_date) {
        msgprint('Start Date and End Date are blank, please amend to continue');
        frappe.validated = false;
    }
}

//Days Calculation
var days_calculation = function (frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    if (row.reservation_option === "Nights") { //For Nights
        if (row.end_date >= row.start_date) { //Days Calculation on End date change
            frappe.model.set_value(cdt, cdn, 'days', frappe.datetime.get_day_diff(row.end_date, row.start_date));
            frm.refresh_field("days");
        }
    } else {
        if (row.end_date >= row.start_date) { //Days Calculation on End date change
            //Days Calculation on End date change
            var daydiff = frappe.datetime.get_day_diff(row.end_date, row.start_date);
            daydiff = daydiff + 1;
            frappe.model.set_value(cdt, cdn, 'days', daydiff);
            frm.refresh_field("days");
        }
    }
}

//End Date Calculation-Not in use, creates cyclic calculations
var end_date_calculation = function (frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    if (row.reservation_option === "Nights") { //For Nights
        if (row.days && row.start_date && !row.end_date) { //End date Calculation on Days change
            frappe.model.set_value(cdt, cdn, 'end_date', frappe.datetime.add_days(row.start_date, row.days));
            frm.refresh_field("end_date");
        }
    } else {
        if (row.days && row.start_date) { //End date Calculation on Days change
            var newdays = row.days + 1;
            frappe.model.set_value(cdt, cdn, 'end_date', frappe.datetime.add_days(row.start_date, newdays));
            frm.refresh_field("end_date");
        }
    }
}

//For Childdoctype
frappe.ui.form.on("Opportunity Item", "item_code", function (frm, cdt, cdn) {
    //Fetch reservation_option from item 
    var d = locals[cdt][cdn];
    frappe.db.get_value("Item", { "name": d.item_code }, "reservation_option", function (value) {
        d.reservation_option = value.reservation_option;
    });
})

frappe.ui.form.on("Opportunity Item", "end_date", function (frm, cdt, cdn) {
    //End date validation on End date change
    end_date_start_date_validation(frm, cdt, cdn);
    //Days or Dates Calculation
    days_calculation(frm, cdt, cdn);
})

frappe.ui.form.on("Opportunity Item", "start_date", function (frm, cdt, cdn) {
    //End date validation on End date change
    end_date_start_date_validation(frm, cdt, cdn);
    //Days or Dates Calculation
    days_calculation(frm, cdt, cdn);
})

//frappe.ui.form.on("Sales Order Item", "days", function (frm, cdt, cdn) {
    //End date validation on End date change
    //end_date_start_date_validation(frm, cdt, cdn);
    //Days or Dates Calculation
    //end_date_calculation(frm, cdt, cdn);
//})
