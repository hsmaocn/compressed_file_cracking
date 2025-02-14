import os
import threading
import zipfile
from tkinter import Tk, Label, Entry, Button, StringVar, Text, Scrollbar, END
from concurrent.futures import ThreadPoolExecutor

# 验证压缩包完整性
def validate_zip(zip_path):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            if zip_file.testzip() is not None:
                return False
        return True
    except Exception as e:
        print(f"压缩包损坏或无法打开: {e}")
        return False

# 尝试解压
def try_extract(zip_path, password):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            zip_file.extractall(pwd=password.encode('utf-8'))
        return True
    except (RuntimeError, zipfile.BadZipFile):
        return False
    except Exception as e:
        print(f"解压异常: {e}")
        return False

# 密码破解主函数
def crack_password(zip_path, dict_file, num_threads, result_var, log_text):
    if not validate_zip(zip_path):
        log_text.insert(END, "压缩包损坏或不完整，请检查！\n")
        return

    passwords = []
    try:
        with open(dict_file, 'r', encoding='utf-8') as f:
            passwords = [line.strip() for line in f]
    except UnicodeDecodeError:
        log_text.insert(END, "字典文件编码错误，请使用 UTF-8 格式！\n")
        return

    def worker(passwords_chunk):
        for pwd in passwords_chunk:
            if try_extract(zip_path, pwd):
                result_var.set(pwd)
                log_text.insert(END, f"密码已找到: {pwd}\n")
                return
            log_text.insert(END, f"尝试密码: {pwd}\n")

    # 分割密码列表
    chunk_size = len(passwords) // num_threads
    chunks = [passwords[i:i + chunk_size] for i in range(0, len(passwords), chunk_size)]

    # 多线程执行
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for chunk in chunks:
            executor.submit(worker, chunk)

# GUI 界面
def main():
    root = Tk()
    root.title("压缩包密码破解工具")

    # 变量
    zip_path_var = StringVar()
    dict_path_var = StringVar()
    thread_num_var = StringVar(value="3")
    result_var = StringVar()

    # 布局
    Label(root, text="压缩包路径:").grid(row=0, column=0, sticky="w")
    Entry(root, textvariable=zip_path_var, width=50).grid(row=0, column=1)
    Label(root, text="字典文件路径:").grid(row=1, column=0, sticky="w")
    Entry(root, textvariable=dict_path_var, width=50).grid(row=1, column=1)
    Label(root, text="线程数:").grid(row=2, column=0, sticky="w")
    Entry(root, textvariable=thread_num_var, width=50).grid(row=2, column=1)
    Label(root, text="破解结果:").grid(row=3, column=0, sticky="w")
    Label(root, textvariable=result_var, fg="green").grid(row=3, column=1, sticky="w")

    log_text = Text(root, height=10, width=60)
    log_text.grid(row=4, column=0, columnspan=2)
    scrollbar = Scrollbar(root, command=log_text.yview)
    scrollbar.grid(row=4, column=2, sticky="ns")
    log_text.config(yscrollcommand=scrollbar.set)

    def start_crack():
        zip_path = zip_path_var.get()
        dict_path = dict_path_var.get()
        num_threads = int(thread_num_var.get())
        crack_password(zip_path, dict_path, num_threads, result_var, log_text)

    Button(root, text="开始破解", command=start_crack).grid(row=5, column=0, columnspan=2)

    root.mainloop()

if __name__ == "__main__":
    main()
