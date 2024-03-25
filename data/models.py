from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, \
    Boolean, func
from sqlalchemy.orm import relationship
from data.base import Model
from sqlalchemy.ext.hybrid import hybrid_property
import datetime

"""Database models:
- Country
- Bookmaker
- Wallet
- Employee
- Transaction
- Report
- Source
- Admin
- Template
- WaitingUser
- OperationHistory
"""


class Country(Model):
    """
    Модель страны

    Поля:
    id -- уникальный идентификатор страны
    name -- название страны
    commission -- комиссия страны
    transactions -- список транзакций, связанных со страной
    bookmakers -- список букмекеров, связанных со страной
    wallets -- список кошельков, связанных со страной
    reports -- список отчетов, связанных со страной
    templates -- список шаблонов отчетов, связанных со страной
    flag -- флаг страны
    is_deleted -- статус удаления страны
    """
    __tablename__ = "country"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    commission = Column(Float, default=0)
    transactions = relationship('Transaction', back_populates='country',
                                lazy='joined')
    bookmakers = relationship('Bookmaker', back_populates='country',
                              lazy='joined')
    wallets = relationship('Wallet', back_populates='country', lazy='joined')
    reports = relationship('Report', back_populates='country')
    templates = relationship('Template', back_populates='country')
    flag = Column(String)
    is_deleted = Column(Boolean, default=False)

    def get_active_balance(self):
        """
        Получение баланса страны

        Баланс страны рассчитывается как сумма балансов всех букмекеров и кошельков, связанных со страной.
        """
        bookmakers_balance = 0
        for bookmaker in self.bookmakers:
            if not bookmaker.is_deleted:
                bookmakers_balance += bookmaker.get_balance()
        wallets_balance = 0
        for wallet in self.wallets:
            if not wallet.is_deleted:
                wallets_balance += wallet.get_balance()
        return bookmakers_balance + wallets_balance

    def get_balance(self):
        """
        Получение пассивного баланса страны

        Пассивный баланс страны рассчитывается как сумма депозитов всех букмекеров, связанных со страной.
        """
        bookmakers_balance = 0
        for bookmaker in self.bookmakers:
            if bookmaker.is_active:
                bookmakers_balance += bookmaker.get_deposit()
        return bookmakers_balance


class Bookmaker(Model):
    """
    Модель букмекера

    Поля:
    id -- уникальный идентификатор букмекера
    name -- название профиля
    country_id -- идентификатор страны, связанной с букмекером
    country -- страна, связанная с букмекером
    salary_percentage -- процент зарплаты сотрудника
    transactions_sender -- список транзакций, где букмекер является отправителем
    transactions_receiver -- список транзакций, где букмекер является получателем
    reports -- список отчетов, связанных с букмекером
    is_active -- статус активности букмекера
    deactivated_at -- дата деактивации букмекера(по истечению 3 месяцев после деактивации букмекера он не будет использоваться в статистике)
    template_id -- идентификатор шаблона к которому привязан букмекер
    template -- шаблон, к которому привязан букмекер
    bk_name -- название букмекера взятое из шаблона при создании букмекера
    is_deleted -- статус удаления букмекера

    """
    __tablename__ = "bookmaker"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    country_id = Column(Integer, ForeignKey('country.id'))
    country = relationship('Country', back_populates='bookmakers',
                           lazy='joined')
    salary_percentage = Column(Float)
    transactions_sender = relationship('Transaction',
                                       back_populates='sender_bookmaker',
                                       foreign_keys='Transaction.sender_bookmaker_id',
                                       lazy='joined')
    transactions_receiver = relationship('Transaction',
                                         back_populates='receiver_bookmaker',
                                         foreign_keys='Transaction.receiver_bookmaker_id',
                                         lazy='joined')
    reports = relationship('Report', back_populates='bookmaker',
                           lazy='subquery')
    is_active = Column(Boolean, default=True)
    deactivated_at = Column(DateTime)
    template_id = Column(Integer, ForeignKey('template.id'))
    template = relationship('Template', back_populates='bookmakers',
                            lazy='joined')
    bk_name = Column(String)
    is_deleted = Column(Boolean, default=False)

    def get_deposit(self):
        """Депозит букмекера"""
        transactions_balance = 0
        for transaction in [t for t in self.transactions_sender if
                            t.from_ == "deposit"]:
            transactions_balance -= transaction.amount
        for transaction in [t for t in self.transactions_receiver if
                            t.where == "deposit"]:
            transactions_balance += transaction.real_amount
        return transactions_balance

    def get_balance(self):
        """
        Получение баланса букмекера

        Баланс букмекера рассчитывается как сумма его депозита, транзакций и отчетов.
        """
        reports_balance = 0
        for report in self.reports:
            if not report.is_deleted:
                reports_balance += report.real_profit
        transactions_balance = 0
        for transaction in [t for t in self.transactions_sender if
                            t.from_ == "balance"]:
            transactions_balance -= transaction.amount
        for transaction in [t for t in self.transactions_receiver if
                            t.where == "balance"]:
            transactions_balance += transaction.real_amount
        return self.get_deposit() + reports_balance + transactions_balance


