# © 2021 Solvos Consultoría Informática (<http://www.solvos.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_currency_id = fields.Many2one(
        related="purchase_id.currency_id",
        readonly=True,
        string="Currency",
        related_sudo=True
    )
    purchase_amount_untaxed = fields.Monetary(
        currency_field="purchase_currency_id",
        compute="_compute_purchase_amount_all",
        compute_sudo=True
    )
    purchase_amount_tax = fields.Monetary(
        currency_field="purchase_currency_id",
        compute="_compute_purchase_amount_all",
        compute_sudo=True
    )
    purchase_amount_total = fields.Monetary(
        currency_field="purchase_currency_id",
        compute="_compute_purchase_amount_all",
        compute_sudo=True
    )

    def _compute_purchase_amount_all(self):
        """This is computed with sudo for avoiding problems if you don't have
        access to purchase orders (stricter warehouse users, inter-company
        records...).
        """
        for pick in self:
            round_curr = pick.purchase_id.currency_id.round
            purchase_amount_tax = 0.0
            for tax_group in pick.get_purchase_taxes_values().values():
                purchase_amount_tax += round_curr(tax_group["amount"])
            purchase_amount_untaxed = sum(
                line.purchase_price_subtotal for line in pick.move_line_ids
            )
            pick.update(
                {
                    "purchase_amount_untaxed": purchase_amount_untaxed,
                    "purchase_amount_tax": purchase_amount_tax,
                    "purchase_amount_total": purchase_amount_untaxed + purchase_amount_tax,
                }
            )

    def get_purchase_taxes_values(self):
        tax_grouped = {}
        for line in self.move_line_ids:
            for tax in line.purchase_line.taxes_id:
                tax_id = tax.id
                if tax_id not in tax_grouped:
                    tax_grouped[tax_id] = {"base": line.purchase_price_subtotal, "tax": tax}
                else:
                    tax_grouped[tax_id]["base"] += line.purchase_price_subtotal
        for tax_id, tax_group in tax_grouped.items():
            tax_grouped[tax_id]["amount"] = tax_group["tax"].compute_all(
                tax_group["base"], self.purchase_id.currency_id
            )["taxes"][0]["amount"]
        return tax_grouped
