import enum
from lib2to3.pgen2.driver import Driver

from Tools.scripts.generate_opcode_h import header
from sqlalchemy import create_engine, select, ForeignKey, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship
from datetime import date, datetime
import sys
from pathlib import Path
from sqlalchemy import create_engine


class OwnershipType(enum.Enum):
    OWNED = 1  # собственность
    JOINT = 2  # совместная собственность супругов
    RENT = 3  # аренда
    LEASING = 4  # лизинг
    FREE_USE = 5  # безвозмездное пользование

class CarType(enum.Enum):
    CARGO = "Грузовой автомобиль"
    PASSENGER = "Легковой автомобиль"
    SPECIAL_CARGO = "Специальный грузовой автомобиль"
    TRUCK = "Седельный тягач"
    TRAILER = "Грузовой прицеп"
    SEMI_TRAILER = "Грузовой полуприцеп"

class DBAgent:
    def __init__(self, debug=False):
        # 1. Определяем директорию, где находится сама программа
        if getattr(sys, 'frozen', False):
            # Если программа скомпилирована в .exe (в папке или одним файлом - неважно)
            # sys.executable укажет на полный путь к .exe, а .parent возьмет его папку
            BASE_DIR = Path(sys.executable).parent
        else:
            # Если мы запускаем обычный .py скрипт через Python
            # __file__ указывает на скрипт, а .parent берет папку, где он лежит
            BASE_DIR = Path(__file__).parent

        # 2. Формируем абсолютный путь к файлу БД
        db_path = BASE_DIR / "database/database.db"
        self.engine = create_engine(f'sqlite:///{db_path}', echo=debug)

    class Base(DeclarativeBase):
        pass

    class Driver(Base):
        __tablename__ = 'drivers'
        id: Mapped[int] = mapped_column(primary_key=True)
        first_name: Mapped[str] = mapped_column()
        last_name: Mapped[str] = mapped_column()
        patronymic: Mapped[str] = mapped_column()
        phone_number: Mapped[str] = mapped_column()
        employer_id: Mapped[int] = mapped_column(ForeignKey('employers.id'))
        employer: Mapped["Employer"] = relationship(back_populates="drivers")
        license: Mapped["License"] = relationship(back_populates="driver", cascade="all, delete-orphan")

    class License(Base):
        __tablename__ = 'licenses'
        id: Mapped[int] = mapped_column(primary_key=True)
        series: Mapped[str] = mapped_column()
        number: Mapped[str] = mapped_column()
        issue_date: Mapped[date] = mapped_column()
        driver_id: Mapped[int] = mapped_column(ForeignKey('drivers.id'), unique=True)
        driver: Mapped["Driver"] = relationship(back_populates="license")

    class Employer(Base):
        __tablename__ = 'employers'
        id: Mapped[int] = mapped_column(primary_key=True)
        last_name: Mapped[str] = mapped_column()
        drivers: Mapped[list["Driver"]] = relationship(back_populates="employer")
        owned_cars: Mapped[list["Car"]] = relationship(back_populates="owner")

    class Car(Base):
        __tablename__ = 'cars'
        id: Mapped[int] = mapped_column(primary_key=True)
        number: Mapped[str] = mapped_column()
        brand: Mapped[str] = mapped_column()
        car_type: Mapped[CarType] = mapped_column()
        load_capacity: Mapped[float] = mapped_column()
        volume: Mapped[float] = mapped_column()
        ownership_type: Mapped[OwnershipType] = mapped_column()
        owner_id: Mapped[int] = mapped_column(ForeignKey('employers.id'))
        owner: Mapped["Employer"] = relationship(back_populates="owned_cars")

    def create(self):
        self.Base.metadata.create_all(self.engine)

    def populate_test_data(self):
        # Импорты можно вынести в самое начало файла
        from sqlalchemy.orm import Session
        from sqlalchemy import select
        from datetime import date

        with Session(self.engine) as session:
            # 1. Защита от дубликатов: проверяем, есть ли уже данные в базе
            if session.scalars(select(self.Employer)).first():
                print("Данные уже существуют. Пропускаем заполнение.")
                return

            print("Заполняем базу тестовыми данными...")

            # 2. Создаем двух нанимателей
            emp1 = self.Employer(last_name="Яндекс.Такси")
            emp2 = self.Employer(last_name="Ситимобил")

            # 3. Создаем 4 водителей
            driver1 = self.Driver(first_name="Иван", last_name="Иванов", patronymic="Иванович",
                                  phone_number="89991112233")
            driver2 = self.Driver(first_name="Петр", last_name="Петров", patronymic="Петрович",
                                  phone_number="89994445566")

            driver3 = self.Driver(first_name="Алексей", last_name="Смирнов", patronymic="Алексеевич",
                                  phone_number="89997778899")
            driver4 = self.Driver(first_name="Дмитрий", last_name="Соколов", patronymic="Дмитриевич",
                                  phone_number="89990001122")

            car1 = self.Car(number="K453MT154", brand="GAZ", car_type=CarType.CARGO, load_capacity="1.5", volume="10", ownership_type=OwnershipType.OWNED)

            emp1.owned_cars = [car1]

            # 4. Привязываем водителей к нанимателям (Связь: Один ко многим)
            emp1.drivers = [driver1, driver2]
            emp2.drivers = [driver3, driver4]

            # 5. Создаем 4 лицензии и СРАЗУ привязываем их к водителям (Связь: Один к одному)
            driver1.license = self.License(series="1122", number="123456", issue_date=date(2020, 5, 15))
            driver2.license = self.License(series="3344", number="654321", issue_date=date(2018, 10, 20))
            driver3.license = self.License(series="5566", number="111222", issue_date=date(2022, 1, 10))
            driver4.license = self.License(series="7788", number="333444", issue_date=date(2015, 8, 30))

            # 6. МАГИЯ SQLAlchemy: добавляем только нанимателей!
            # Так как водители привязаны к нанимателям, а лицензии к водителям,
            # SQLAlchemy по цепочке (cascade) сохранит вообще всё.
            session.add_all([emp1, emp2])
            session.commit()

            print("База успешно заполнена!")

    def get_driver_info_by_last_name(self, target_last_name: str):
        from sqlalchemy.orm import Session
        from sqlalchemy import select

        with Session(self.engine) as session:
            # Ищем водителя по фамилии (если их может быть несколько, используйте .scalars().all() и цикл for)
            stmt = select(self.Driver).where(self.Driver.last_name == target_last_name)

            # Берем первого найденного
            driver = session.scalar(stmt)

            if not driver:
                print(f"Водитель с фамилией '{target_last_name}' не найден в базе.\n")
                return

            # 2. Безопасно достаем данные лицензии (на случай, если её вдруг нет)
            if driver.license:
                vu_series = driver.license.series
                vu_number = driver.license.number
                vu_date = driver.license.issue_date#.strftime("%d.%m.%Y")  # Красивый формат даты
            else:
                vu_series = vu_number = vu_date = "Нет ВУ"

            # 3. Безопасно достаем нанимателя
            employer = driver.employer.last_name if driver.employer else "Без нанимателя"

            return {
                "last_name": driver.last_name,
                "first_name": driver.first_name,
                "patronymic": driver.patronymic,
                "phone_number": driver.phone_number,
                "series": vu_series,
                "number": vu_number,
                "issue_date": vu_date,
                "employer": employer
            }

    def get_car_info_by_number(self, target_number: str):
        from sqlalchemy.orm import Session
        from sqlalchemy import select
        with Session(self.engine) as session:
            stmt = select(self.Car).where(self.Car.number == target_number)
            car = session.scalar(stmt)
            if not car:
                print(f"Автомобиль с номером '{target_number}' не найден в базе.\n")
                return
            return {
                "number": car.number,
                "brand": car.brand,
                "car_type": car.car_type,
                "load_capacity": car.load_capacity,
                "volume": car.volume,
                "ownership_type": car.ownership_type,
                "owner": car.owner.last_name
            }

    def get_columns_from_table(self, table: str):
        inspector = None
        match table:
            case "drivers":
                inspector = inspect(self.Driver)
            case "cars":
                inspector = inspect(self.Car)
        return [column.key for column in inspector.columns]

    def get_drivers_for_table(self) -> tuple[list[str], list[tuple]]:
        headers = ["ID", "Фамилия", "Имя", "Отчество", "Телефон", "ВУ Серия", "ВУ Номер", "ВУ Дата", "Наниматель"]
        table_data = []
        with Session(self.engine) as session:
            drivers = session.scalars(select(self.Driver)).all()
            for d in drivers:
                if d.license:
                    vu_series = d.license.series
                    vu_number = d.license.number
                    vu_date = d.license.issue_date.strftime("%d.%m.%Y")
                else:
                    vu_series = "Нет данных"
                    vu_number = "Нет данных"
                    vu_date = "-"
                employer = d.employer.last_name if d.employer else "Нет данных"

                row = (d.id, d.last_name, d.first_name, d.patronymic, d.phone_number, vu_series, vu_number, vu_date, employer)
                table_data.append(row)
        return headers, table_data

    def get_cars_for_table(self) -> tuple[list[str], list[tuple]]:
        headers = ["ID", "Гос. номер", "Марка", "Тип", "Грузоподъемность", "Вместимость", "Тип владения", "Владелец"]
        table_data = []
        with Session(self.engine) as session:
            cars = session.scalars(select(self.Car)).all()
            for c in cars:
                owner = c.owner.last_name if c.owner else "Нет данных"
                row = (c.id, c.number, c.brand, c.car_type.value, c.load_capacity, c.volume, c.ownership_type.name, owner)
                table_data.append(row)
        return headers, table_data

    def __find_col(self, col_name: str, model_class: int):
        match model_class:
            case 1:
                headers = ["ID", "Фамилия", "Имя", "Отчество", "Телефон", "ВУ Серия", "ВУ Номер", "ВУ Дата", "Наниматель"]
                match headers.index(col_name):
                    case 1: return "last_name", 1
                    case 2: return "first_name", 1
                    case 3: return "patronymic", 1
                    case 4: return "phone_number", 1
                    case 5: return "series", 3
                    case 6: return "number", 3
                    case 7: return "issue_date", 3
                    case 8: return "employer", 4
            case 2:
                headers = ["ID", "Гос. номер", "Марка", "Тип", "Грузоподъемность", "Вместимость", "Тип владения", "Владелец"]
                match headers.index(col_name):
                    case 1: return "number", 2
                    case 2: return "brand", 2
                    case 3: return "car_type", 2
                    case 4: return "load_capacity", 2
                    case 5: return "volume", 2
                    case 6: return "ownership_type", 2
                    case 7: return "owner", 4
        return "", 0

    def update_cell(self, model_class: int, item_id: int, col_name: str, new_value):
        column_name, model_num = self.__find_col(col_name, model_class)
        model = None
        match model_num:
            case 1: model = self.Driver
            case 2: model = self.Car
            case 3: model = self.License
            case 4: model = self.Employer
        with Session(self.engine) as session:
            # 1. Находим нужный объект в базе по его ID
            # session.get() - это самый быстрый способ поиска по primary_key
            obj = session.get(model, item_id)

            if not obj:
                print(f"Ошибка: Запись с ID {item_id} не найдена в таблице {model.__tablename__}")
                return

            if column_name in ["issue_date"]:
                try:
                    # Пытаемся превратить строку "дд.мм.гггг" в объект date
                    new_value = datetime.strptime(new_value, "%d.%m.%Y").date()
                except ValueError:
                    # Если пользователь ввел дичь (например "32.13.2023" или буквы)
                    print(f"Ошибка: Неверный формат даты ({new_value}). Ожидается ДД.ММ.ГГГГ")
                    return

                # --- ОБРАБОТЧИК ДЛЯ ЧИСЕЛ (ФЛОАТОВ) ---
                # Если у вас есть колонки с грузоподъемностью и объемом, из GUI они тоже придут как текст
            elif column_name in ["load_capacity", "volume"]:
                try:
                    # Меняем запятую на точку (если юзер ввел "1,5" вместо "1.5")
                    new_value = float(new_value.replace(",", "."))
                except ValueError:
                    print(f"Ошибка: Ожидается число, а получено '{new_value}'")
                    return

            # 2. Устанавливаем новое значение динамически
            # Это равносильно написанию obj.phone_number = "8999..."
            setattr(obj, column_name, new_value)

            # 3. Сохраняем изменения
            session.commit()
            print(f"Успешно обновлено: {column_name} = {new_value}")

    def delete_row(self, model_class: int, item_id: int):
        model = None
        match model_class:
            case 1:
                model = self.Driver
            case 2:
                model = self.Car
            case 3:
                model = self.License
            case 4:
                model = self.Employer
        with Session(self.engine) as session:
            obj = session.get(model, item_id)

            if not obj:
                print(f"Ошибка: Запись с ID {item_id} не найдена в {model.__tablename__}.")
                return

            session.delete(obj)

            session.commit()
            print(f"Запись (и связанные данные) успешно удалена: ID {item_id}")
            return