class Wallet(Model):
    """
    Модель кошелька

    Поля:
    id -- уникальный идентификатор кошелька
    name -- название кошелька
    general_wallet_type -- тип кошелька(Binance или Карта)
    wallet_type -- тип кошелька(Страна или Общий)
    country_id -- идентификатор страны, связанной с кошельком
    country -- страна, связанная с кошельком
    deposit -- депозит кошелька
    transactions_sender -- список транзакций, где кошелек является отправителем
    transactions_receiver -- список транзакций, где кошелек является получателем
    adjustment -- корректировка баланса кошелька
    is_deleted -- статус удаления кошелька

    """
    __tablename__ = "wallet"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    general_wallet_type = Column(String)
    wallet_type = Column(String)
    country_id = Column(Integer, ForeignKey('country.id'))
    country = relationship('Country', back_populates='wallets', lazy='joined')
    deposit = Column(Float)
    transactions_sender = relationship('Transaction',
                                       back_populates='sender_wallet',
                                       foreign_keys='Transaction.sender_wallet_id',
                                       lazy='joined')
    transactions_receiver = relationship('Transaction',
                                         back_populates='receiver_wallet',
                                         foreign_keys='Transaction.receiver_wallet_id',
                                         lazy='joined')
    adjustment = Column(Float, default=0)
    is_deleted = Column(Boolean, default=False)

    def get_balance(self):
        """
        Получение баланса кошелька

        Баланс кошелька рассчитывается как сумма его депозита, суммы всех входящих транзакций и корректировки, минус сумма всех исходящих транзакций.
        """
        sender_transactions = sum(transaction.amount for transaction in
                                  self.transactions_sender)
        receiver_transactions = sum(transaction.real_amount for transaction in
                                    self.transactions_receiver)
        return self.deposit + receiver_transactions - sender_transactions + self.adjustment


class Employee(Model):
    """
    Модель сотрудника

    Поля:
    id -- уникальный идентификатор сотрудника в телеграм
    name -- имя сотрудника
    adjustment -- корректировка баланса сотрудника
    reports -- список отчетов, связанных с сотрудником
    username -- имя пользователя в телеграм
    """
    __tablename__ = "employee"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    adjustment = Column(Float, default=0)

    reports = relationship('Report', back_populates='employee', lazy='joined')
    username = Column(String)

    def salary(self):
        """
        Расчет зарплаты сотрудника

        Зарплата сотрудника рассчитывается как сумма зарплат по всем отчетам.
        """
        salary_sum = 0
        for report in self.reports:
            if not report.is_error and not report.is_deleted:
                salary_sum += report.salary
        return salary_sum

    def penalty(self):
        """
        Расчет штрафа сотрудника

        Штраф сотрудника рассчитывается как сумма штрафов по всем отчетам.
        """
        penalty_sum = 0
        for report in self.reports:
            if not report.is_deleted:
                penalty_sum += report.penalty
        return penalty_sum

    def get_balance(self):
        """
        Получение баланса сотрудника

        Баланс сотрудника рассчитывается как сумма всех транзакций, связанных с сотрудником, плюс корректировка, плюс зарплата, минус штраф.
        """

        return self.adjustment + self.salary() - self.penalty()


