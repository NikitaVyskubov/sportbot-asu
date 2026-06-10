# keyboards.py
from vkbottle import Keyboard, KeyboardButtonColor, Text, Callback


# ========== ОСНОВНАЯ КЛАВИАТУРА ==========
def get_main_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("💪 Техника тренажеров"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🍽 Калькулятор калоража"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("🥗 Советы по питанию"), color=KeyboardButtonColor.SECONDARY)
    keyboard.row()
    keyboard.add(Text("🏆 Расчёт 1ПМ"), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text("⚡ Рабочий вес"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🕐 Расписание зала"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("📚 Дополнительная литература"), color=KeyboardButtonColor.SECONDARY)
    return keyboard


# ========== КЛАВИАТУРЫ ДЛЯ ТЕХНИКИ ==========
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


def get_machines_keyboard(category_name):
    from techniques import TECHNIQUES, CATEGORIES
    keyboard = Keyboard(one_time=False, inline=False)
    for machine_key in CATEGORIES.get(category_name, []):
        machine = TECHNIQUES.get(machine_key, {})
        if machine:
            keyboard.add(Text(machine["name"]), color=KeyboardButtonColor.PRIMARY)
            keyboard.row()
    keyboard.add(Text("◀️ Назад к категориям"), color=KeyboardButtonColor.SECONDARY)
    return keyboard


# ========== КЛАВИАТУРЫ ДЛЯ 1ПМ ==========
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


# ========== КЛАВИАТУРА АДМИНИСТРАТОРА ==========
def get_admin_schedule_keyboard():
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("✏️ Редактировать расписание"), color=KeyboardButtonColor.PRIMARY)
    return keyboard