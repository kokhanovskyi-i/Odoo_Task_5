import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HrHospitalDisease(models.Model):
    _name = 'hr.hospital.disease'
    _description = 'Disease'
    _parent_name = 'parent_id'
    _parent_store = True
    _order = 'parent_path, name'

    code = fields.Char(
        string='Code',
        required=True,
    )

    name = fields.Char(
        string='Name',
        required=True,
    )

    display_name = fields.Char(
        compute='_compute_display_name',
        recursive=True,
    )

    parent_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        string='Parent Disease',
        index=True,
        ondelete='restrict',
    )

    child_ids = fields.One2many(
        comodel_name='hr.hospital.disease',
        inverse_name='parent_id',
        string='Child Diseases',
    )

    parent_path = fields.Char(
        index=True,
    )

    @api.constrains('parent_id')
    def _check_parent_id(self):
        for disease in self:
            if disease._has_cycle():
                raise ValidationError('Disease hierarchy cannot be recursive.')

    @api.depends('name', 'parent_id.display_name')
    def _compute_display_name(self):
        for disease in self:
            disease.display_name = disease._get_complete_name()

    def _get_complete_name(self):
        self.ensure_one()

        names = []
        current = self

        while current:
            names.append(current.name or '')
            current = current.parent_id

        return ' / '.join(reversed(names))
