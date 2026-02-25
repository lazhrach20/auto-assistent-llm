import asyncio
import json
import logging
import os
from typing import Optional, List

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from dotenv import load_dotenv
from openai import AsyncOpenAI
from sqlalchemy import select

from database import AsyncSessionLocal
from models import Car

# Load environment variables
load_dotenv()

# Configuration
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")
AI_BASE_URL = os.getenv("AI_BASE_URL")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o")

if not TG_BOT_TOKEN:
    raise ValueError("TG_BOT_TOKEN environment variable is not set")
if not AI_API_KEY:
    raise ValueError("AI_API_KEY environment variable is not set")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher()

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=AI_API_KEY,
    base_url=AI_BASE_URL
)


async def extract_filters_from_text(user_text: str) -> dict:
    """
    Use LLM to extract car search filters from user's natural language text
    
    Args:
        user_text: User's message in natural language
        
    Returns:
        Dictionary with optional keys: brand, color, max_price
    """
    logger.info(f"Extracting filters from: {user_text}")
    
    system_prompt = """You are a helpful car search assistant. Your job is to extract search filters from the user's message.

Extract the following information if present:
- brand: Car brand name (normalize to English, e.g., "Toyota", "Honda", "Nissan", "Mazda", "BMW")
- color: Car color (normalize to English, e.g., "Red", "Blue", "White", "Black", "Silver")
- max_price: Maximum price in JPY (Japanese Yen). Convert from millions if needed. For example:
  - "2 million" or "2 million yen" → 2000000
  - "1.5 million" → 1500000
  - "2000000 yen" → 2000000

Return your response as a JSON object with only the fields that are present in the user's message.
Example: {"brand": "Toyota", "color": "Red", "max_price": 2000000}

If no filters are found, return an empty JSON object: {}"""

    try:
        response = await openai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        
        result = response.choices[0].message.content
        filters = json.loads(result)
        
        logger.info(f"Extracted filters: {filters}")
        return filters
        
    except Exception as e:
        logger.error(f"Error extracting filters: {e}")
        return {}


async def search_cars_in_db(filters: dict) -> List[Car]:
    """
    Search for cars in the database based on extracted filters
    
    Args:
        filters: Dictionary with optional keys: brand, color, max_price
        
    Returns:
        List of Car objects matching the criteria (max 5)
    """
    logger.info(f"Searching database with filters: {filters}")
    
    async with AsyncSessionLocal() as session:
        try:
            # Build base query
            query = select(Car)
            
            # Add brand filter if present
            if "brand" in filters and filters["brand"]:
                brand = filters["brand"]
                query = query.where(Car.brand.ilike(f"%{brand}%"))
            
            # Add color filter if present
            if "color" in filters and filters["color"]:
                color = filters["color"]
                query = query.where(Car.color.ilike(f"%{color}%"))
            
            # Add max_price filter if present
            if "max_price" in filters and filters["max_price"]:
                max_price = int(filters["max_price"])
                query = query.where(Car.price <= max_price)
            
            # Order by price (ascending) and limit to 5 results
            query = query.order_by(Car.price.asc()).limit(5)
            
            # Execute query
            result = await session.execute(query)
            cars = result.scalars().all()
            
            logger.info(f"Found {len(cars)} matching cars")
            return list(cars)
            
        except Exception as e:
            logger.error(f"Error searching database: {e}")
            return []
        finally:
            await session.close()


def format_car_message(cars: List[Car]) -> str:
    """
    Format list of cars into a readable message for Telegram
    
    Args:
        cars: List of Car objects
        
    Returns:
        Formatted string message
    """
    if not cars:
        return "🔍 No cars found matching your criteria. Try adjusting your search parameters!"
    
    message = f"🚗 Found {len(cars)} car(s):\n\n"
    
    for idx, car in enumerate(cars, 1):
        price_formatted = f"¥{car.price:,}"
        message += f"{idx}. 🏷️ {car.brand} {car.model}\n"
        message += f"   📅 Year: {car.year}\n"
        message += f"   💰 Price: {price_formatted}\n"
        message += f"   🎨 Color: {car.color}\n"
        message += f"   🔗 Link: {car.link}\n\n"
    
    return message


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    welcome_text = """👋 Welcome to the Million Miles Car Search Bot!

I can help you find cars based on your preferences. Just tell me what you're looking for in natural language!

Examples:
• "Find a red BMW under 2 million yen"
• "Show me Toyota cars"
• "I want a blue Honda under 1.5 million"
• "Looking for a white car under 3 million yen"

Just send me a message and I'll search for matching cars! 🚗"""
    
    await message.answer(welcome_text)


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command"""
    help_text = """ℹ️ How to use this bot:

Simply describe the car you're looking for in natural language. You can specify:
• Brand (Toyota, Honda, Nissan, etc.)
• Color (Red, Blue, White, Black, etc.)
• Maximum price (in yen or millions)

Examples:
• "Find a red BMW under 2 million yen"
• "Show me Toyota cars"
• "I want a blue Honda under 1.5 million"

The bot will search our database and show you up to 5 matching cars with details and links."""
    
    await message.answer(help_text)


@dp.message(F.text)
async def handle_text_message(message: types.Message):
    """
    Handle all text messages - extract filters, search database, and respond
    """
    user_text = message.text
    user_id = message.from_user.id
    
    logger.info(f"User {user_id} sent: {user_text}")
    
    # Send "thinking" message
    thinking_msg = await message.answer("🤔 Searching for cars...")
    
    try:
        # Extract filters using LLM
        filters = await extract_filters_from_text(user_text)
        
        # Search database
        cars = await search_cars_in_db(filters)
        
        # Format and send response
        response = format_car_message(cars)
        
        # Delete thinking message and send results
        await thinking_msg.delete()
        await message.answer(response, disable_web_page_preview=True)
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await thinking_msg.delete()
        await message.answer(
            "❌ Sorry, I encountered an error while processing your request. Please try again!"
        )


async def main():
    """
    Main function to start the bot
    """
    logger.info("🤖 Starting Million Miles Car Bot...")
    logger.info(f"Using AI Model: {AI_MODEL}")
    
    try:
        # Start polling
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Error in bot: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
