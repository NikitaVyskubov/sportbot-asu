import asyncio
import re
import os
import json
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text
from vkbottle import PhotoMessageUploader

# ========== ИМПОРТЫ ==========
from techniques import TECHNIQUES, CATEGORIES
from techniques.chest import CHEST_TECHNIQUES
from techniques.back import BACK_TECHNIQUES
from techniques.legs import LEGS_TECHNIQUES
from techniques.shoulders import SHOULDERS_TECHNIQUES
from techniques.arms import ARMS_TECHNIQUES
from techniques.core import CORE_TECHNIQUES
from books_data import BOOKS_DATA

# ========== НАСТРОЙКИ ==========
GROUP_TOKEN = "vk1.a.eOV8BNuV-NOZGR4DSw14CDk6bl-6jXpBz-2Qd7hcV6ma27kuC8RkzsYy4jVS9COvOYNbSErt1vft0dvfODzDky8esotaeIDbxiThDNZ0WvY8qCF5_b9ArwhBEGaQk6_4ULs4HWgrS1NI3z2iQfowUTVHk-pSSopvFxS3V9uM9fmY5vncyh84ACTn1L3-Kd8XEwe58Q1nByK5cklUCcT6iQ"
ADMIN_ID = 511117713

os.chdir(r"D:\bot")

bot = Bot(token=GROUP_TOKEN)

# Создаём загрузчик фото
photo_uploader = PhotoMessageUploader(bot.api)

# Режим редактирования расписания
editing_mode = False

# Файл для хранения ID пользователей
USERS_FILE = "users.json"


# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛОВЫМ ХРАНЕНИЕМ ==========
def load_known_users():
    """Загружает список пользователей из JSON-файла"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data)
        except (json.JSONDecodeError, FileNotFoundError):
            return set()
    return set()


def save_known_users():
    """Сохраняет список пользователей в JSON-файл"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(known_users), f, ensure_ascii=False, indent=2)


def add_user(user_id):
    """Добавляет пользователя и сохраняет в файл"""
    if user_id not in known_users:
        known_users.add(user_id)
        save_known_users()


# Загружаем существующих пользователей при старте
known_users = load_known_users()
print(f"Загружено {len(known_users)} пользователей из файла")

# Данные для калькулятора калоража
user_calorie_data = {}

# Хранилище для пагинации
pagination_data = {}

# Хранилище для выбранного упражнения 1ПМ
user_1rm_exercise = {}

# Хранилище для расчёта рабочего веса
user_working_weight_data = {}


# ========== ДАННЫЕ ==========
schedule_data = {
    "monday": "ПН - 12:20 – 20:50",
    "tuesday": "ВТ - 16:00 – 21:00",
    "wednesday": "СР - 14:20 – 20:50",
    "thursday": "ЧТ - 16:00 – 21:00",
    "friday": "ПТ - 14:20 – 20:50",
    "saturday": "СБ - 10:00 – 18:30",
    "sunday": "ВС - ВЫХОДНОЙ"
}

# Типы упражнений для расчёта рабочего веса
EXERCISE_TYPES = {
    "базовое": ["жим", "присед", "становая", "тяга штанги", "подтягивание", "отжимание на брусьях", "жим ногами",
                "армейский"],
    "вспомогательное": ["жим гантелей", "тяга гантели", "выпады", "французский жим", "пуловер", "шраги"],
    "изолирующее": ["сгибание", "разгибание", "махи", "подъём", "бабочка", "crossover", "бицепс", "трицепс", "дельт",
                    "молотки"]
}


# ========== ФУНКЦИИ РАСЧЁТА ==========
def calculate_bmr(weight_kg, height_cm, age):
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5


def calculate_calories(weight, height, age, activity, goal):
    bmr = calculate_bmr(weight, height, age)
    activity_mult = {"min": 1.2, "light": 1.375, "medium": 1.55, "high": 1.725}.get(activity, 1.2)
    tdee = bmr * activity_mult
    if goal == "mass":
        return tdee + 300
    elif goal == "cut":
        return tdee - 400
    return tdee


def calculate_1rm(weight, reps):
    if reps >= 37:
        return weight
    return weight * (36 / (37 - reps))


def get_exercise_type(exercise_name: str) -> str:
    """Определяет тип упражнения по названию"""
    exercise_lower = exercise_name.lower()

    for ex_type, keywords in EXERCISE_TYPES.items():
        for keyword in keywords:
            if keyword in exercise_lower:
                return ex_type
    return "вспомогательное"