class Transaction(Model):
    """
    Модель транзакции

    Поля:
    id -- уникальный идентификатор транзакции
    amount -- сумма транзакции
    commission -- комиссия транзакции (число которое вычитается из суммы транзакции)
    sender_wallet_id -- идентификатор кошелька отправителя
    sender_wallet -- кошелек отправителя
    sender_bookmaker_id -- идентификатор букмекера, связанного с транзакцией
    sender_bookmaker -- букмекер, связанный с транзакцией
    receiver_wallet_id -- идентификатор кошелька получателя
    receiver_wallet -- кошелек получателя
    receiver_bookmaker_id = идентификатор букмекера, связанного с транзакцией
    receiver_bookmaker = букмекер, связанный с транзакцией
    bookmaker_id -- идентификатор букмекера, связанного с транзакцией
    bookmaker -- букмекер, связанный с транзакцией
    country_id -- идентификатор страны, связанной с транзакцией
    country -- страна, связанная с транзакцией
    transaction_type -- тип транзакции
    timestamp -- дата и время транзакции
    is_deleted -- статус удаления транзакции (не используется)
    """
    __tablename__ = "transaction"
    id = Column(Integer, primary_key=True)
    from_ = Column(String)
    where = Column(String)
    amount = Column(Float)
    commission = Column(Float, default=0)
    sender_wallet_id = Column(Integer,
                              ForeignKey('wallet.id'))  # кошелек отправителя
    sender_wallet = relationship('Wallet',
                                 back_populates='transactions_sender',
                                 foreign_keys=[sender_wallet_id])
    sender_bookmaker_id = Column(Integer, ForeignKey('bookmaker.id'))
    sender_bookmaker = relationship('Bookmaker',
                                    back_populates='transactions_sender',
                                    foreign_keys=[sender_bookmaker_id])

    receiver_wallet_id = Column(Integer,
                                ForeignKey('wallet.id'))  # кошелек получателя
    receiver_wallet = relationship('Wallet',
                                   back_populates='transactions_receiver',
                                   foreign_keys=[receiver_wallet_id])
    receiver_bookmaker_id = Column(Integer, ForeignKey('bookmaker.id'))
    receiver_bookmaker = relationship('Bookmaker',
                                      back_populates='transactions_receiver',
                                      foreign_keys=[receiver_bookmaker_id])
    country_id = Column(Integer, ForeignKey('country.id'))
    country = relationship('Country', back_populates='transactions')
    transaction_type = Column(String)
    timestamp = Column(DateTime)
    is_deleted = Column(Boolean, default=False)

    @property
    def real_amount(self):
        """Реальная сумма транзакции"""
        if not self.commission:
            return self.amount
        return self.amount - self.commission


