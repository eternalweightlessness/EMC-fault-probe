import os
import sys
import json
import re
import traceback
import pandas as pd
from ollama import chat   # ===== 修改点 1：引入 LLM =====

import EMC_Fault_Database
from PyQt5.QtGui import QImage, QPixmap, QIcon, QStandardItemModel, QStandardItem, QFont
from PyQt5.QtWidgets import QMainWindow, QApplication, QHeaderView, QMessageBox, QFileDialog
from PyQt5.QtCore import QTimer, QThread


class MainWindows(QMainWindow, EMC_Fault_Database.Ui_MainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        # 初始化显示表格
        self.resetdispTableView()

        # 将“发送”按钮的信号与Slot函数连接
        self.sendPushButton.clicked.connect(self.sendPushButtonClicked)
        # 将“保存数据”按钮的信号与Slot函数连接
        self.saveDataPushButton.clicked.connect(self.save_userdata_pushButtonClicked)
        # 将“退出程序”按钮的信号与Slot函数连接
        self.exitPushButton.clicked.connect(self.exitPushButtonClicked)

        # 全局变量
        # 字符串匹配
        self.json_dir = "."  # 读取当前目录下的所有json文件
        self.readJsonData = []  # 读取json文件得到的数据
        self.searchTextfromUserInput = None  # 来自用户输入的要搜索的字段
        self.target_field = None  # 目标字段
        self.search_string = None  # 搜索字段
        self.search_results_exact = []  # 精确字段匹配的结果

        #self.enable_llm_fuzzy = True   #选择开/关模糊搜索
        # 数据保存
        self.save_data_path = ""  # 数据保存的文件路径

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

    # def load_json_file(self):
    #     try:
    #         with open(self.json_file_path, 'r', encoding='utf-8') as f:
    #             self.readJsonData = json.load(f)
    #     except Exception as e:
    #         error_details = f"错误类型: {type(e).__name__}\n\n详细错误:\n{traceback.format_exc()}"
    #         QMessageBox.critical(self, '系统错误', f'发生未知错误:\n{error_details}')
    def load_json_file(self):
        try:
            json_dir = self.json_dir

            # 遍历指定目录下的所有文件
            for filename in os.listdir(json_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(json_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 假设每个json文件都是列表或字典，统一合并到readJsonData列表中
                        if isinstance(data, list):
                            self.readJsonData.extend(data)
                        elif isinstance(data, dict):
                            self.readJsonData.append(data)
        except Exception as e:
            error_details = f"错误类型: {type(e).__name__}\n\n详细错误:\n{traceback.format_exc()}"
            QMessageBox.critical(self, '系统错误', f'发生错误:\n{error_details}')

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
                user_input = str(self.userInputTextEdit.toPlainText())#self.search_string = str(self.userInputTextEdit.toPlainText())
                # 调用 LLM，把用户输入扩展为多个关键词
                # ==================================================
                fuzzy_keywords = self.llm_generate_fuzzy_keywords(user_input)
                # 兜底：至少保证有原词
                if not fuzzy_keywords:
                    fuzzy_keywords = [user_input]

                self.search_results_exact = []  # 保证是干净的
                seen = set()  # 用于去重
                for self.search_string in fuzzy_keywords:

                    for item in self.readJsonData:
                        if self.target_field:
                            if self.target_field in item and isinstance(item[self.target_field], str):
                                if self.search_string in item[self.target_field]:
                                    item_id = json.dumps(item, ensure_ascii=False)
                                    if item_id not in seen:
                                        seen.add(item_id)
                                        self.search_results_exact.append(item)
                        else:
                            for value in item.values():
                                if isinstance(value, str) and self.search_string in value:
                                    item_id = json.dumps(item, ensure_ascii=False)
                                    if item_id not in seen:
                                        seen.add(item_id)
                                        self.search_results_exact.append(item)
                                    break

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
            QMessageBox.critical(self, '系统错误', f'发生错误:\n{error_details}')
        except json.JSONDecodeError:
            error_details = f"错误：文件 '{self.json_file_path}' 不是有效的JSON格式"
            QMessageBox.critical(self, '系统错误', f'发生错误:\n{error_details}')
        except Exception as e:
            error_details = f"错误类型: {type(e).__name__}\n\n详细错误:\n{traceback.format_exc()}"
            QMessageBox.critical(self, '系统错误', f'发生错误:\n{error_details}')

    def llm_generate_fuzzy_keywords(self, user_keyword):
        from ollama import chat
        import re, json

        prompt = f"""
    请根据输入的电磁兼容故障关键词，生成用于模糊搜索的关键词。
    只返回 JSON 数组，不要解释。
    示例：["传导发射", "辐射发射超标"]

    输入关键词：
    "{user_keyword}"
    """

        try:
            resp = chat(
                model="deepseek-r1:8b",
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )

            content = resp["message"]["content"]
            match = re.search(r"\[[\s\S]*?\]", content)
            if match:
                return json.loads(match.group())

        except Exception as e:
            print("LLM 关键词生成失败:", e)

        return [user_keyword]

    def save_userdata_pushButtonClicked(self):
        try:
            self.save_data_path = QFileDialog.getSaveFileName(
                None,
                "选择目录",
                "",
                "Excel Files (*.xlsx);;All Files (*)"
                # QFileDialog.ShowDirsOnly,
            )
            # print(self.save_data_path) # 调试用

            to_save_model = self.dispTableView.model()
            # 获取行数和列数
            row_count = to_save_model.rowCount()
            col_count = to_save_model.columnCount()
            if row_count > 0 and col_count > 0:
                # 提取表头
                headers = []
                for col in range(col_count):
                    # 获取列标题
                    header = to_save_model.headerData(col, 1)  # 1表示水平表头
                    if header is None:
                        header = f"Column_{col + 1}"
                    headers.append(header)

                # 提取表格数据
                data = []
                for row in range(row_count):
                    row_data = []
                    for col in range(col_count):
                        index = to_save_model.index(row, col)
                        # 0表示显示表头角色的数据
                        value = to_save_model.data(index, 0)
                        row_data.append(value if value is not None else "")
                    data.append(row_data)

                # 使用pandas创建DataFrame并保存为Excel
                df = pd.DataFrame(data, columns=headers)
                df.to_excel(self.save_data_path[0], index=False)
                self.infoLabel.setText("数据保存完成")
            else:
                self.infoLabel.setText("警告：表格数据为空！")
        except Exception as e:
            error_details = f"错误类型: {type(e).__name__}\n\n详细错误:\n{traceback.format_exc()}"
            QMessageBox.critical(self, '系统错误', f'发生错误:\n{error_details}')
            # print(error_details) # 调试用

    def exitPushButtonClicked(self):
        try:
            sys.exit(app.exec_())
        except Exception as e:
            error_details = f"错误类型: {type(e).__name__}\n\n详细错误:\n{traceback.format_exc()}"
            QMessageBox.critical(self, '系统错误', f'发生错误:\n{error_details}')



if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = MainWindows()
    main.setWindowTitle('电磁兼容故障库')
    main.setWindowIcon(QIcon("BUAA_logo_2048px.png"))
    main.show()

    main.load_json_file()

    sys.exit(app.exec_())
