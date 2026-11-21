from django.utils.http import url_has_allowed_host_and_scheme


def get_safe_next_url(request, default: str) -> str:
    """Return the POSTed `next` URL if it points to this site, otherwise `default`."""
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return default
