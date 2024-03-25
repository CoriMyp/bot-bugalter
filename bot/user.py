from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from bot.keyboards import *
from bot.utils import *
from bot.states import *
from data.statistic import *


async def start(message: types.Message):
    if await is_admin(message.from_user.id):
        await message.answer("Привет, админ!",
                             reply_markup=main_menu_keyboard)
        return
    if await if_user_employee(message.from_user.id):
        await message.answer("Привет, сотрудник!👋",
                             reply_markup=emploee_main_menu_keyboard)
        return
    if await if_user_pending(message.from_user.id):
        await message.answer("Не нужно, вы уже в списке ожидания")
        return
    await message.answer("Hello, I'm a bot!")

    # Сохранем пользователя в список ожидающих подтверждения
    ans = await add_user_to_pending(message.from_user.id,
                                    message.from_user.full_name,
                                    message.from_user.username)
    if ans:
        await message.answer("Вы добавлены в список ожидания!")
    else:
        await message.answer("Произошла чудовищная ошибка😭")


@employee_required
async def get_balance_info(message: types.Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не сотрудник")
        return
    await message.answer(f"Ваш баланс: {employee.get_balance()}")


@employee_required
async def get_reports_history(message: types.Message):
    await message.answer("Введи период в формате ДД.ММ.ГГГГ-ДД.ММ.ГГГГ")
    await UserStates.waiting_for_period.set()


@employee_required
async def watch_reports(message: types.Message, state: FSMContext):
    period = message.text

    try:
        start_date, end_date = period.split("-")
        start_date = datetime.strptime(start_date, "%d.%m.%Y").date()
        end_date = datetime.strptime(end_date, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Неверный формат даты")
        return
    employee_id = message.from_user.id
    reports = await get_reports_by_period_and_employee(start_date, end_date,
                                                       employee_id)
    if reports:
        keyboard = await format_report_stats(reports)
        await message.answer("Выберите отчет", reply_markup=keyboard)
        await message.answer("Введите номер отчета для просмотра деталей:")
        await UserStates.waiting_for_report_number.set()
    else:
        await message.answer("Нет отчетов для выбранного периода.")
        await state.finish()


@employee_required
async def go_to_main_menu(message: types.Message):
    await message.answer("Главное меню",
                         reply_markup=emploee_main_menu_keyboard)


@employee_required
async def show_report_details(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    try:
        report_number = int(call.data.split("_|_")[1])
        report = await get_report_by_id(report_number)
        if report:
            output = await format_report_details(report)
            await call.message.answer(output)
        else:
            await call.message.answer("Отчет не найден.")
    except ValueError:
        await call.message.answer(
            "Неверный формат номера отчета. Введите число.")
    finally:
        await state.finish()


def register_user_handlers(dp):
    dp.register_message_handler(go_to_main_menu, lambda
        message: message.text == "Отмена", state="*")
    dp.register_message_handler(start, Command("start"))
    dp.register_message_handler(get_reports_history, lambda
        message: message.text == "📝 Мои отчеты", state="*")
    dp.register_message_handler(watch_reports,
                                state=UserStates.waiting_for_period)
    dp.register_message_handler(get_balance_info, lambda
        message: message.text == "📊 Баланс", state="*")
    dp.register_callback_query_handler(show_report_details,
                                       lambda call: call.data.startswith(
                                           "report_details_"))
