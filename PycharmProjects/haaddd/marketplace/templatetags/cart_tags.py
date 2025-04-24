from django import template

register = template.Library()

@register.filter
def group_by_seller(items):
    sellers = {}
    for item in items:
        seller = item.product.seller
        if seller not in sellers:
            sellers[seller] = []
        sellers[seller].append(item)
    return sellers.items()