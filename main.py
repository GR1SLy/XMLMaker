import sys
from lib.dbagent import DBAgent

if __name__ == '__main__':
    agent = DBAgent(debug=True)
    agent.create()
    #agent.populate_test_data()
    driver = agent.get_driver_info_by_last_name('Петров')
    car = agent.get_car_info_by_number('K453MT154')
    print(f'{driver}\n\n\n\n{car}')

    # app = QtWidgets.QApplication(sys.argv)
    # MainWindow = QtWidgets.QMainWindow()
    # ui = Ui_MainWindow()
    # ui.setupUi(MainWindow)
    # MainWindow.show()
    # sys.exit(app.exec())