def calculate_working_weight(one_rm, reps, week=1, experience="intermediate", exercise_name=""):
    """
    Расчёт рабочего веса с учётом типа упражнения
    """
    percentage_map = {
        1: 100, 2: 95, 3: 93, 4: 90, 5: 87,
        6: 85, 7: 83, 8: 80, 9: 77, 10: 75,
        11: 73, 12: 70, 13: 68, 14: 65, 15: 60
    }

    percentage = percentage_map.get(reps, 75)

    # Корректировка в зависимости от типа упражнения
    exercise_type = get_exercise_type(exercise_name)

    if exercise_type == "базовое":
        type_multiplier = 1.00
    elif exercise_type == "вспомогательное":
        type_multiplier = 0.95
    else:
        type_multiplier = 0.85

    # Корректировка по опыту
    if experience == "beginner":
        exp_multiplier = 0.90
    elif experience == "advanced":
        exp_multiplier = 1.05
    else:
        exp_multiplier = 1.00

    # Корректировка для большого количества повторений
    reps_multiplier = 0.95 if reps > 12 else 1.00

    # Прогрессия по неделям
    progression_increment = 1.5 if exercise_type == "изолирующее" else 2.5
    progression = ((week - 1) // 2) * progression_increment

    # Финальный расчёт
    working_weight = one_rm * (percentage / 100) * type_multiplier * exp_multiplier * reps_multiplier + progression

    # Округление
    if exercise_type == "изолирующее":
        rounded = round(working_weight)
    else:
        rounded = round(working_weight / 2.5) * 2.5

    # Безопасное округление для новичков
    if experience == "beginner" and rounded > working_weight:
        rounded -= (2.5 if exercise_type != "изолирующее" else 1)

    min_weight = 5.0 if exercise_type == "изолирующее" else 20.0
    return max(rounded, min_weight)


def get_reps_guide(reps):
    """Возвращает цель подхода в зависимости от повторений"""
    if reps <= 5:
        return "Силовая работа (развитие силы)"
    elif reps <= 8:
        return "Силовая гипертрофия (сила + масса)"
    elif reps <= 12:
        return "Гипертрофия (набор массы)"
    elif reps <= 15:
        return "Тонировка + выносливость"
    else:
        return "Пампинг (кровенаполнение)"


def get_reps_recommendation(exercise_name: str) -> str:
    """Рекомендация по количеству повторений для конкретного упражнения"""
    exercise_type = get_exercise_type(exercise_name)

    if exercise_type == "базовое":
        return """
Рекомендуемые диапазоны повторений для БАЗОВЫХ упражнений:
• 3-5 повторений - развитие силы
• 6-8 повторений - силовая гипертрофия
• 8-12 повторений - набор массы (оптимально)
"""
    elif exercise_type == "вспомогательное":
        return """
Рекомендуемые диапазоны повторений для ВСПОМОГАТЕЛЬНЫХ упражнений:
• 6-8 повторений - сила + масса
• 8-12 повторений - набор массы (оптимально)
• 10-15 повторений - тонировка
"""
    else:
        return """
Рекомендуемые диапазоны повторений для ИЗОЛИРУЮЩИХ упражнений:
• 8-12 повторений - набор массы
• 12-15 повторений - детализация
• 15-20 повторений - пампинг (кровенаполнение)
"""


# ========== ТЕКСТЫ ПИТАНИЯ ==========
def get_mass_nutrition_text():
    return """
ПИТАНИЕ НА МАССОНАБОР

Главная цель: Профицит калорий (есть больше, чем тратишь).

Расчёт калорий (примерный):
• Вес тела × 30-35 ккал = дневная норма на поддержание
• Для набора: +300-500 ккал сверху

БЖУ в день (на 1 кг веса):
• Белки: 1.8-2.2 г (основа мышц)
• Жиры: 0.8-1 г (гормоны + суставы)
• Углеводы: 4-7 г (энергия + рост)

Лучшие продукты:
• Курица, индейка, говядина, рыба (все виды)
• Яйца, творог (5-9%), сыр, греческий йогурт
• Рис, гречка, овсянка, макароны из твёрдых сортов
• Картофель, бананы, хлеб (цельнозерновой)
• Орехи, арахисовая паста, оливковое масло

Ограничить:
• Фастфуд, сладости, трансжиры (чистый жир, не мышцы)

Важные правила:
1. Ешьте каждые 3-4 часа (4-5 приёмов пищи)
2. Обязательно есть в течение 1-2 часов после тренировки
3. Не бойтесь углеводов — это энергия для роста
4. Пейте 2-3 литра воды в день
5. Контролируйте прогресс: если вес не растёт — добавляйте ещё 200 ккал
"""


def get_cut_nutrition_text():
    return """
ПИТАНИЕ НА СУШКУ

Главная цель: Дефицит калорий (тратить больше, чем есть).

Расчёт калорий:
• Дефицит 300-500 ккал от нормы поддержания
• НЕ создавайте слишком большой дефицит (>700 ккал) — потеряете мышцы

БЖУ в день (на 1 кг веса):
• Белки: 2.0-2.4 г (сохраняем мышцы)
• Жиры: 0.7-0.9 г (не опускать ниже!)
• Углеводы: 1.5-3 г (по самочувствию)

Лучшие продукты:
• Куриное филе, индейка, белая рыба (треска, минтай)
• Яичные белки, обезжиренный творог, тофу
• Овощи: брокколи, цветная капуста, шпинат, огурцы, листовой салат
• Гречка, бурый рис (только в первой половине дня)
• Авокадо, оливковое масло (источники жиров)

Исключить/минимизировать:
• Быстрые углеводы (сахар, сладости, белый хлеб)
• Жирное мясо, колбасы, копчёности
• Сладкие йогурты, творожные массы
• Алкоголь (абсолютно)

Важные правила:
1. Больше белка — насыщает и сохраняет мышцы
2. Овощи в каждом приёме — для объёма и клетчатки
3. Углеводы — в первой половине дня и вокруг тренировки
4. Пейте много воды (от 2.5 литров) — ускоряет метаболизм
5. Не исключайте жиры полностью (нарушится гормональный фон)
"""


def get_general_nutrition_text():
    return """
ОБЩИЕ ПРИНЦИПЫ ПИТАНИЯ

1. Пейте достаточно воды
   • 30-40 мл на 1 кг веса тела
   • Вода ускоряет метаболизм и помогает восстановлению

2. Ешьте дробно
   • 4-5 приёмов пищи в день
   • Не допускайте сильного чувства голода

3. Учитывайте время приёмов
   • Завтрак: в течение часа после пробуждения
   • Последний приём: за 1.5-2 часа до сна
   • До тренировки: за 1.5-2 часа (сложные углеводы + белок)
   • После тренировки: в течение часа (белок + быстрые углеводы)

4. Источники нутриентов
   • Белки: мясо, рыба, яйца, творог, бобовые
   • Жиры: орехи, авокадо, оливковое масло, жирная рыба
   • Углеводы: крупы, овощи, фрукты, цельнозерновой хлеб

5. Что исключить
   • Фастфуд, сладкие газировки, промышленные соусы
   • Чипсы, сухарики, кондитерские изделия
   • Алкоголь (пустые калории + замедляет восстановление)

6. Контролируйте прогресс
   • Взвешивайтесь 1 раз в неделю в одно и то же время
   • Смотрите на изменения в зеркале и самочувствие
   • Корректируйте калорийность по результатам
"""


# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("💪 Техника тренажеров"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🍽 Калькулятор калоража"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("🥗 Советы по питанию"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🏆 Расчёт 1ПМ"), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text("⚡ Расчёт рабочего веса"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🕐 Расписание зала"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("📚 Дополнительная литература"), color=KeyboardButtonColor.SECONDARY)
    return keyboard


def get_technique_categories_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("ГРУДЬ"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("СПИНА"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("НОГИ"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("ПЛЕЧИ"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("РУКИ"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("ПРЕСС И КОР"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🔙 Назад в меню"), color=KeyboardButtonColor.SECONDARY)
    return keyboard


def get_nutrition_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("💪 Набор массы"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🔥 Сушка"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("📋 Общие принципы питания"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🔙 Назад в меню"), color=KeyboardButtonColor.SECONDARY)
    return keyboard


def get_1rm_menu_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("🏋️‍♂️ Жим лёжа"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🏋️‍♂️ Становая тяга"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🏋️‍♂️ Приседания со штангой"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🔙 Назад в меню"), color=KeyboardButtonColor.SECONDARY)
    return keyboard


def get_1rm_result_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("🔄 Рассчитать ещё"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🏋️ Другое упражнение"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🔙 Назад в меню"), color=KeyboardButtonColor.SECONDARY)
    return keyboard


def get_working_weight_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("🏋️ Рассчитать рабочий вес"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("📊 Таблица процентов"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🔄 Прогрессия по неделям"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("💡 Рекомендации по повторениям"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🔙 Назад в меню"), color=KeyboardButtonColor.SECONDARY)
    return keyboard


def get_experience_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("🟢 Новичок (до 6 мес)"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🟡 Средний (6 мес - 2 года)"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🔴 Продвинутый (2+ года)"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🔙 Отмена"), color=KeyboardButtonColor.NEGATIVE)
    return keyboard


def get_activity_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("🛌 Минимальная"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🚶 Легкая"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🏃 Средняя"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("💪 Высокая"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🔙 Отмена"), color=KeyboardButtonColor.NEGATIVE)
    return keyboard


def get_goal_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("💪 Набор массы (расчёт)"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🔥 Сушка (расчёт)"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("⚖️ Поддержание (расчёт)"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🔙 Отмена"), color=KeyboardButtonColor.NEGATIVE)
    return keyboard


def get_library_categories_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("📖 Базовые учебники"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🥗 Питание"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("📊 Программы тренировок"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🌐 Онлайн-ресурсы"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🎓 Научные статьи и исследования"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🔙 Назад в меню"), color=KeyboardButtonColor.SECONDARY)
    return keyboard


def get_activity_value(text: str) -> str:
    if "Минимальная" in text:
        return "min"
    elif "Легкая" in text:
        return "light"
    elif "Средняя" in text:
        return "medium"
    elif "Высокая" in text:
        return "high"
    return "medium"


def get_goal_value(text: str) -> str:
    if "Набор" in text:
        return "mass"
    elif "Сушка" in text:
        return "cut"
    elif "Поддержание" in text:
        return "maintenance"
    return "maintenance"


def get_experience_value(text: str) -> str:
    if "Новичок" in text:
        return "beginner"
    elif "Средний" in text:
        return "intermediate"
    elif "Продвинутый" in text:
        return "advanced"
    return "intermediate"


# ========== ФУНКЦИЯ ПАГИНАЦИИ ==========
async def show_exercises_page(user_id, message, category, page):
    exercises_dict = {
        "chest": CHEST_TECHNIQUES,
        "back": BACK_TECHNIQUES,
        "legs": LEGS_TECHNIQUES,
        "shoulders": SHOULDERS_TECHNIQUES,
        "arms": ARMS_TECHNIQUES,
        "core": CORE_TECHNIQUES
    }.get(category)

    if not exercises_dict:
        return

    exercises_list = list(exercises_dict.items())
    total = len(exercises_list)

    ITEMS_PER_PAGE = 5
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    page = max(0, min(page, total_pages - 1))

    start = page * ITEMS_PER_PAGE
    end = min(start + ITEMS_PER_PAGE, total)
    current_exercises = exercises_list[start:end]

    keyboard = Keyboard(one_time=False, inline=False)

    for key, exercise in current_exercises:
        name = exercise["name"]
        # Обрезаем название, если длиннее 40 символов
        if len(name) > 40:
            name = name[:37] + "..."
        keyboard.add(Text(name), color=KeyboardButtonColor.PRIMARY)
        keyboard.row()

    nav_buttons = []
    if page > 0:
        nav_buttons.append("◀️ Предыдущая")
    if page < total_pages - 1:
        nav_buttons.append("Следующая ▶️")

    if nav_buttons:
        for btn in nav_buttons:
            keyboard.add(Text(btn), color=KeyboardButtonColor.SECONDARY)
        keyboard.row()

    keyboard.add(Text("◀️ Назад к категориям"), color=KeyboardButtonColor.SECONDARY)

    pagination_data[user_id] = {
        "category": category,
        "page": page,
        "total_pages": total_pages
    }

    category_names = {
        "chest": "груди",
        "back": "спины",
        "legs": "ног",
        "shoulders": "плеч",
        "arms": "рук",
        "core": "пресса и кора"
    }

    page_info = f" (страница {page + 1}/{total_pages})" if total_pages > 1 else ""
    await message.answer(f"Упражнения для {category_names[category]}{page_info}:", keyboard=keyboard)


# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========

@bot.on.message(text=["start", "начать", "меню"])
async def start_handler(message: Message):
    add_user(message.from_id)
    await message.answer(
        "Добро пожаловать в бота для Спортивного зала СОК АлтГУ!\n\n"
        "Я помогу вам узнать технику упражнений и многое другое\n\n"
        "Используйте кнопки ниже",
        keyboard=get_main_keyboard()
    )


@bot.on.message(text="💪 Техника тренажеров")
async def technique_menu(message: Message):
    add_user(message.from_id)
    await message.answer("Выберите группу мышц:", keyboard=get_technique_categories_keyboard())


@bot.on.message(text="ГРУДЬ")
async def show_chest_exercises(message: Message):
    add_user(message.from_id)
    await show_exercises_page(message.from_id, message, "chest", 0)


@bot.on.message(text="СПИНА")
async def show_back_exercises(message: Message):
    add_user(message.from_id)
    await show_exercises_page(message.from_id, message, "back", 0)


@bot.on.message(text="НОГИ")
async def show_legs_exercises(message: Message):
    add_user(message.from_id)
    await show_exercises_page(message.from_id, message, "legs", 0)


@bot.on.message(text="ПЛЕЧИ")
async def show_shoulders_exercises(message: Message):
    add_user(message.from_id)
    await show_exercises_page(message.from_id, message, "shoulders", 0)


@bot.on.message(text="РУКИ")
async def show_arms_exercises(message: Message):
    add_user(message.from_id)
    await show_exercises_page(message.from_id, message, "arms", 0)


@bot.on.message(text="ПРЕСС И КОР")
async def show_core_exercises(message: Message):
    add_user(message.from_id)
    await show_exercises_page(message.from_id, message, "core", 0)


@bot.on.message(text=["◀️ Предыдущая", "Следующая ▶️"])
async def navigate_pagination(message: Message):
    user_id = message.from_id
    add_user(user_id)

    data = pagination_data.get(user_id)
    if not data:
        await message.answer("Пожалуйста, выберите категорию заново.", keyboard=get_technique_categories_keyboard())
        return

    new_page = data["page"]
    if message.text == "◀️ Предыдущая":
        new_page -= 1
    elif message.text == "Следующая ▶️":
        new_page += 1

    await show_exercises_page(user_id, message, data["category"], new_page)


@bot.on.message(text="◀️ Назад к категориям")
async def back_to_categories(message: Message):
    add_user(message.from_id)
    if message.from_id in pagination_data:
        del pagination_data[message.from_id]
    await message.answer("Выберите группу мышц:", keyboard=get_technique_categories_keyboard())


@bot.on.message(text="🔙 Назад в меню")
async def back_to_main(message: Message):
    add_user(message.from_id)
    await message.answer("Главное меню", keyboard=get_main_keyboard())


# ========== КАЛЬКУЛЯТОР КАЛОРАЖА ==========
@bot.on.message(text="🍽 Калькулятор калоража")
async def start_calorie_calculator(message: Message):
    add_user(message.from_id)
    user_calorie_data[message.from_id] = {}
    await message.answer(
        "КАЛЬКУЛЯТОР КАЛОРАЖА\n\n"
        "Отвечайте на вопросы по очереди.\n\n"
        "Сколько вам лет?\n\n"
        "Отмена - напишите: отмена",
        keyboard=Keyboard(one_time=False, inline=False)
    )


# ========== СОВЕТЫ ПО ПИТАНИЮ ==========
@bot.on.message(text="🥗 Советы по питанию")
async def nutrition_menu(message: Message):
    add_user(message.from_id)
    await message.answer(
        "СОВЕТЫ ПО ПИТАНИЮ\n\n"
        "Выберите интересующий вас раздел:",
        keyboard=get_nutrition_keyboard()
    )


@bot.on.message(text="💪 Набор массы")
async def mass_nutrition(message: Message):
    add_user(message.from_id)
    await message.answer(get_mass_nutrition_text(), keyboard=get_nutrition_keyboard())


@bot.on.message(text="🔥 Сушка")
async def cut_nutrition(message: Message):
    add_user(message.from_id)
    await message.answer(get_cut_nutrition_text(), keyboard=get_nutrition_keyboard())


@bot.on.message(text="📋 Общие принципы питания")
async def general_nutrition(message: Message):
    add_user(message.from_id)
    await message.answer(get_general_nutrition_text(), keyboard=get_nutrition_keyboard())


# ========== РАСЧЁТ 1ПМ ==========
@bot.on.message(text="🏆 Расчёт 1ПМ")
async def start_1rm_menu(message: Message):
    add_user(message.from_id)
    await message.answer(
        "Выберите упражнение:",
        keyboard=get_1rm_menu_keyboard()
    )


@bot.on.message(text="🏋️‍♂️ Жим лёжа")
async def select_bench_press(message: Message):
    add_user(message.from_id)
    user_1rm_exercise[message.from_id] = "ЖИМ ЛЁЖА"
    await message.answer("Введите вес и повторения через пробел:\nПример: 100 8")


@bot.on.message(text="🏋️‍♂️ Становая тяга")
async def select_deadlift(message: Message):
    add_user(message.from_id)
    user_1rm_exercise[message.from_id] = "СТАНОВАЯ ТЯГА"
    await message.answer("Введите вес и повторения через пробел:\nПример: 140 6")


@bot.on.message(text="🏋️‍♂️ Приседания со штангой")
async def select_squat(message: Message):
    add_user(message.from_id)
    user_1rm_exercise[message.from_id] = "ПРИСЕДАНИЯ СО ШТАНГОЙ"
    await message.answer("Введите вес и повторения через пробел:\nПример: 120 5")


@bot.on.message(text="🔄 Рассчитать ещё")
async def calculate_again(message: Message):
    add_user(message.from_id)
    await message.answer("Введите вес и повторения через пробел:\nПример: 100 8")


@bot.on.message(text="🏋️ Другое упражнение")
async def other_exercise(message: Message):
    add_user(message.from_id)
    if message.from_id in user_1rm_exercise:
        del user_1rm_exercise[message.from_id]
    await message.answer("Выберите упражнение:", keyboard=get_1rm_menu_keyboard())


# ========== РАСЧЁТ РАБОЧЕГО ВЕСА ==========
@bot.on.message(text="⚡ Расчёт рабочего веса")
async def working_weight_menu(message: Message):
    add_user(message.from_id)
    await message.answer(
        "РАСЧЁТ РАБОЧЕГО ВЕСА\n\n"
        "Выберите режим:\n\n"
        "• Рассчитать рабочий вес - пошаговый расчёт\n"
        "• Таблица процентов - справочная информация\n"
        "• Прогрессия по неделям - план на несколько недель\n"
        "• Рекомендации по повторениям - советы для разных упражнений",
        keyboard=get_working_weight_keyboard()
    )


@bot.on.message(text="🏋️ Рассчитать рабочий вес")
async def working_weight_start(message: Message):
    add_user(message.from_id)
    user_working_weight_data[message.from_id] = {"step": "exercise"}
    await message.answer(
        "Введите название упражнения (например: Жим лёжа, Приседания, Сгибания на бицепс):"
    )


@bot.on.message(text="📊 Таблица процентов")
async def show_percentage_table(message: Message):
    add_user(message.from_id)
    table = """
ТАБЛИЦА ПРОЦЕНТОВ ОТ 1ПМ

Повторения | % от 1ПМ | Цель подхода
1-2 повтора | 95-100%  | Максимальная сила
3-5 повторов| 85-93%   | Силовая выносливость
6-8 повторов| 78-85%   | Силовая гипертрофия
8-12 повторов| 70-78%  | Набор массы
12-15 повторов| 60-70% | Тонировка
15+ повторов | <60%    | Пампинг/выносливость

КАК ПОЛЬЗОВАТЬСЯ:
1. Узнайте свой 1ПМ (одноповторный максимум)
2. Определите цель подхода (например, 8 повторений)
3. Умножьте 1ПМ на процент из таблицы
4. Получите рабочий вес

Пример: 1ПМ = 100 кг, цель 8 повторений (80%)
100 × 0.80 = 80 кг
"""
    await message.answer(table, keyboard=get_working_weight_keyboard())


@bot.on.message(text="🔄 Прогрессия по неделям")
async def progression_weeks_start(message: Message):
    add_user(message.from_id)
    user_working_weight_data[message.from_id] = {"step": "progression_exercise"}
    await message.answer(
        "РАСЧЁТ ПРОГРЕССИИ ПО НЕДЕЛЯМ\n\n"
        "Введите название упражнения:"
    )


@bot.on.message(text="💡 Рекомендации по повторениям")
async def reps_recommendations_start(message: Message):
    add_user(message.from_id)
    user_working_weight_data[message.from_id] = {"step": "recommendation"}
    await message.answer(
        "Введите название упражнения, и я подскажу оптимальный диапазон повторений.\n\n"
        "Примеры:\n"
        "- Жим лёжа\n"
        "- Сгибания на бицепс\n"
        "- Разгибания на трицепс"
    )


# ========== РАСПИСАНИЕ И ЛИТЕРАТУРА ==========
@bot.on.message(text="🕐 Расписание зала")
async def show_schedule(message: Message):
    add_user(message.from_id)
    schedule_text = "Расписание тренажёрного зала СОК АлтГУ на 2026 год\n\n"
    for day in schedule_data.values():
        schedule_text += f"• {day}\n"
    schedule_text += "\nРасписание может меняться в праздничные дни."

    if message.from_id == ADMIN_ID:
        admin_keyboard = Keyboard(one_time=False, inline=False)
        admin_keyboard.add(Text("✏️ Редактировать расписание"), color=KeyboardButtonColor.PRIMARY)
        admin_keyboard.row()
        admin_keyboard.add(Text("📢 Рассылка"), color=KeyboardButtonColor.PRIMARY)
        await message.answer(schedule_text + "\n\nВы администратор, доступны доп. функции.", keyboard=admin_keyboard)
    else:
        await message.answer(schedule_text)


@bot.on.message(text="📚 Дополнительная литература")
async def show_library_categories(message: Message):
    add_user(message.from_id)
    await message.answer("Библиотека знаний\n\nВыберите категорию:", keyboard=get_library_categories_keyboard())


@bot.on.message(text="📖 Базовые учебники")
async def show_books_basic(message: Message):
    add_user(message.from_id)
    text = "БАЗОВЫЕ УЧЕБНИКИ\n\n"
    for title, info in BOOKS_DATA["📖 Базовые учебники"].items():
        text += f"📖 {title}\n📌 {info['desc']}\n👨‍🔬 {info['about_author']}\n✅ {info['why_reliable']}\n\n"
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("◀️ Назад к категориям библиотеки"), color=KeyboardButtonColor.SECONDARY)
    await message.answer(text, keyboard=keyboard)


@bot.on.message(text="🥗 Питание")
async def show_books_nutrition(message: Message):
    add_user(message.from_id)
    text = "ПИТАНИЕ\n\n"
    for title, info in BOOKS_DATA["🥗 Питание"].items():
        text += f"📖 {title}\n📌 {info['desc']}\n👨‍🔬 {info['about_author']}\n✅ {info['why_reliable']}\n\n"
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("◀️ Назад к категориям библиотеки"), color=KeyboardButtonColor.SECONDARY)
    await message.answer(text, keyboard=keyboard)


@bot.on.message(text="📊 Программы тренировок")
async def show_books_programs(message: Message):
    add_user(message.from_id)
    text = "ПРОГРАММЫ ТРЕНИРОВОК\n\n"
    for title, info in BOOKS_DATA["📊 Программы тренировок"].items():
        text += f"📖 {title}\n📌 {info['desc']}\n👨‍🔬 {info['about_author']}\n✅ {info['why_reliable']}\n\n"
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("◀️ Назад к категориям библиотеки"), color=KeyboardButtonColor.SECONDARY)
    await message.answer(text, keyboard=keyboard)


@bot.on.message(text="🌐 Онлайн-ресурсы")
async def show_books_online(message: Message):
    add_user(message.from_id)
    text = "ОНЛАЙН-РЕСУРСЫ\n\n"
    for title, info in BOOKS_DATA["🌐 Онлайн-ресурсы"].items():
        text += f"📖 {title}\n📌 {info['desc']}\n👨‍🔬 {info['about_author']}\n✅ {info['why_reliable']}\n\n"
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("◀️ Назад к категориям библиотеки"), color=KeyboardButtonColor.SECONDARY)
    await message.answer(text, keyboard=keyboard)


@bot.on.message(text="🎓 Научные статьи и исследования")
async def show_books_science(message: Message):
    add_user(message.from_id)
    text = "НАУЧНЫЕ СТАТЬИ И ИССЛЕДОВАНИЯ\n\n"
    for title, info in BOOKS_DATA["🎓 Научные статьи и исследования"].items():
        text += f"📖 {title}\n📌 {info['desc']}\n👨‍🔬 {info['about_author']}\n✅ {info['why_reliable']}\n\n"
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("◀️ Назад к категориям библиотеки"), color=KeyboardButtonColor.SECONDARY)
    await message.answer(text, keyboard=keyboard)


@bot.on.message(text="◀️ Назад к категориям библиотеки")
async def back_to_library_categories(message: Message):
    add_user(message.from_id)
    await message.answer("Библиотека знаний\n\nВыберите категорию:", keyboard=get_library_categories_keyboard())


# ========== АДМИНСКИЕ ФУНКЦИИ ==========
@bot.on.message(text="✏️ Редактировать расписание")
async def edit_schedule_start(message: Message):
    if message.from_id != ADMIN_ID:
        return
    global editing_mode
    editing_mode = True
    await message.answer(
        "Режим редактирования расписания ВКЛЮЧЕН\n\n"
        "Введите новое время в формате:\n"
        "ПН - 10:00 – 22:00\n\n"
        "Для выхода: отмена"
    )


@bot.on.message(text="📢 Рассылка")
async def push_start(message: Message):
    if message.from_id != ADMIN_ID:
        await message.answer("У вас нет прав.")
        return
    global editing_mode
    editing_mode = "push"
    await message.answer("Режим рассылки\n\nВведите текст для рассылки.\n\nДля отмены: отмена")


# ========== ЕДИНЫЙ УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК ==========
@bot.on.message()
async def handle_all(message: Message):
    global editing_mode

    user_id = message.from_id
    text = message.text

    # Автоматическое добавление пользователя (для всех, кто пишет боту)
    add_user(user_id)

    # ========== КАЛЬКУЛЯТОР КАЛОРАЖА ==========
    if user_id in user_calorie_data:
        step = user_calorie_data[user_id].get("step")

        if step is None:
            if text.lower() == "отмена":
                del user_calorie_data[user_id]
                await message.answer("Расчёт отменён.", keyboard=get_main_keyboard())
                return
            try:
                age = int(text)
                if 10 <= age <= 100:
                    user_calorie_data[user_id]["age"] = age
                    user_calorie_data[user_id]["step"] = "weight"
                    await message.answer(f"Возраст: {age}\n\nСколько вы весите (кг)?")
                else:
                    await message.answer("Ошибка. Возраст от 10 до 100 лет.")
            except ValueError:
                await message.answer("Ошибка. Введите число.")
            return

        elif step == "weight":
            if text.lower() == "отмена":
                del user_calorie_data[user_id]
                await message.answer("Расчёт отменён.", keyboard=get_main_keyboard())
                return
            try:
                weight = float(text.replace(",", "."))
                if 20 <= weight <= 300:
                    user_calorie_data[user_id]["weight"] = weight
                    user_calorie_data[user_id]["step"] = "height"
                    await message.answer(f"Вес: {weight} кг\n\nКакой у вас рост (см)?")
                else:
                    await message.answer("Ошибка. Вес от 20 до 300 кг.")
            except ValueError:
                await message.answer("Ошибка. Введите число.")
            return

        elif step == "height":
            if text.lower() == "отмена":
                del user_calorie_data[user_id]
                await message.answer("Расчёт отменён.", keyboard=get_main_keyboard())
                return
            try:
                height = int(text)
                if 50 <= height <= 250:
                    user_calorie_data[user_id]["height"] = height
                    user_calorie_data[user_id]["step"] = "activity"
                    await message.answer(f"Рост: {height} см\n\nВыберите уровень активности:",
                                         keyboard=get_activity_keyboard())
                else:
                    await message.answer("Ошибка. Рост от 50 до 250 см.")
            except ValueError:
                await message.answer("Ошибка. Введите число.")
            return

        elif step == "activity":
            if text == "🔙 Отмена":
                del user_calorie_data[user_id]
                await message.answer("Расчёт отменён.", keyboard=get_main_keyboard())
                return
            if any(key in text for key in ["Минимальная", "Легкая", "Средняя", "Высокая"]):
                activity = get_activity_value(text)
                user_calorie_data[user_id]["activity"] = activity
                user_calorie_data[user_id]["step"] = "goal"
                await message.answer("Активность выбрана\n\nВыберите цель:", keyboard=get_goal_keyboard())
            else:
                await message.answer("Выберите активность из кнопок.")
            return

        elif step == "goal":
            if text == "🔙 Отмена":
                del user_calorie_data[user_id]
                await message.answer("Расчёт отменён.", keyboard=get_main_keyboard())
                return
            if any(key in text for key in ["Набор", "Сушка", "Поддержание"]):
                goal = get_goal_value(text)
                user_calorie_data[user_id]["goal"] = goal

                data = user_calorie_data[user_id]
                age = data["age"]
                weight = data["weight"]
                height = data["height"]
                activity = data["activity"]

                calories = calculate_calories(weight, height, age, activity, goal)

                goal_text = {
                    "mass": "Набор массы",
                    "cut": "Сушка",
                    "maintenance": "Поддержание веса"
                }.get(goal, "Поддержание веса")

                protein = round(weight * 2)
                fats = round(weight * 0.8)
                carbs = round((calories - (protein * 4) - (fats * 9)) / 4)

                result = f"""
РЕЗУЛЬТАТ РАСЧЁТА

Ваши данные:
- Возраст: {age} лет
- Вес: {weight} кг
- Рост: {height} см
- Цель: {goal_text}

Дневная норма калорий: {int(calories)} ккал

БЖУ в день:
- Белки: {protein} г
- Жиры: {fats} г
- Углеводы: {carbs} г
"""
                await message.answer(result, keyboard=get_main_keyboard())
                del user_calorie_data[user_id]
            else:
                await message.answer("Выберите цель из кнопок.")
            return

    # РАСЧЁТ РАБОЧЕГО ВЕСА - ОБРАБОТКА ШАГОВ
    if user_id in user_working_weight_data:
        data = user_working_weight_data[user_id]
        step = data.get("step")

        # Отмена
        if text.lower() == "отмена":
            del user_working_weight_data[user_id]
            await message.answer("Расчёт отменён.", keyboard=get_main_keyboard())
            return

        # Шаг 1: Ввод упражнения для обычного расчёта
        if step == "exercise":
            data["exercise"] = text
            data["step"] = "one_rm"
            await message.answer(
                f"Упражнение: {text}\n\n"
                "Введите ваш 1ПМ (одноповторный максимум) в кг:"
            )

        # Шаг 2: Ввод 1ПМ
        elif step == "one_rm":
            try:
                one_rm = float(text.replace(",", "."))
                if one_rm <= 0:
                    await message.answer("Вес должен быть больше 0 кг. Попробуйте снова:")
                    return
                data["one_rm"] = one_rm
                data["step"] = "reps"
                await message.answer(
                    f"1ПМ: {one_rm} кг\n\n"
                    "Сколько повторений вы планируете делать в подходе?\n"
                    "(введите число от 1 до 15)"
                )
            except ValueError:
                await message.answer("Ошибка! Введите число. Пример: 100")

        # Шаг 3: Ввод повторений
        elif step == "reps":
            try:
                reps = int(text)
                if reps < 1 or reps > 15:
                    await message.answer("Количество повторений должно быть от 1 до 15. Попробуйте снова:")
                    return
                data["reps"] = reps
                data["step"] = "experience"

                await message.answer(
                    f"Повторений: {reps}\n"
                    f"{get_reps_guide(reps)}\n\n"
                    "Выберите ваш уровень опыта:",
                    keyboard=get_experience_keyboard()
                )
            except ValueError:
                await message.answer("Ошибка! Введите число (1-15):")

        # Шаг 4: Уровень опыта
        elif step == "experience":
            if any(key in text for key in ["Новичок", "Средний", "Продвинутый"]):
                experience = get_experience_value(text)
                data["experience"] = experience

                one_rm = data["one_rm"]
                reps = data["reps"]
                exercise = data["exercise"]
                exercise_type = get_exercise_type(exercise)

                working_weight = calculate_working_weight(one_rm, reps, 1, experience, exercise)

                result = f"""
РЕЗУЛЬТАТ РАСЧЁТА РАБОЧЕГО ВЕСА

Упражнение: {exercise}
Тип упражнения: {exercise_type}
1ПМ: {one_rm} кг
Повторений: {reps}
Уровень опыта: {text}

Рекомендуемый рабочий вес: {working_weight} кг

{get_reps_guide(reps)}

Совет: Начните с разминочных подходов (50%, 70% от рабочего веса), затем 3-4 рабочих подхода.
"""
                await message.answer(result, keyboard=get_working_weight_keyboard())
                del user_working_weight_data[user_id]
            else:
                await message.answer("Пожалуйста, выберите уровень из кнопок.", keyboard=get_experience_keyboard())

        # Прогрессия по неделям - шаг 1: упражнение
        elif step == "progression_exercise":
            data["exercise"] = text
            data["step"] = "progression_one_rm"
            await message.answer(f"Упражнение: {text}\n\nВведите ваш 1ПМ в кг:")

        # Прогрессия - шаг 2: 1ПМ
        elif step == "progression_one_rm":
            try:
                one_rm = float(text.replace(",", "."))
                if one_rm <= 0:
                    await message.answer("Вес должен быть больше 0 кг. Попробуйте снова:")
                    return
                data["one_rm"] = one_rm
                data["step"] = "progression_reps"
                await message.answer(f"1ПМ: {one_rm} кг\n\nСколько повторений в подходе (1-12)?")
            except ValueError:
                await message.answer("Ошибка! Введите число.")

        # Прогрессия - шаг 3: повторения
        elif step == "progression_reps":
            try:
                reps = int(text)
                if reps < 1 or reps > 12:
                    await message.answer("Введите число от 1 до 12:")
                    return
                data["reps"] = reps
                data["step"] = "progression_weeks"
                await message.answer(
                    f"Повторений: {reps}\n\n"
                    "На сколько недель рассчитать прогрессию?\n"
                    "(обычно 4-8 недель, максимум 12)"
                )
            except ValueError:
                await message.answer("Ошибка! Введите число:")

        # Прогрессия - шаг 4: количество недель
        elif step == "progression_weeks":
            try:
                weeks = int(text)
                if weeks < 1 or weeks > 12:
                    await message.answer("Введите число от 1 до 12 недель:")
                    return

                one_rm = data["one_rm"]
                reps = data["reps"]
                exercise = data["exercise"]
                exercise_type = get_exercise_type(exercise)

                result = f"""
ПЛАН ПРОГРЕССИИ ДЛЯ {exercise.upper()}

Исходные данные:
• 1ПМ: {one_rm} кг
• Целевое количество повторений: {reps}
• Тип упражнения: {exercise_type}
• Длительность программы: {weeks} недель

НЕДЕЛЯ | РАБОЧИЙ ВЕС | ПРИМЕЧАНИЕ
"""
                for week in range(1, weeks + 1):
                    weight = calculate_working_weight(one_rm, reps, week, "intermediate", exercise)
                    if week == 1:
                        note = "Разминка обязательна"
                    elif week % 2 == 0:
                        note = "Прогрессия"
                    else:
                        note = "Адаптация"
                    result += f"Неделя {week:2} | {weight:5} кг | {note}\n"

                result += f"""

КАК РАБОТАТЬ ПО ПЛАНУ:
1. Каждую неделю используйте указанный рабочий вес
2. Делайте 3-4 подхода по {reps} повторений
3. Последнее повторение должно быть сложным, но чистым
4. Если легко делаете все подходы - на следующей неделе прогрессия
5. После {weeks} недель сделайте перерыв 1 неделю (легкий вес)

СОВЕТ: Всегда делайте 2-3 разминочных подхода (50% и 70% от рабочего веса)
"""
                await message.answer(result, keyboard=get_working_weight_keyboard())
                del user_working_weight_data[user_id]

            except ValueError:
                await message.answer("Ошибка! Введите число недель:")

        # Рекомендации по повторениям
        elif step == "recommendation":
            if text:
                result = get_reps_recommendation(text)
                result += f"\n\nДля упражнения: {text}"
                await message.answer(result, keyboard=get_working_weight_keyboard())
                del user_working_weight_data[user_id]
            else:
                await message.answer("Введите название упражнения:")

        return

    # АДМИНСКИЕ РЕЖИМЫ
    if user_id == ADMIN_ID:
        if editing_mode == "push":
            if text.lower() == "отмена":
                editing_mode = False
                await message.answer("Рассылка отменена.", keyboard=get_main_keyboard())
                return
            await message.answer("Начинаю рассылку...")
            success = 0
            fail = 0
            for uid in known_users:
                try:
                    await bot.api.messages.send(peer_id=uid, message=f"РАССЫЛКА:\n\n{text}", random_id=0)
                    success += 1
                except:
                    fail += 1
            await message.answer(
                f"Рассылка завершена!\nОтправлено: {success}\nНе доставлено: {fail}\nВсего: {len(known_users)}",
                keyboard=get_main_keyboard())
            editing_mode = False
            return

        elif editing_mode is True:
            if text.lower() == "отмена":
                editing_mode = False
                await message.answer("Режим редактирования выключен.", keyboard=get_main_keyboard())
                return
            days = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
            for day in days:
                if text.startswith(day + " -"):
                    new_time = text.replace(day + " -", "").strip()
                    if day == "ПН":
                        schedule_data["monday"] = f"ПН - {new_time}"
                    elif day == "ВТ":
                        schedule_data["tuesday"] = f"ВТ - {new_time}"
                    elif day == "СР":
                        schedule_data["wednesday"] = f"СР - {new_time}"
                    elif day == "ЧТ":
                        schedule_data["thursday"] = f"ЧТ - {new_time}"
                    elif day == "ПТ":
                        schedule_data["friday"] = f"ПТ - {new_time}"
                    elif day == "СБ":
                        schedule_data["saturday"] = f"СБ - {new_time}"
                    elif day == "ВС":
                        schedule_data["sunday"] = f"ВС - {new_time}"
                    await message.answer(f"Расписание на {day} обновлено: {new_time}")
                    editing_mode = False
                    return
            await message.answer("Неверный формат. Пример: ПН - 10:00 – 22:00")
            return

    # ========== ПОКАЗ ТЕХНИКИ УПРАЖНЕНИЙ С ФОТО ==========
    for key, exercise in TECHNIQUES.items():
        if text == exercise["name"]:
            image_path = exercise.get("image", "")

            # Проверяем, есть ли фото
            if image_path and os.path.exists(image_path):
                try:
                    # Загружаем фото
                    attachment = await photo_uploader.upload(
                        file_source=image_path,
                        peer_id=message.peer_id
                    )
                    await message.answer(
                        exercise["description"],
                        attachment=attachment
                    )
                except Exception as e:
                    print(f"Ошибка загрузки фото для {key}: {e}")
                    await message.answer(exercise["description"])
            else:
                await message.answer(exercise["description"])
            return

    # ПАРСИНГ ФОРМУЛ ДЛЯ 1ПМ
    if re.match(r"^\d+\.?\d*\s+\d+$", text):
        try:
            if user_id not in user_1rm_exercise:
                await message.answer(
                    "Сначала выберите упражнение!\n\n"
                    "Нажмите на кнопку «Расчёт 1ПМ»",
                    keyboard=get_main_keyboard()
                )
                return

            parts = text.split()
            weight = float(parts[0])
            reps = int(parts[1])

            if reps < 1 or reps > 36:
                await message.answer(
                    "Ошибка!\n\n"
                    "Количество повторений должно быть от 1 до 36.\n"
                    "Формула работает корректно до 10 повторений.\n\n"
                    "Попробуйте снова:"
                )
                return

            if weight <= 0:
                await message.answer("Ошибка! Вес должен быть больше 0 кг.")
                return

            rm = calculate_1rm(weight, reps)
            exercise = user_1rm_exercise[user_id]

            result_text = f"""
РЕЗУЛЬТАТ РАСЧЁТА 1ПМ

Упражнение: {exercise}
Вес в подходе: {weight} кг
Повторения: {reps} раз

Ваш одноповторный максимум: {int(rm)} кг
"""
            await message.answer(result_text, keyboard=get_1rm_result_keyboard())

        except ValueError:
            await message.answer(
                "Ошибка формата!\n\n"
                "Введите: вес повторения\n"
                "Пример: 100 8\n\n"
                "Попробуйте снова:"
            )
        except Exception as e:
            await message.answer(f"Ошибка: {str(e)}\n\nПопробуйте снова.")
        return


# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("Бот запущен и готов к работе!")
    print("Автор: Выскубов Никита")
    print("=" * 40)
    print(f"Администратор ID: {ADMIN_ID}")
    print(f"Загружено пользователей: {len(known_users)}")
    print("=" * 40)
    bot.run_forever()