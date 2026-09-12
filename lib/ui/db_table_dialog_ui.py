from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QAbstractItemView, QMenu, QMessageBox, QLabel, \
    QTextEdit, QPushButton, QHBoxLayout, QVBoxLayout, QLineEdit
import enum


class DBDialog(QDialog):

    class TableType(enum.Enum):
        DRIVERS = 1
        CARS = 2

    def __init__(self, db_agent, table_type, parent=None):
        super().__init__(parent)
        self.dbagent = db_agent
        self.setWindowTitle("База данных")
        self.resize(640, 480)

        self.DBTable = QTableWidget(self)
        self.DBTable.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.DBTable.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.DBTable.customContextMenuRequested.connect(self.__show_context_menu)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.DBTable)

        self.__fill(table_type)

    def __fill(self, table_type):
        headers, data = [], []
        self.table_type = table_type
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

    def __show_context_menu(self, pos):
        item = self.DBTable.itemAt(pos)
        if item is None:          # клик вне ячеек
            return

        menu = QMenu(self)
        act_edit = menu.addAction("Изменить")
        act_edit.triggered.connect(lambda: self.__change_cell(item))
        act_delete = menu.addAction("Удалить строку")
        act_delete.triggered.connect(lambda: self.__delete_row(item))
        menu.exec(self.DBTable.viewport().mapToGlobal(pos))

    def __change_cell(self, item):
        if (item.column() == 0) or (item.column() == self.DBTable.columnCount() - 1):
            QMessageBox.critical(self, "Ошибка", "Нельзя менять это поле!")
            return
        print(f'ADD: model_class: {self.table_type.value}; id: {self.DBTable.item(item.row(), 0).text()}, column_name: {self.DBTable.horizontalHeaderItem(item.column()).text()}')
        dlg = InputDialog(
            title="Изменение данных",
            label_text=f'Изменение {self.DBTable.horizontalHeaderItem(item.column()).text()}:',
            initial_text=item.text(),
            parent=self
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_value = dlg.value()
            print(f'new_value: {new_value}')
            self.dbagent.update_cell(
                model_class=self.table_type.value,
                item_id=self.DBTable.item(item.row(), 0).text(),
                col_name=self.DBTable.horizontalHeaderItem(item.column()).text(),
                new_value=new_value
            )
            self.__fill(table_type=self.table_type)

    def __delete_row(self, item):
        id = self.DBTable.item(item.row(), 0).text()
        print(f'DELL: id: {id}; model: {self.table_type.value}')
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            "Удалить запись?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.dbagent.delete_row(model_class=self.table_type.value, item_id=int(id))
        self.__fill(table_type=self.table_type)


class InputDialog(QDialog):
    def __init__(self, title: str, label_text: str, initial_text: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)

        self.label = QLabel(label_text, self)
        self.line = QLineEdit(self)
        self.line.setText(initial_text)

        self.btn_ok = QPushButton("OK", self)
        self.btn_cancel = QPushButton("Отмена", self)

        # Enter в поле = нажать OK
        self.line.returnPressed.connect(self.accept)
        # Кнопки
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        # OK — кнопка по умолчанию (реагирует на Enter, если фокус не в поле)
        self.btn_ok.setDefault(True)

        btns = QHBoxLayout()
        btns.addStretch()
        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.line)
        layout.addLayout(btns)

        self.line.setFocus()          # курсор сразу в поле
        self.line.selectAll()         # выделить текст для быстрой замены

    def value(self) -> str:
        return self.line.text()