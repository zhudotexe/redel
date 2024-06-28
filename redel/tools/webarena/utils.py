# ==== adapted from webarena ====
from browser_env.env_config import URL_MAPPINGS


def map_url_to_real(url: str) -> str:
    """Map the urls to their real world counterparts"""
    for i, j in URL_MAPPINGS.items():
        if i in url:
            url = url.replace(i, j)
    return url


def map_url_to_local(url: str) -> str:
    """Map the urls to their local counterparts"""
    for i, j in URL_MAPPINGS.items():
        if j in url:
            url = url.replace(j, i)
        # https
        if j.replace("http", "https") in url:
            url = url.replace(j.replace("http", "https"), i)
    return url
