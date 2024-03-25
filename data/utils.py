from data.tools import session_scope
from data.models import *
from sqlalchemy import select
import datetime


async def is_admin(user_id):
    admin = await Admin.get(employee_id=user_id)
    return admin is not None


async def make_employee(user_id, name, username):
    employee = await Employee.create(id=user_id, name=name, username=username)
    return employee


async def remove_employee(user_id):
    employee = await Employee.get(id=user_id)
    if employee:
        if await is_admin(user_id):
            await remove_admin(user_id)
        await employee.delete()
        return True
    return False


async def make_admin(user_id):
    admin = await Admin.create(employee_id=user_id)
    return admin


async def remove_admin(user_id):
    admin = await Admin.get(employee_id=user_id)
    if admin:
        await admin.delete()
        return True
    return False


async def add_user_to_pending(user_id, name, username):
    user = await WaitingUser.create(id=user_id, name=name, username=username)
    return user


async def get_pending_users():
    return await WaitingUser.all()


async def remove_user_from_pending(user_id):
    user = await WaitingUser.get(id=user_id)
    if user:
        await user.delete()
        return True
    return False


async def if_user_employee(user_id):
    employee = await Employee.get(id=user_id)
    return employee is not None


async def if_user_pending(user_id):
    user = await WaitingUser.get(id=user_id)
    return user is not None


async def make_employee_from_pending(user_id):
    user = await WaitingUser.get(id=user_id)
    if user:
        employee = await Employee.create(id=user.id, name=user.name,
                                         username=user.username)
        await user.delete()
        return employee
    return None


async def get_employees_without_admins():
    async with session_scope() as session:
        stmt = select(Employee).where(~Employee.id.in_(
            select(Admin.employee_id)))
        result = await session.execute(stmt)
        return result.scalars().unique().all()


async def get_admins():
    return await Admin.all()


async def get_employees():
    return await Employee.all()


async def get_employee(user_id):
    return await Employee.get(id=user_id)


async def get_sources():
    return await Source.all()


async def remove_source_from_db(source_id):
    source = await Source.get(id=source_id, is_deleted=False)
    if source:
        await source.update(is_deleted=True)
        return True
    return False


async def add_source_to_db(name):
    source = await Source.create(name=name)
    return source


async def get_countries():
    return await Country.filter_by(is_deleted=False)


async def remove_country_from_db(country_id):
    country = await Country.get(id=country_id, is_deleted=False)
    if country:
        await country.update(is_deleted=True)
        return True
    return False


async def add_country_to_db(name, flag):
    country = await Country.create(name=name, flag=flag)
    return country


async def remove_template_from_db(template_id):
    template = await Template.get(id=template_id, is_deleted=False)
    if template:
        await template.update(is_deleted=True)
        return True
    return False


async def add_template_to_db(name, percent, country_id):
    template = await Template.create(name=name.capitalize(),
                                     employee_percentage=percent,
                                     country_id=country_id)
    return template


async def get_templates():
    return await Template.filter_by(is_deleted=False)


async def get_country_by_id(country_id):
    return await Country.get(id=country_id, is_deleted=False)


async def get_template_by_id(template_id):
    return await Template.get(id=template_id, is_deleted=False)


async def get_templates_by_country_id(country_id):
    templates = await Template.filter_by(country_id=country_id,
                                         is_deleted=False)
    return templates


async def add_bk_to_db(profile_name, template_id, country_id):
    template = await get_template_by_id(template_id)
    country = await get_country_by_id(country_id)
    if not template or not country:
        return None
    bookmaker_employee_percentage = template.employee_percentage
    bookmaker = await Bookmaker.create(
        salary_percentage=bookmaker_employee_percentage,
        name=profile_name.capitalize(),
        template_id=template_id, country_id=country_id, bk_name=template.name)
    return bookmaker


async def get_bk_by_template_id(template_id):
    return await Bookmaker.filter_by(template_id=template_id,
                                     is_deleted=False)


async def get_bk_by_id(bk_id):
    return await Bookmaker.get(id=bk_id, is_deleted=False)


