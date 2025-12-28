import sys
import json
import traceback

import EMC_Fault_Database
from PyQt5.QtGui import QImage, QPixmap, QIcon, QStandardItemModel, QStandardItem, QFont
from PyQt5.QtWidgets import QMainWindow, QApplication, QHeaderView, QMessageBox
from PyQt5.QtCore import QTimer, QThread

import warnings

warnings.filterwarnings("ignore", message="iCCP")
warnings.resetwarnings()


class MainWindows(QMainWindow, EMC_Fault_Database.Ui_MainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        # 初始化显示表格
        self.resetdispTableView()

        # 将“发送”按钮的信号与Slot函数连接
        self.sendPushButton.clicked.connect(self.sendPushButtonClicked)

        # 全局变量
        self.json_file_path = "12.29.json"  # json文件的相对路径
        self.readJsonData = None  # 读取json文件得到的数据
        self.searchTextfromUserInput = None  # 来自用户输入的要搜索的字段
        self.target_field = None  # 目标字段
        self.search_string = None  # 搜索字段
        self.search_results_exact = []  # 精确字段匹配的结果

    def resetdispTableView(self):
        # 规定水平表头标签
        tableTitle = ['故障对象', '故障现象', '故障原因', '解决方案', '故障等级', '发生频率']
        self.model = QStandardItemModel(1, len(tableTitle))

        # 设置水平表头标签
        self.model.setHorizontalHeaderLabels(tableTitle)

        # 设置表格基础字体及表头字体
        base_font = QFont("HarmonyOS Sans SC Medium", 10)
        self.dispTableView.setFont(base_font)
        header_font = QFont("HarmonyOS Sans SC Medium", 12, QFont.Bold)
        self.dispTableView.horizontalHeader().setFont(header_font)

        # 将模型设置给dispTableView控件
        self.dispTableView.setModel(self.model)

        # 均匀拉伸所有的列和行
        header = self.dispTableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        vheader = self.dispTableView.verticalHeader()
        vheader.setSectionResizeMode(QHeaderView.Stretch)

    def load_json_file(self):
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self.readJsonData = json.load(f)
        except Exception as e:
            error_details = f"错误类型: {type(e).__name__}\n\n详细错误:\n{traceback.format_exc()}"
            QMessageBox.critical(self, '系统错误', f'发生未知错误:\n{error_details}')

    def sendPushButtonClicked(self):
        """
        在JSON文件中搜索包含特定字符串的词条

        Args:
            file_path (str): JSON文件路径
            search_string (str): 要搜索的字符串
            target_field (str, optional): 指定搜索的字段名，如果为None则搜索所有字段

        Returns:
            list: 包含搜索字符串的词条列表
        """
        try:
            # 重置表格
            self.resetdispTableView()
            # 1. 读取JSON文件，这一步已在load_json_file函数中执行并存储在self.readJsonData变量中
            # 2. 筛选包含搜索字符串的词条
            if self.userInputTextEdit.toPlainText() != "":
                # 获取
                self.search_string = str(self.userInputTextEdit.toPlainText())

                # print(self.search_string) # 调试用
                for item in self.readJsonData:
                    # 如果self.target_field有值，则在target_field中搜索
                    # 如果self.target_field没有值，则在json文件中的所有字段中搜索
                    if self.target_field:
                        # 只在指定字段中搜索
                        if self.target_field in item and isinstance(item[self.target_field], str):
                            if self.search_string in item[self.target_field]:
                                self.search_results_exact.append(item)
                    else:
                        # 在所有字段中搜索
                        for value in item.values():
                            if isinstance(value, str) and self.search_string in value:
                                self.search_results_exact.append(item)
                                break

                self.infoLabel.setText(self.search_string + f"——找到 {len(self.search_results_exact)} 条匹配结果\n")
                # print(self.search_results_exact) # 调试用
                for i, entry in enumerate(self.search_results_exact):
                    self.model.setItem(i, 0, QStandardItem(entry.get('故障对象', '')))
                    self.model.setItem(i, 1, QStandardItem(entry.get('故障现象', '')))
                    self.model.setItem(i, 2, QStandardItem(entry.get('故障原因', '')))
                    self.model.setItem(i, 3, QStandardItem(entry.get('解决方案', '')))
                    self.model.setItem(i, 4, QStandardItem(entry.get('故障等级', '')))
                    self.model.setItem(i, 5, QStandardItem(entry.get('发生频率', '')))
                    self.dispTableView.setModel(self.model)

                self.search_results_exact = []

            else:
                self.infoLabel.setText("请您输入文本！")

        except FileNotFoundError:
            error_details = f"错误：文件 '{self.json_file_path}' 未找到"
            QMessageBox.critical(self, '系统错误', f'发生未知错误:\n{error_details}')
        except json.JSONDecodeError:
            error_details = f"错误：文件 '{self.json_file_path}' 不是有效的JSON格式"
            QMessageBox.critical(self, '系统错误', f'发生未知错误:\n{error_details}')
        except Exception as e:
            error_details = f"错误类型: {type(e).__name__}\n\n详细错误:\n{traceback.format_exc()}"
            QMessageBox.critical(self, '系统错误', f'发生未知错误:\n{error_details}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindows()
    main.setWindowTitle('电磁兼容故障库')
    main.setWindowIcon(QIcon("BUAA_logo_2048px.png"))
    main.show()

    main.load_json_file()

    sys.exit(app.exec_())
