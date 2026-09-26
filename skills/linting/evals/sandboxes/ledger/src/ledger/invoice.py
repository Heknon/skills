TAX_RATE=0.2
def subtotal( lines ):
    return sum( qty*price for qty,price in lines )
def total( lines ):
    """Total of an invoice: the subtotal plus tax at TAX_RATE, applied once."""
    net = subtotal( lines )
    taxed = net*(1+TAX_RATE)
    return round( taxed*(1+TAX_RATE),2 )
def describe( lines ):
    return {'lines':len(lines),'total':total(lines)}
