import json

from scraper import EtagiScraper


def page_with_data(data):
    return f"<html><script>var data={json.dumps(data, ensure_ascii=False)};</script></html>"


FLAT = {
    "object_id": 123,
    "price": 5_500_000,
    "rooms": 2,
    "square": 54.3,
    "floor": 4,
    "floors": 9,
    "building_year": 2015,
    "house_num": "12",
    "meta": {"street": "ул. Республики"},
}


def test_parse_json_reads_flats_list():
    listings = EtagiScraper().parse_json(page_with_data({"lists": {"flats": [FLAT]}}))
    assert listings == [
        {
            "Price": 5_500_000,
            "Rooms": 2,
            "Area": 54.3,
            "Floor": "4/9",
            "Address": "ул. Республики, 12",
            "Year": 2015,
            "Link": "https://www.etagi.com/realty/123/",
        }
    ]


def test_parse_json_finds_listings_under_other_key():
    other = dict(FLAT, _object_id=123)
    listings = EtagiScraper().parse_json(page_with_data({"lists": {"flats": [], "objects": [other]}}))
    assert [item["Link"] for item in listings] == ["https://www.etagi.com/realty/123/"]


def test_format_flat_handles_missing_fields():
    flat = EtagiScraper().format_flat({})
    assert flat["Address"] == ""
    assert flat["Link"] == "N/A"
    assert flat["Floor"] == "N/A/N/A"


def test_falls_back_to_html_cards():
    html = """
    <div data-testid="object_card">
      <a class="templates-object-card__body" href="/realty/777/"></a>
      <div class="uwvkD">4 200 000</div>
      <div class="mW0Ci"><span>1</span><span>·</span><span>38</span><span>·</span><span>3/5</span></div>
      <div class="EDAsp">ул. Мира, 1</div>
    </div>
    """
    listings = EtagiScraper().parse_json(html)
    assert listings == [
        {
            "Price": "4200000",
            "Rooms": "1",
            "Area": "38",
            "Floor": "3/5",
            "Address": "ул. Мира, 1",
            "Year": "N/A",
            "Link": "https://www.etagi.com/realty/777/",
        }
    ]


def test_no_listings_on_unknown_page():
    assert EtagiScraper().parse_json("<html><body>nothing</body></html>") == []
