from leadscraper.listing import extract_items

HTML = """
<article class="product_pod">
  <h3><a href="a-book.html" title="A Book">A Bo...</a></h3>
  <p class="price_color">£10.00</p>
</article>
<article class="product_pod">
  <h3><a href="b-book.html" title="B Book">B Bo...</a></h3>
  <p class="price_color">£12.50</p>
</article>
"""

CFG = {
    "item_selector": "article.product_pod",
    "static": {},
    "fields": {
        "title": {"selector": "h3 a", "attr": "title"},
        "price": {"selector": ".price_color"},
        "link": {"selector": "h3 a", "attr": "href", "absolute": True},
    },
}


def test_extract_items():
    rows = extract_items(HTML, CFG, "https://books.toscrape.com/catalogue/page-1.html")
    assert len(rows) == 2
    assert rows[0]["title"] == "A Book"
    assert rows[1]["price"] == "£12.50"
    assert rows[0]["link"] == "https://books.toscrape.com/catalogue/a-book.html"
