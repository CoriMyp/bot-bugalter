import pandas as pd
from data.utils import *
import io
import openpyxl
fields_to_check = ['Дата', 'Источник', 'Страна', 'Букмекер',
                   'Профиль', 'Сумма Проставленных', 'Возврат',
                   'Является Ли Ошибочным', 'userID', 'nickName']


async def process_excel_file(file_path: str):
    # Чтение файла Excel
    df = pd.read_excel(file_path)
    df_copy = df.copy()  # Создание копии DataFrame
    df_copy[
        'Error'] = None  # Добавление столбца 'Error' со значением по умолчанию None
    # переводим дату в datetime
    df['Дата'] = pd.to_datetime(df['Дата'], errors='coerce')

    # Перебор строк DataFrame и добавление в базу данных
    for index, row in df.iterrows():

        # Проверка, что все поля не равны None
        if not all(row.get(field) is not None for field in fields_to_check):
            # Если хотя бы одно поле равно None, находим эти поля и возвращаем
            missing_fields = [field for field in fields_to_check if
                              row.get(field) is None]
            error_message = f"Не хватает полей: {', '.join(missing_fields)}"
            df_copy.at[
                index, 'Error'] = error_message  # Обновление столбца 'Error' в df_copy
            continue

        # Удаление всех пробелов из строки
        cleaned_value = row['Является Ли Ошибочным'].replace(" ", "")

        # Проверка на "да" или "Да" без пробелов
        wrong_report_value = 1 if cleaned_value.lower() == "да" else 0

        date = row.get('Дата')
        source = row.get('Источник')
        country = row.get('Страна')
        bk_name = row.get('Букмекер')
        bk_login = row.get('Профиль')
        placed = row.get('Сумма Проставленных')
        received = row.get('Возврат')
        userid = row.get('userID')
        nick_name = row.get('nickName')

        # Добавление строки в базу данных
        ans = await add_report_to_db(date, wrong_report_value,
                                     source,
                                     country, bk_name, bk_login, placed,
                                     received, userid, nick_name)
        if ans != True:
            df_copy.at[
                index, 'Error'] = ans  # Обновление столбца 'Error' в df_copy

    # Фильтрация df_copy для включения только строк с ошибками
    df_errors = df_copy[df_copy['Error'].notna()]

    # Запись df_errors в файл 'errors.xlsx'
    df_errors.to_excel('errors.xlsx', index=False)

    # Возвращение True, если df_errors пуст
    return df_errors.empty



async def export_reports_to_excel(reports, start_date, end_date):
    # Создание Excel файла и заполнение данными
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["Номер отчета", "Статус", "Username", "Дата отчета",
                  "Сумма проставленных",
                  "Сумма возврата", "Профит", "Зарплата за отчет", "Источник",
                  "Страна", "БК", "Профиль", "Название матча"])
    for report in reports:
        sheet.append([
            report.id,
            "Не ошибочный" if not report.is_error else "Ошибочный",
            report.employee.username,
            report.date.strftime('%d.%m.%Y %H:%M'),
            report.bet_amount,
            report.return_amount,
            report.profit,
            report.salary,
            report.source.name,
            report.country.name,
            report.bookmaker.name,
            report.nickname,
            report.match_name
        ])

    # Сохранение файла в байт-код
    excel_file = io.BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)
    return excel_file