def unread_notifications(request):
    if request.user.is_authenticated:
        return {
            'unread_count': request.user.notifications.filter(is_read=False).count()
        }
    return {}


from .models import Message, Chat


def unread_chats(request):
    if not request.user.is_authenticated:
        return {}

    unread_count = Message.objects.filter(
        chat__order__order_items__seller=request.user,
        is_read=False
    ).exclude(
        sender=request.user
    ).count()

    return {'unread_chats_count': unread_count}