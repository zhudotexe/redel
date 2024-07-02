# ==== adapted from webarena ====
from browser_env.env_config import GITLAB, HOMEPAGE, MAP, REDDIT, SHOPPING, SHOPPING_ADMIN, WIKIPEDIA

# pretty much the same as the provided one in webarena, but accounting for www.
URL_MAPPINGS = (
    (REDDIT, "http://reddit.com"),
    (REDDIT, "http://www.reddit.com"),
    (SHOPPING, "http://onestopmarket.com"),
    (SHOPPING, "http://www.onestopmarket.com"),
    (SHOPPING_ADMIN, "http://luma.com/admin"),
    (SHOPPING_ADMIN, "http://www.luma.com/admin"),
    (GITLAB, "http://gitlab.com"),
    (GITLAB, "http://www.gitlab.com"),
    (WIKIPEDIA, "http://wikipedia.org"),
    (WIKIPEDIA, "http://www.wikipedia.org"),
    (MAP, "http://openstreetmap.org"),
    (MAP, "http://www.openstreetmap.org"),
    (HOMEPAGE, "http://homepage.com"),
    (HOMEPAGE, "http://www.homepage.com"),
)


def map_url_to_real(url: str) -> str:
    """Map the urls to their real world counterparts"""
    for i, j in URL_MAPPINGS:
        if i in url:
            url = url.replace(i, j)
        # https
        if i.replace("https", "http") in url:
            url = url.replace(i.replace("https", "http"), j)
    return url


def map_url_to_local(url: str) -> str:
    """Map the urls to their local counterparts"""
    for i, j in URL_MAPPINGS:
        if j in url:
            url = url.replace(j, i)
        # https
        if j.replace("http", "https") in url:
            url = url.replace(j.replace("http", "https"), i)
    return url
