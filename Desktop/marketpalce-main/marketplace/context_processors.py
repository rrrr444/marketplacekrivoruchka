def unread_notifications(request):
    if request.user.is_authenticated:
        return {
            'unread_count': request.user.notifications.filter(is_read=False).count()
        }
    return {}