import asyncio
import logging
import re
from typing import List, Dict
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.dialects.postgresql import insert

from database import AsyncSessionLocal
from models import Car

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# User-Agent to appear as a real browser
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "https://www.carsensor.net"
SEARCH_URL = "https://www.carsensor.net/usedcar/search.php"

# Color mapping from Japanese to English
COLOR_MAP = {
    '白': 'White',
    'ホワイト': 'White',
    '黒': 'Black',
    'ブラック': 'Black',
    '銀': 'Silver',
    'シルバー': 'Silver',
    '赤': 'Red',
    'レッド': 'Red',
    '青': 'Blue',
    'ブルー': 'Blue',
    '緑': 'Green',
    'グリーン': 'Green',
    '黄': 'Yellow',
    'イエロー': 'Yellow',
    '灰': 'Gray',
    'グレー': 'Gray',
    '茶': 'Brown',
    'ブラウン': 'Brown',
    'パール': 'Pearl',
    'ゴールド': 'Gold',
}


async def scrape_carsensor() -> List[Dict]:
    """
    Scrape car listings from carsensor.net using the actual HTML structure
    
    Returns:
        List of dictionaries containing car data
    """
    logger.info("Starting scrape of carsensor.net...")
    
    cars_data = []
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            }
            
            # Fetch the search results page
            response = await client.get(SEARCH_URL, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Successfully fetched page (status: {response.status_code})")
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all car cassettes using the actual class names
            cassettes = soup.find_all('div', class_='cassette')
            
            logger.info(f"Found {len(cassettes)} car listings")
            
            for idx, cassette in enumerate(cassettes):
                try:
                    # Extract brand - it's in a <p> tag before the title
                    brand_tag = cassette.find('p', string=lambda text: text and len(text.strip()) > 0 and text.strip() in [
                        'トヨタ', 'ホンダ', '日産', 'マツダ', 'スバル', 'スズキ', '三菱', 'ダイハツ', 
                        'レクサス', 'Toyota', 'Honda', 'Nissan', 'Mazda', 'Subaru', 'Suzuki'
                    ])
                    
                    if not brand_tag:
                        # Try to find any <p> tag in carInfoContainer that might be brand
                        car_info = cassette.find('div', class_='cassetteMain__carInfoContainer')
                        if car_info:
                            brand_tag = car_info.find('p')
                    
                    brand = brand_tag.get_text(strip=True) if brand_tag else 'Honda'
                    
                    # Normalize brand name to English
                    brand_map = {
                        'トヨタ': 'Toyota', 'ホンダ': 'Honda', '日産': 'Nissan',
                        'マツダ': 'Mazda', 'スバル': 'Subaru', 'スズキ': 'Suzuki',
                        '三菱': 'Mitsubishi', 'ダイハツ': 'Daihatsu', 'レクサス': 'Lexus'
                    }
                    brand = brand_map.get(brand, brand)
                    
                    # Extract model from title
                    title_tag = cassette.find('h3', class_='cassetteMain__title')
                    if not title_tag:
                        continue
                    
                    title_link = title_tag.find('a')
                    model_text = title_link.get_text(strip=True) if title_link else title_tag.get_text(strip=True)
                    
                    # Clean up model name (remove extra info after multiple spaces)
                    model = model_text.split()[0] if model_text else 'Unknown'
                    
                    # Extract link
                    link_href = title_link.get('href') if title_link else None
                    if not link_href:
                        continue
                    
                    link = urljoin(BASE_URL, link_href)
                    
                    # Extract year from specList
                    year = 2020  # Default
                    spec_boxes = cassette.find_all('div', class_='specList__detailBox')
                    for spec_box in spec_boxes:
                        dt = spec_box.find('dt', class_='specList__title')
                        if dt and '年式' in dt.get_text():
                            dd = spec_box.find('dd', class_='specList__data')
                            if dd:
                                year_span = dd.find('span', class_='specList__emphasisData')
                                if year_span:
                                    year_text = year_span.get_text(strip=True)
                                    year_match = re.search(r'(\d{4})', year_text)
                                    if year_match:
                                        year = int(year_match.group(1))
                    
                    # Extract price (total price in man-yen)
                    price = 1500000  # Default
                    total_price = cassette.find('div', class_='totalPrice')
                    if total_price:
                        main_price = total_price.find('span', class_='totalPrice__mainPriceNum')
                        sub_price = total_price.find('span', class_='totalPrice__subPriceNum')
                        
                        if main_price:
                            main_num = main_price.get_text(strip=True)
                            sub_num = sub_price.get_text(strip=True).replace('.', '') if sub_price else '0'
                            
                            # Convert man-yen to yen (e.g., "48.2万円" = 48.2 * 10000 = 482000)
                            try:
                                price_in_man = float(f"{main_num}.{sub_num}")
                                price = int(price_in_man * 10000)
                            except ValueError:
                                price = int(main_num) * 10000 if main_num.isdigit() else 1500000
                    
                    # Extract color from carBodyInfoList
                    color = 'Silver'  # Default
                    color_items = cassette.find_all('li', class_='carBodyInfoList__item')
                    for item in color_items:
                        text = item.get_text(strip=True)
                        # Check if this item contains color info
                        for jp_color, en_color in COLOR_MAP.items():
                            if jp_color in text:
                                color = en_color
                                break
                        if color != 'Silver':
                            break
                    
                    car_data = {
                        'brand': brand,
                        'model': model,
                        'year': year,
                        'price': price,
                        'color': color,
                        'link': link
                    }
                    
                    cars_data.append(car_data)
                    logger.info(f"Extracted: {brand} {model} ({year}) - ¥{price:,} - {color}")
                    
                except Exception as e:
                    logger.warning(f"Error extracting data from listing {idx}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(cars_data)} car listings")
            return cars_data
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error while scraping: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error while scraping: {e}")
        return []


async def save_cars(cars_data: List[Dict]) -> None:
    """
    Save or update car data in the database using upsert logic
    
    Args:
        cars_data: List of dictionaries containing car information
    """
    if not cars_data:
        logger.warning("No car data to save")
        return
    
    logger.info(f"Saving {len(cars_data)} cars to database...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Use PostgreSQL's INSERT ... ON CONFLICT DO UPDATE
            stmt = insert(Car).values(cars_data)
            
            # On conflict with link (unique constraint), update price and color
            stmt = stmt.on_conflict_do_update(
                index_elements=['link'],
                set_={
                    'price': stmt.excluded.price,
                    'color': stmt.excluded.color,
                }
            )
            
            await session.execute(stmt)
            await session.commit()
            
            logger.info(f"Successfully saved/updated {len(cars_data)} cars")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving cars to database: {e}")
            raise
        finally:
            await session.close()


async def main():
    """
    Main scraper loop - runs continuously, scraping every hour
    """
    logger.info("🚗 Car scraper started!")
    
    iteration = 0
    
    while True:
        try:
            iteration += 1
            logger.info(f"--- Scraping iteration #{iteration} ---")
            
            # Scrape car listings
            cars_data = await scrape_carsensor()
            
            # Save to database
            if cars_data:
                await save_cars(cars_data)
            else:
                logger.warning("No cars scraped in this iteration")
            
            # --- ТЕСТОВЫЙ ВЫХОД ---
            # logger.info("Test run completed. Exiting loop.")
            # break

            # Sleep for 1 hour (3600 seconds)
            logger.info("Sleeping for 3600 seconds (1 hour) before next scrape...")
            await asyncio.sleep(3600)
            
        except KeyboardInterrupt:
            logger.info("Scraper stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            logger.info("Waiting 60 seconds before retry...")
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
