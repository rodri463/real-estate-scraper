import requests
import pandas as pd
from bs4 import BeautifulSoup
import json
from datetime import datetime
import random
import time
import aiohttp
import asyncio

class IdealistaScraperTorrevieja:
    def __init__(self):
        self.base_url = "https://www.idealista.com"
        self.zones = {
            'playa_del_cura': '/venta-viviendas/torrevieja-alicante/playa-del-cura/',
            'centro': '/venta-viviendas/torrevieja-alicante/centro/',
            'acequion': '/venta-viviendas/torrevieja-alicante/acequion/',
            'playa_los_locos': '/venta-viviendas/torrevieja-alicante/playa-los-locos/'
        }
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]

    def get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'es-ES,es;q=0.9'
        }

    def parse_property(self, item):
        try:
            price = item.find('span', {'class': 'item-price'})
            size = item.find('span', {'class': 'item-detail'})
            location = item.find('a', {'class': 'item-link'})
            
            return {
                'price': float(''.join(filter(str.isdigit, price.text))) if price else None,
                'size': float(''.join(filter(str.isdigit, size.text.split('m')[0]))) if size else None,
                'location': location.text.strip() if location else None,
                'date_scraped': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error parsing property: {str(e)}")
            return None

    async def scrape_torrevieja(self):
        properties = []
        async with aiohttp.ClientSession() as session:
            for zone, url_path in self.zones.items():
                url = f"{self.base_url}{url_path}"
                try:
                    async with session.get(url, headers=self.get_headers()) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            for item in soup.find_all('div', {'class': 'item-info-container'}):
                                if prop := self.parse_property(item):
                                    prop['zone'] = zone
                                    properties.append(prop)
                            await asyncio.sleep(random.uniform(3, 5))
                except Exception as e:
                    print(f"Error scraping zone {zone}: {str(e)}")
        return properties

async def main():
    scraper = IdealistaScraperTorrevieja()
    properties = await scraper.scrape_torrevieja()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save raw data
    with open(f'data/torrevieja_{timestamp}.json', 'w') as f:
        json.dump(properties, f)
    
    # Analysis
    df = pd.DataFrame(properties)
    df['price_per_m2'] = df['price'] / df['size']
    
    analysis = {
        'promedio_por_zona': df.groupby('zone')['price_per_m2'].mean().to_dict(),
        'total_propiedades': len(df),
        'rango_precios': {
            'min': df['price'].min(),
            'max': df['price'].max(),
            'promedio': df['price'].mean()
        }
    }
    
    with open(f'data/torrevieja_analysis_{timestamp}.json', 'w') as f:
        json.dump(analysis, f)

if __name__ == "__main__":
    asyncio.run(main())