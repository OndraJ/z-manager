from django.conf import settings


def hotel_links(request):
    return {"hotel_links": settings.HOTEL_LINKS}