class Report(Model):
    """
    Модель отчета

    Поля:
    id -- уникальный идентификатор отчета
    date -- дата отчета
    source_id -- идентификатор источника, связанного с отчетом
    source -- источник, связанный с отчетом
    country_id -- идентификатор страны, связанной с отчетом
    country -- страна, связанная с отчетом
    bookmaker_id -- идентификатор букмекера, связанного с отчетом
    bookmaker -- букмекер, связанный с отчетом
    match_name -- название матча
    nickname -- никнейм
    bet_amount -- сумма ставки
    return_amount -- сумма возврата
    salary_percentage -- процент зарплаты
    employee_id -- идентификатор сотрудника, связанного с отчетом
    employee -- сотрудник, связанный с отчетом
    is_error -- статус ошибки в отчете
    is_deleted -- статус удаления отчета
    """
    __tablename__ = "report"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    source_id = Column(Integer, ForeignKey('source.id'))
    source = relationship('Source', back_populates='reports', lazy='joined')
    country_id = Column(Integer, ForeignKey('country.id'))
    country = relationship('Country', back_populates='reports',
                           lazy='joined')
    bookmaker_id = Column(Integer, ForeignKey('bookmaker.id'))
    bookmaker = relationship('Bookmaker', back_populates='reports',
                             lazy='joined')
    match_name = Column(String)
    nickname = Column(String)
    bet_amount = Column(Float)
    return_amount = Column(Float)
    _salary_percentage = Column(Float)
    employee_id = Column(Integer, ForeignKey('employee.id'))
    employee = relationship('Employee', back_populates='reports',
                            lazy='joined')
    is_error = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    # задаем комиссию из бк если она не задана
    @hybrid_property
    def salary_percentage(self):
        if self._salary_percentage is not None:
            return self._salary_percentage
        elif self.bookmaker is not None:
            return self.bookmaker.salary_percentage
        else:
            return 0

    @salary_percentage.expression
    def salary_percentage(cls):
        return func.coalesce(cls._salary_percentage,
                             Bookmaker.salary_percentage, 0)

    @salary_percentage.setter
    def salary_percentage(self, value):
        self._salary_percentage = value

    @property
    def profit(self):
        """Прибыль отчета"""

        return self.return_amount - self.bet_amount

    @property
    def salary(self):
        """Зарплата за отчет"""
        if not self.is_error:
            return self.bet_amount * self.salary_percentage / 100
        else:
            return 0

    @property
    def penalty(self):
        """Штраф за ошибку в отчете"""
        if self.is_error and self.profit < 0:
            return abs(self.profit) * 3 * self.salary_percentage / 100
        else:
            return 0

    @property
    def real_profit(self):
        """Реальная прибыль отчета"""
        # return self.profit - self.salary
        return self.profit

    @property
    def real_salary(self):
        """Реальная зарплата за отчет"""
        return self.salary - self.penalty


class Source(Model):
    """
    Модель источника

    Поля:
    id -- уникальный идентификатор источника
    name -- название источника
    reports -- список отчетов, связанных с источником
    is_deleted -- статус удаления источника
    """
    __tablename__ = "source"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    reports = relationship('Report', back_populates='source')
    is_deleted = Column(Boolean, default=False)


class Admin(Model):
    """
    Модель админа

    Поля:
    id -- уникальный идентификатор админа
    employee_id -- идентификатор сотрудника, который является админом
    employee -- сотрудник, который является админом
    """
    __tablename__ = "admin"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employee.id'))
    employee = relationship('Employee', backref='admins_employee')


class Template(Model):
    """
    Модель шаблона отчета

    Поля:
    id -- уникальный идентификатор шаблона отчета
    name -- название шаблона отчета
    country_id -- идентификатор страны, связанной с шаблоном отчета
    country -- страна, связанная с шаблоном отчета
    employee_percentage -- процент зарплаты сотрудника
    bookmakers -- список букмекеров, связанных с шаблоном
    is_deleted -- статус удаления шаблона отчета
    """
    __tablename__ = "template"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    country_id = Column(Integer, ForeignKey('country.id'))
    country = relationship('Country', back_populates='templates')
    employee_percentage = Column(Float)
    bookmakers = relationship('Bookmaker', back_populates='template',
                              lazy='joined')
    is_deleted = Column(Boolean, default=False)


class WaitingUser(Model):
    """
    Модель ожидающих пользователей

    Поля:
    id -- уникальный идентификатор пользователя
    name -- имя пользователя
    username -- имя пользователя в телеграм
    """
    __tablename__ = "waiting_Users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    username = Column(String)


class OperationHistory(Model):
    """
    Модель истории операций

    Поля:
    id -- уникальный идентификатор операции
    date -- дата и время операции
    user_name -- имя пользователя, выполнившего операцию
    operation_type -- тип операции
    operation_description -- описание операции
    """
    __tablename__ = "operation_history"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    user_name = Column(String)
    operation_type = Column(String)
    operation_description = Column(String)


class CommissionHistory(Model):
    """
    Модель истории комиссий

    Поля:
    id -- уникальный идентификатор комиссии
    date -- дата и время комиссии
    user_name -- имя пользователя, выполнившего комиссию
    commission -- сумма комиссии
    commission_type -- тип комиссии
    commission_description -- описание комиссии
    """
    __tablename__ = "commission_history"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    user_name = Column(String)
    commission = Column(Float)
    commission_type = Column(String)
    commission_description = Column(String)
