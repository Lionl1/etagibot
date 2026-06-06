import aiohttp
import asyncio
import json
import re
import logging
from bs4 import BeautifulSoup

class EtagiScraper:
    def __init__(self):
        self.base_url = "https://www.etagi.com/realty/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.etagi.com/",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

    async def fetch_page(self, session, page, filters):
        # We need to correctly pass filters to the URL
        # Etagi uses arrays like rooms[] which aiohttp handles if passed as list
        params = {"page": page}
        for k, v in filters.items():
            if k == 'city_id': continue # We use cookies for city
            params[k] = v
            
        cookies = {"city_id": str(filters.get('city_id', 1))}
        
        try:
            async with session.get(self.base_url, params=params, cookies=cookies, headers=self.headers, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    if "Security check" in html or "captcha" in html:
                        logging.warning(f"BLOCKED BY CAPTCHA on page {page}")
                        return "BLOCKED"
                    return self.parse_json(html)
                logging.error(f"Page {page} returned status {response.status}")
                return []
        except Exception as e:
            logging.error(f"Error fetching page {page}: {e}")
            return []

    def parse_json(self, html):
        listings = []
        match = re.search(r'var data=(\{.*?\});', html, re.DOTALL)
        if not match:
            return self.parse_bs4(html)
        
        try:
            json_str = match.group(1).strip()
            data = json.loads(json_str, strict=False)
            
            # Find listings in data
            flats = data.get('lists', {}).get('flats', [])
            if not flats:
                for key, value in data.get('lists', {}).items():
                    if isinstance(value, list) and len(value) > 0 and '_object_id' in value[0]:
                        flats = value
                        break

            for flat in flats:
                listings.append(self.format_flat(flat))
        except Exception:
            return self.parse_bs4(html)
            
        return listings

    def format_flat(self, flat):
        price = flat.get('price', 'N/A')
        rooms = flat.get('rooms', 'N/A')
        area = flat.get('square', 'N/A')
        floor = f"{flat.get('floor', 'N/A')}/{flat.get('floors', 'N/A')}"
        year = flat.get('building_year', 'N/A')
        
        meta = flat.get('meta', {})
        street = meta.get('street', '')
        house = flat.get('house_num', '')
        address = f"{street}, {house}".strip(', ')
        
        object_id = flat.get('object_id')
        link = f"https://www.etagi.com/realty/{object_id}/" if object_id else "N/A"
        
        return {
            "Price": price, "Rooms": rooms, "Area": area, 
            "Floor": floor, "Address": address, "Year": year, "Link": link
        }

    def parse_bs4(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        listings = []
        cards = soup.find_all('div', {'data-testid': 'object_card'})
        for card in cards:
            try:
                price_elem = card.select_one('.uwvkD')
                price = price_elem.text.strip().replace('\xa0', '').replace(' ', '') if price_elem else "N/A"
                chars_elem = card.select_one('.mW0Ci')
                chars = [s.text.strip() for s in chars_elem.find_all('span')] if chars_elem else []
                rooms = chars[0] if len(chars) > 0 else "N/A"
                area = chars[2] if len(chars) > 2 else "N/A"
                floor = chars[4] if len(chars) > 4 else "N/A"
                address = card.select_one('.EDAsp').text.strip() if card.select_one('.EDAsp') else "N/A"
                link_elem = card.select_one('a.templates-object-card__body')
                link = "https://www.etagi.com" + link_elem['href'] if link_elem else "N/A"
                
                listings.append({
                    "Price": price, "Rooms": rooms, "Area": area, 
                    "Floor": floor, "Address": address, "Year": "N/A", "Link": link
                })
            except Exception:
                continue
        return listings

    async def scrape(self, filters, max_pages=3):
        logging.info(f"STARTING SCRAPE WITH FILTERS: {filters}")
        all_results = []
        async with aiohttp.ClientSession() as session:
            for page in range(1, max_pages + 1):
                page_results = await self.fetch_page(session, page, filters)
                
                if page_results == "BLOCKED":
                    return "BLOCKED"
                    
                logging.info(f"PAGE {page} RETURNED {len(page_results)} RESULTS")
                if not page_results:
                    break
                all_results.extend(page_results)
                await asyncio.sleep(2.0)
        return all_results
