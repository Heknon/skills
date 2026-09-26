# orders

The orders API. `POST /orders` prices an order, checks the customer's
credit limit and saves it. A nightly job that imports orders from the
shop's CSV export is planned and will need the same pricing and credit
rules without HTTP.
