from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QAbstractItemView
import enum


class DBDialog(QDialog):                          # ← QDialog, а не QWidget

    class TableType(enum.Enum):
        DRIVERS = 1
        CARS = 2

    def __init__(self, db_agent, table_type, parent=None):
        super().__init__(parent)               # ← parent = главное окно
        self.dbagent = db_agent
        self.setWindowTitle("База данных")
        self.resize(640, 480)

        self.DBTable = QTableWidget(self)
        self.DBTable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        layout = QtWidgets.QVBoxLayout(self)   # ← менеджер компоновки вместо setGeometry
        layout.addWidget(self.DBTable)

        self._fill(table_type)                 # заполняем сразу

    def _fill(self, table_type):
        headers, data = [], []
        match table_type:
            case DBDialog.TableType.DRIVERS:
                headers, data = self.dbagent.get_drivers_for_table()
            case DBDialog.TableType.CARS:
                headers, data = self.dbagent.get_cars_for_table()

        self.DBTable.setRowCount(len(data))
        self.DBTable.setColumnCount(len(headers))
        self.DBTable.setHorizontalHeaderLabels(headers)

        for row_idx, row_data in enumerate(data):
            for col_idx, col_data in enumerate(row_data):
                self.DBTable.setItem(
                    row_idx, col_idx,
                    QTableWidgetItem(str(col_data))
                )
        self.DBTable.resizeRowsToContents()
        self.DBTable.resizeColumnsToContents()