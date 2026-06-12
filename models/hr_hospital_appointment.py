import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrHospitalAppointment(models.Model):
    _name = "hr.hospital.appointment"
    _description = "Hospital appointment"
    _rec_name = "planned_datetime"
    _order = "planned_datetime desc, id desc"

    status = fields.Selection(
        selection=[
            ("planned", "Заплановано"),
            ("done", "Завершено"),
            ("cancelled", "Скасовано"),
        ],
        string="Visit Status",
        default="planned",
        required=True,
    )

    planned_datetime = fields.Datetime(
        string="Planned Date and Time",
        default=fields.Datetime.now,
        required=True,
    )

    visit_datetime = fields.Datetime(
        string="Visit Date and Time",
    )

    doctor_id = fields.Many2one(
        comodel_name="hr.hospital.doctor",
        string="Doctor",
        required=True,
    )

    patient_id = fields.Many2one(
        comodel_name="hr.hospital.patient",
        string="Patient",
        required=True,
    )

    summary = fields.Html(
        string="Summary",
    )

    disease_id = fields.Many2one(
        comodel_name="hr.hospital.disease",
        string="Disease",
    )

    same_disease_visit_count = fields.Integer(
        string="Same Disease Visits",
        compute="_compute_same_disease_visit_count",
    )

    active = fields.Boolean(
        string="Active",
        default=True,
    )

    def write(self, vals):
        protected_fields = {
            "planned_datetime",
            "visit_datetime",
            "doctor_id",
        }

        if protected_fields.intersection(vals):
            finished_appointments = self.filtered(
                lambda appointment: appointment.status == "done"
            )
            if finished_appointments:
                raise UserError(
                    "You cannot change date, time or doctor for a completed visit."
                )

        if vals.get("active") is False:
            finished_appointments = self.filtered(
                lambda appointment: appointment.status == "done"
            )
            if finished_appointments:
                raise UserError("You cannot archive completed visits.")

        return super().write(vals)

    def unlink(self):
        finished_appointments = self.filtered(
            lambda appointment: appointment.status == "done"
        )
        if finished_appointments:
            raise UserError("You cannot delete completed visits.")

        return super().unlink()

    @api.depends("disease_id")
    def _compute_same_disease_visit_count(self):
        for appointment in self:
            if appointment.disease_id:
                appointment.same_disease_visit_count = self.search_count(
                    [
                        ("disease_id", "=", appointment.disease_id.id),
                    ]
                )
            else:
                appointment.same_disease_visit_count = 0

    def action_view_same_disease_visits(self):
        self.ensure_one()

        domain = [("id", "=", False)]
        context = {}

        if self.disease_id:
            domain = [("disease_id", "=", self.disease_id.id)]
            context = {
                "default_disease_id": self.disease_id.id,
            }

        return {
            "type": "ir.actions.act_window",
            "name": "Visits With Same Disease",
            "res_model": "hr.hospital.appointment",
            "view_mode": "list,form",
            "domain": domain,
            "context": context,
        }
