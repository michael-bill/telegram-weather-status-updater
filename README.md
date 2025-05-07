# Telegram Weather Status Updater

Автоматически обновляет ваш эмодзи-статус в Telegram в соответствии с текущей погодой в заданном городе.

## Особенности
- Автоматическое определение дневного/ночного времени
- Поддержка различных погодных условий (дождь, снег, гроза, облачность и т.д.)
- Настраиваемые интервалы обновления
- Поддержка пользовательских эмодзи-статусов

## Требования
- Python 3.9+
- Аккаунт Telegram
- API ключ OpenWeatherMap

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/michael-bill/telegram-weather-status-updater
cd telegram-weather-status-updater
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` и заполните его:
```ini
TELEGRAM_API_ID=ваш_api_id
TELEGRAM_API_HASH=ваш_api_hash
OPENWEATHERMAP_API_KEY=ваш_api_key
```

## Настройка
Перед первым запуском:
1. Получите API ключ на [OpenWeatherMap](https://openweathermap.org/api)
2. Зарегистрируйте приложение Telegram на [my.telegram.org](https://my.telegram.org)
3. Настройте параметры города в файле `main.py` (по умолчанию Санкт-Петербург)

## Использование
Запустите бота:
```bash
python main.py
```

Бот будет автоматически:
- Определять текущую погоду
- Выбирать соответствующий эмодзи-статус
- Обновлять статус каждые 10 минут

## Конфигурация
Основные настройки в коде:
```python
CITY_NAME = "Saint Petersburg"  # Ваш город
COUNTRY_CODE = "RU"             # Код страны
UPDATE_INTERVAL_SECONDS = 5 * 60  # Интервал обновления (в секундах)
```
