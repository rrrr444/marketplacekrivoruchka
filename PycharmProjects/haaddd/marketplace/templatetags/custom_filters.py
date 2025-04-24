from django import template

register = template.Library()

@register.filter(name='intcomma')
def intcomma(value, decimal_places=2):
    """Форматирует число с разделителями тысяч"""
    try:
        num = float(value)
        return "{:,.{prec}f}".format(num, prec=decimal_places).replace(",", " ").replace(".", ",")
    except (ValueError, TypeError):
        return str(value)

@register.filter
def multiply(value, arg):
    """Умножение значения на аргумент"""
    return value * arg

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''
from django import template



@register.filter
def sum_items(items):
    return sum(item.product.price * item.quantity for item in items)