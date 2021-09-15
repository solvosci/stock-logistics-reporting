# © 2021 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    purchase_line = fields.Many2one(
        related="move_id.purchase_line_id",
        readonly=True,
        string="Related order line"
    )
    purchase_currency_id = fields.Many2one(
        related="purchase_line.currency_id",
        readonly=True,
        string="Purchase Currency"
    )
    purchase_tax_id = fields.Many2many(
        related="purchase_line.taxes_id",
        readonly=True,
        string="Purchase Tax"
    )
    purchase_price_unit = fields.Float(
        related="purchase_line.price_unit",
        readonly=True,
        string="Purchase price unit"
    )
    purchase_discount = fields.Float(
        related="purchase_line.discount",
        readonly=True,
        string="Purchase discount (%)"
    )
    purchase_tax_description = fields.Char(
        compute="_compute_purchase_order_line_fields",
        string="Tax Description",
        compute_sudo=True
    )
    purchase_price_subtotal = fields.Monetary(
        currency_field="purchase_currency_id",
        compute="_compute_purchase_order_line_fields",
        string="Price subtotal",
        compute_sudo=True
    )
    purchase_price_tax = fields.Float(
        compute="_compute_purchase_order_line_fields",
        string="Taxes",
        compute_sudo=True
    )
    purchase_price_total = fields.Monetary(
        currency_field="purchase_currency_id",
        compute="_compute_purchase_order_line_fields",
        string="Total",
        compute_sudo=True
    )

    def _compute_purchase_order_line_fields(self):
        for line in self:
            purchase_line = line.purchase_line
            price_unit = (
                purchase_line.price_subtotal / purchase_line.product_uom_qty
                if purchase_line.product_uom_qty
                # else purchase_line.price_reduce
                else purchase_line._get_discounted_price_unit()
            )
            taxes = line.purchase_tax_id.compute_all(
                price_unit=price_unit,
                currency=line.purchase_currency_id,
                quantity=line.qty_done or line.product_qty,
                product=line.product_id,
                partner=purchase_line.order_id.dest_address_id,
            )
            if purchase_line.company_id.tax_calculation_rounding_method == (
                "round_globally"
            ):
                price_tax = sum(t.get("amount", 0.0) for t in taxes.get("taxes", []))
            else:
                price_tax = taxes["total_included"] - taxes["total_excluded"]
            line.update(
                {
                    "purchase_tax_description": ", ".join(
                        t.name or t.description for t in line.purchase_tax_id
                    ),
                    "purchase_price_subtotal": taxes["total_excluded"],
                    "purchase_price_tax": price_tax,
                    "purchase_price_total": taxes["total_included"],
                }
            )