async def edit_bk_name(bk_id, new_name):
    bk = await get_bk_by_id(bk_id)
    if bk:
        await bk.update(name=new_name)
        return True
    return False


async def edit_bk_percent(bk_id, new_percent):
    bk = await get_bk_by_id(bk_id)
    if bk:
        await bk.update(salary_percentage=new_percent)
        return True
    return False


async def deactivate_bk(bk_id):
    bk = await get_bk_by_id(bk_id)
    if bk:
        await bk.update(is_active=False,
                        deactivated_at=datetime.datetime.now())
        return True
    return False


async def activate_bk(bk_id):
    bk = await get_bk_by_id(bk_id)
    if bk:
        await bk.update(is_active=True, deactivated_at=None)
        return True
    return False


async def is_bk_active(bk_id):
    bk = await get_bk_by_id(bk_id)
    if bk:
        return bk.is_active
    return False


async def delite_bk(bk_id):
    bk = await get_bk_by_id(bk_id)
    if bk:
        await bk.update(is_deleted=True)
        return True
    return False


async def add_wallet_to_db(wallet_name: str, wallet_type: str,
                           general_wallet_type: str, deposit: float,
                           country_id: int = None):
    wallet = await Wallet.create(name=wallet_name, wallet_type=wallet_type,
                                 general_wallet_type=general_wallet_type,
                                 deposit=deposit, country_id=country_id)
    return wallet


async def get_wallets():
    return await Wallet.filter_by(is_deleted=False)


async def get_wallets_by_country_id(country_id):
    wallets = await Wallet.filter_by(country_id=country_id, is_deleted=False)
    return wallets


async def get_wallets_by_wallet_type(wallet_type):
    wallets = await Wallet.filter_by(wallet_type=wallet_type,
                                     is_deleted=False)
    return wallets


async def get_wallet_by_id(wallet_id):
    return await Wallet.get(id=wallet_id, is_deleted=False)


async def remove_wallet_from_db(wallet_id):
    wallet = await Wallet.get(id=wallet_id, is_deleted=False)
    if wallet:
        await wallet.update(is_deleted=True)
        return True
    return False


async def edit_wallet_balans(wallet_id, adjustment_now):
    wallet = await get_wallet_by_id(wallet_id)
    if wallet:
        await wallet.update(adjustment=wallet.adjustment + adjustment_now)
        return True
    return False


async def edit_wallet_country_by_id(wallet_id, country_id):
    wallet = await get_wallet_by_id(wallet_id)
    if country_id == "O":
        country_id = None
        if wallet:
            await wallet.update(country_id=country_id, wallet_type="Общий")
            return True
    else:
        if wallet:
            await wallet.update(country_id=country_id, wallet_type="Страна")
            return True
    return False


async def create_transaction(sender_wallet_id, receiver_wallet_id,
                             sender_bk_id, receiver_bk_id, sum, sum_received,
                             from_, where):
    # print(sender_wallet_id, receiver_wallet_id, sender_bk_id, receiver_bk_id, sum, sum_received, from_, where)
    transaction = await Transaction.create(
        sender_wallet_id=sender_wallet_id,
        receiver_wallet_id=receiver_wallet_id,
        sender_bookmaker_id=sender_bk_id,
        receiver_bookmaker_id=receiver_bk_id,
        amount=sum,
        commission=sum - sum_received,
        from_=from_,
        where=where
    )
    return transaction


async def add_report_to_db(date, wrong_report_value, source, country, bk_name,
                           bk_login, placed, received, userid, nick_name):
    # Получаем объекты Source, Country и Bookmaker по их именам
    source_obj = await Source.get(name=source, is_deleted=False)
    country_obj = await Country.get(name=country, is_deleted=False)
    employee = await Employee.get(id=userid)
    errors = []
    if not employee:
        errors.append(f"Пользователь {nick_name} с id {userid} не найден")
    if not source_obj:
        errors.append(f"Источник {source} не найден")
    if not country_obj:
        errors.append(f"Страна {country} не найдена")
    if errors:
        return " ".join(errors)
    bk_name = bk_name.capitalize()
    bk_login = bk_login.capitalize()
    bookmaker_obj = await Bookmaker.get(name=bk_login,
                                        bk_name=bk_name,
                                        country_id=country_obj.id,
                                        is_active=True, is_deleted=False)
    if not bookmaker_obj:
        return f"Букмекер {bk_name} с логином {bk_login} в стране {country} с isActive=True не найден"

    # Создаем новый отчет
    report = await Report.create(
        date=date,
        is_error=wrong_report_value,
        source_id=source_obj.id,
        country_id=country_obj.id,
        bookmaker_id=bookmaker_obj.id,
        bet_amount=placed,
        return_amount=received,
        employee_id=employee.id,
    )

    return True


