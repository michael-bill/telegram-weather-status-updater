import asyncio
import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

import requests
from telethon import TelegramClient
from telethon.tl.functions.account import UpdateEmojiStatusRequest
from telethon.tl.types import EmojiStatus, EmojiStatusEmpty

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')

CITY_NAME = "Saint Petersburg"
COUNTRY_CODE = "RU"
UPDATE_INTERVAL_SECONDS = 10 * 60  # 10 minutes

# Validate environment variables
if not all([TELEGRAM_API_ID, TELEGRAM_API_HASH, OPENWEATHERMAP_API_KEY]):
    raise EnvironmentError(
        "Missing required environment variables: "
        "TELEGRAM_API_ID, TELEGRAM_API_HASH, OPENWEATHERMAP_API_KEY"
    )

try:
    TELEGRAM_API_ID = int(TELEGRAM_API_ID)
except ValueError:
    raise ValueError("TELEGRAM_API_ID must be a valid integer")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Emoji status configuration
EMOJI_STATUS_IDS = {
    "sun_clear": 5469947168523558652,
    "sun_few_clouds": 5283075860188898177,
    "sun_scattered_clouds": 5283197442123114023,
    "moon_clear": 5188452705546281155,
    "cloud_broken": 5283155153875116393,
    "cloud_overcast": 5287571024500498635,
    "showers_rain_day": 5283097055852503586,
    "rain": 5283243028905994049,
    "thunderstorm": 5282939632416206153,
    "thunderstorm_light": 5282731554135615450,
    "snow": 5431895003821513760,
}

WEATHER_CONDITION_MAP = {
    200: "thunderstorm", 201: "thunderstorm", 202: "thunderstorm",
    210: "thunderstorm_light", 211: "thunderstorm_light", 212: "thunderstorm",
    300: "showers_rain_day", 301: "showers_rain_day", 302: "rain",
    310: "showers_rain_day", 311: "rain", 312: "rain",
    500: "showers_rain_day", 501: "rain", 502: "rain", 503: "rain",
    511: "snow", 520: "showers_rain_day", 521: "showers_rain_day",
    600: "snow", 601: "snow", 602: "snow", 611: "snow",
    800: "sun_clear", 801: "sun_few_clouds", 802: "sun_scattered_clouds",
    803: "cloud_broken", 804: "cloud_overcast",
}

DAY_SPECIFIC_EMOJI_KEYS = {
    "sun_clear", "sun_few_clouds",
    "sun_scattered_clouds", "showers_rain_day"
}

DAY_TO_NIGHT_MAP = {
    "sun_clear": "moon_clear",
    "sun_few_clouds": "cloud_broken",
    "sun_scattered_clouds": "cloud_broken",
    "showers_rain_day": "rain",
}


async def fetch_weather_data(api_key: str, city: str, country: str) -> dict:
    """Fetch current weather data from OpenWeatherMap API."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country}&appid={api_key}&units=metric&lang=ru"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info(
            f"Weather data received for {data.get('name', city)} "
            f"(lat: {data.get('coord', {}).get('lat', 'N/A')}, "
            f"lon: {data.get('coord', {}).get('lon', 'N/A')})"
        )
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Weather API request failed: {e}")
        return None


def determine_day_night(weather_data: dict) -> bool:
    """Determine if it's daytime based on sunrise/sunset data."""
    current_ts = datetime.now(timezone.utc).timestamp()
    sunrise = weather_data.get('sys', {}).get('sunrise')
    sunset = weather_data.get('sys', {}).get('sunset')

    if sunrise and sunset:
        return sunrise < current_ts < sunset

    # Fallback to local time
    now_hour = datetime.now().hour
    return 6 <= now_hour < 21


def select_emoji_status(weather_data: dict) -> int:
    """Select appropriate emoji status based on weather conditions."""
    if not weather_data or not weather_data.get('weather'):
        logging.warning("Invalid weather data for emoji selection")
        return EMOJI_STATUS_IDS.get("cloud_overcast")

    weather = weather_data['weather'][0]
    condition_code = weather['id']
    is_day = determine_day_night(weather_data)

    base_key = WEATHER_CONDITION_MAP.get(condition_code, "cloud_overcast")
    
    # Handle day/night transitions
    if not is_day and base_key in DAY_SPECIFIC_EMOJI_KEYS:
        base_key = DAY_TO_NIGHT_MAP.get(base_key, base_key)

    emoji_id = EMOJI_STATUS_IDS.get(base_key)
    
    if not emoji_id:
        logging.warning(f"No emoji found for {base_key}, using fallback")
        emoji_id = EMOJI_STATUS_IDS.get("cloud_overcast")

    return emoji_id


async def update_emoji_status(client: TelegramClient, emoji_id: int) -> None:
    """Update Telegram emoji status."""
    try:
        status = EmojiStatus(document_id=emoji_id) if emoji_id else EmojiStatusEmpty()
        await client(UpdateEmojiStatusRequest(status))
        logging.info(f"Emoji status updated to {emoji_id if emoji_id else 'empty'}")
    except Exception as e:
        logging.error(f"Failed to update emoji status: {e}")


async def weather_update_loop(client: TelegramClient) -> None:
    """Main loop for periodic weather updates."""
    while True:
        try:
            weather_data = await fetch_weather_data(
                OPENWEATHERMAP_API_KEY,
                CITY_NAME,
                COUNTRY_CODE
            )
            
            emoji_id = select_emoji_status(weather_data) if weather_data else None
            await update_emoji_status(client, emoji_id)
            
            await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
            
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            await asyncio.sleep(60)  # Wait before retrying


async def main() -> None:
    """Main application entry point."""
    client = TelegramClient(
        'weather_status_session',
        TELEGRAM_API_ID,
        TELEGRAM_API_HASH
    )
    
    try:
        async with client:
            logging.info("Connected to Telegram")
            me = await client.get_me()
            logging.info(f"Logged in as {me.first_name} (id: {me.id})")
            await weather_update_loop(client)
            
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
    finally:
        logging.info("Telegram client disconnected")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Application stopped by user")
