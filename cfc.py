import sys
import os
import threading
import zipfile
import chardet
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit, QVBoxLayout, QWidget, QHBoxLayout, QSpinBox

class PasswordCracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.passwords = []
        self.current_password_index = 0
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

    def initUI(self):
        self.setWindowTitle("压缩包密码破解工具")
        self.setGeometry(100, 100, 600, 400)

        # 布局
        layout = QVBoxLayout()

        # 选择字典文件
        self.dict_label = QLabel("字典文件:")
        self.dict_path_edit = QLineEdit()
        self.dict_browse_btn = QPushButton("浏览")
        self.dict_browse_btn.clicked.connect(self.browse_dict_file)
        
        dict_layout = QHBoxLayout()
        dict_layout.addWidget(self.dict_label)
        dict_layout.addWidget(self.dict_path_edit)
        dict_layout.addWidget(self.dict_browse_btn)
        layout.addLayout(dict_layout)

        # 选择压缩包文件
        self.zip_label = QLabel("压缩包文件:")
        self.zip_path_edit = QLineEdit()
        self.zip_browse_btn = QPushButton("浏览")
        self.zip_browse_btn.clicked.connect(self.browse_zip_file)
        
        zip_layout = QHBoxLayout()
        zip_layout.addWidget(self.zip_label)
        zip_layout.addWidget(self.zip_path_edit)
        zip_layout.addWidget(self.zip_browse_btn)
        layout.addLayout(zip_layout)

        # 线程数设置
        self.thread_label = QLabel("线程数:")
        self.thread_spinbox = QSpinBox()
        self.thread_spinbox.setRange(1, 50)
        self.thread_spinbox.setValue(5)
        
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(self.thread_label)
        thread_layout.addWidget(self.thread_spinbox)
        layout.addLayout(thread_layout)

        # 开始按钮
        self.start_btn = QPushButton("开始破解")
        self.start_btn.clicked.connect(self.start_cracking)
        layout.addWidget(self.start_btn)

        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # 设置主窗口布局
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def browse_dict_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "选择字典文件", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            self.dict_path_edit.setText(file_name)

    def browse_zip_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "选择压缩包文件", "", "ZIP Files (*.zip);;All Files (*)", options=options)
        if file_name:
            self.zip_path_edit.setText(file_name)

    def load_dictionary(self, dict_path):
        try:
            with open(dict_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']
                if encoding is None:
                    raise ValueError("无法检测字典文件编码")
                self.passwords = raw_data.decode(encoding).splitlines()
                self.log(f"加载字典文件成功，编码: {encoding}")
        except Exception as e:
            self.log(f"加载字典文件失败: {str(e)}")

    def verify_zip_integrity(self, zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                bad_file = zf.testzip()
                if bad_file:
                    self.log(f"压缩包损坏: {bad_file}")
                    return False
                else:
                    self.log("压缩包完整性验证通过")
                    return True
        except zipfile.BadZipFile:
            self.log("压缩包损坏，无法打开")
            return False

    def crack_password(self, zip_path, password):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(pwd=password.encode('utf-8'))
                self.log(f"密码破解成功: {password}")
                self.stop_event.set()
        except RuntimeError as e:
            if 'Bad password' in str(e):
                self.log(f"密码错误: {password}")
            else:
                self.log(f"解压时发生错误: {str(e)}")
        except Exception as e:
            self.log(f"未知错误: {str(e)}")

    def worker(self, zip_path):
        while not self.stop_event.is_set():
            with self.lock:
                if self.current_password_index >= len(self.passwords):
                    break
                password = self.passwords[self.current_password_index]
                self.current_password_index += 1
            self.crack_password(zip_path, password)

    def start_cracking(self):
        dict_path = self.dict_path_edit.text()
        zip_path = self.zip_path_edit.text()
        thread_count = self.thread_spinbox.value()

        if not os.path.isfile(dict_path):
            self.log("字典文件不存在，请重新选择")
            return

        if not os.path.isfile(zip_path):
            self.log("压缩包文件不存在，请重新选择")
            return

        if not self.verify_zip_integrity(zip_path):
            return

        self.load_dictionary(dict_path)
        if not self.passwords:
            self.log("字典文件为空或无法读取")
            return

        self.current_password_index = 0
        self.stop_event.clear()

        threads = []
        for _ in range(thread_count):
            t = threading.Thread(target=self.worker, args=(zip_path,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        if not self.stop_event.is_set():
            self.log("所有密码尝试完毕，未找到正确密码")

    def log(self, message):
        self.log_text.append(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PasswordCracker()
    window.show()
    sys.exit(app.exec_())