async def add_to_history(user_name, operation_type,
                         operation_description):
    history = await OperationHistory.create(
        user_name=user_name,
        operation_type=operation_type,
        operation_description=operation_description
    )
    return history


async def add_to_commission_history(user_name, commission,
                                    commission_type, commission_description):
    history = await CommissionHistory.create(
        user_name=user_name,
        commission=commission,
        commission_type=commission_type,
        commission_description=commission_description
    )
    return history


async def get_last_10_operations():
    operations = await OperationHistory.all()
    return operations[-10:]


async def get_last_10_commissions():
    commissions = await CommissionHistory.all()
    return commissions[-10:]


async def get_source_by_name(source_name):
    return await Source.get(name=source_name, is_deleted=False)


async def get_bookmakers_by_country(country_id):
    return await Bookmaker.filter_by(country_id=country_id, is_deleted=False)


async def get_report_by_id(report_id):
    return await Report.get(id=report_id, is_deleted=False)


# async def pay_all_salaries():
#     employees = await get_employees()
#     for employee in employees:
#         await employee.update(
#             adjustment=employee.adjustment - employee.get_balance())


async def update_employee_salary(employee_id, adjustment_now):
    employee = await get_employee(employee_id)
    if employee:
        await employee.update(adjustment=employee.adjustment + adjustment_now)


async def pay_employee_salary(employee_id):
    employee = await get_employee(employee_id)
    if employee:
        await employee.update(
            adjustment=employee.adjustment - employee.get_balance())


async def delete_report_by_id(report_id):
    report = await get_report_by_id(report_id)
    if report:
        await report.update(is_deleted=True)
        return True
    return False


async def get_bookmakers():
    return await Bookmaker.filter_by(is_deleted=False)


async def get_reports_by_period_and_employee(start_date,
                                             end_date, employee_id):
    reports = await Report.filter(Report.date >= start_date,
                                  Report.date <= end_date,
                                  Report.employee_id == employee_id,
                                  Report.is_deleted == False)
    return reports


# async def format_report_stats(reports):
#     if not reports:
#         return "Нет отчетов для выбранного периода."
#
#     output = "Список отчетов:\n"
#     for report in reports:
#         status_icon = "🔴" if report.is_error else "🟢"
#         output += f"{status_icon} Отчет №{report.id}\n"
#
#     return output


async def get_operations_by_period(start_date, end_date):
    operations = await OperationHistory.filter(
        OperationHistory.date >= start_date,
        OperationHistory.date <= end_date)
    return operations


async def get_commissions_by_period(start_date, end_date):
    commissions = await CommissionHistory.filter(
        CommissionHistory.date >= start_date,
        CommissionHistory.date <= end_date)
    return commissions


async def is_country_balance_positive(country_id):
    country = await Country.get(id=country_id, is_deleted=False)
    if country:
        return country.get_active_balance() > 0
    return False


async def is_wallet_balance_positive(wallet_id):
    wallet = await Wallet.get(id=wallet_id, is_deleted=False)
    if wallet:
        return wallet.get_balance() > 0
    return False


async def is_template_exists(country_id, template_name):
    template = await Template.get(name=template_name.capitalize(),
                                  country_id=country_id, is_deleted=False)
    return template is not None


async def is_bk_exists(template_id, country_id, bk_name, bk_login):
    bookmaker = await Bookmaker.get(name=bk_login.capitalize(),
                                    bk_name=bk_name.capitalize(),
                                    template_id=template_id,
                                    country_id=country_id, is_deleted=False)
    return bookmaker is not None
