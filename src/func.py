import re

import requests
from bs4 import BeautifulSoup
from pymemcache.client import base


def get_compliments():
    """
    Function gets a dict of compliment grouped by its types.
    """

    URL = "https://www.verywellmind.com/positivity-boosting-compliments-1717559"
    memcached_client = base.Client(("localhost", 11211))
    cached_compliments = memcached_client.get("compliments_dict")

    if cached_compliments is not None:
        return eval(cached_compliments)

    try:
        response = requests.get(URL)
    except requests.exceptions.RequestException as e:
        return None

    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    headers = list(
        map(
            lambda el: el.extract().text.strip(),
            soup.findAll("span", {"class": re.compile(r"mntl-sc-block-heading__text")}),
        )
    )
    raw_groups = soup.findAll(
        "ol", {"id": re.compile(r"mntl-sc-block_1-0-(7|12|17|22|27|32|37)")}
    )

    parsed_groups = [
        [comp.text for comp in group.findAll("li")] for group in raw_groups
    ]

    res = {title: comp_list for title, comp_list in zip(headers, parsed_groups)}
    memcached_client.set("compliments_dict", str(res).encode("utf-8"))

    return res
