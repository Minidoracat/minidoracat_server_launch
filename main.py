import sys
import os
import json
import sqlite3
import requests
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import subprocess
import threading
import time
from queue import Empty, Queue
from pathlib import Path
from logger import logger
from config_manager import ConfigManager

class VersionManager:
    """版本管理類"""
    def __init__(self):
        self.version_file = Path('version.json')
        self.versions = self._load_versions()
    
    def _load_versions(self):
        """載入版本資訊"""
        if self.version_file.exists():
            try:
                return json.loads(self.version_file.read_text(encoding='utf-8'))
            except Exception as e:
                logger.error(f"讀取版本資訊失敗: {str(e)}")
        return self._download_versions()
    
    def _download_versions(self):
        """從 GitHub 下載版本資訊"""
        try:
            url = "https://raw.githubusercontent.com/Minidoracat/kcptube_launch/main/version.json"
            response = requests.get(url)
            response.raise_for_status()
            
            versions = response.json()
            self.version_file.write_text(json.dumps(versions, indent=4, ensure_ascii=False), encoding='utf-8')
            logger.info(f"成功下載版本資訊: {versions}")
            return versions
        except Exception as e:
            logger.error(f"下載版本資訊失敗: {str(e)}")
            return {
                "launcher_version": "unknown",
                "kcptube_version": "unknown",
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
    
    @property
    def launcher_version(self):
        """取得啟動器版本"""
        return self.versions.get('launcher_version', 'unknown')
    
    @property
    def kcptube_version(self):
        """取得 KCPTube 版本"""
        return self.versions.get('kcptube_version', 'unknown')
    
    @property
    def last_updated(self):
        """取得最後更新日期"""
        return self.versions.get('last_updated', 'unknown')

class KCPTubeManager:
    """KCPTube 管理類"""
    def __init__(self):
        self._ensure_directories()
        self.version_manager = VersionManager()
        self.config_manager = ConfigManager("Minidoracat", "kcptube_launch")
        self.process = None
        self.monitor_threads = []
        logger.info(f"KCPTube 管理器初始化完成，版本: {self.version_manager.kcptube_version}")
    
    def _ensure_directories(self):
        """確保必要的目錄存在"""
        Path('kcptube').mkdir(exist_ok=True)
        Path('logs').mkdir(exist_ok=True)
        Path('conf').mkdir(exist_ok=True)
        logger.debug("確保必要目錄存在: kcptube/, logs/, conf/")
    
    def sync_configs(self):
        """同步設定檔"""
        return self.config_manager.sync_configs()
    
    def start_kcptube(self, config_path):
        """啟動 KCPTube"""
        if self.process:
            logger.warning("KCPTube 已在運行中")
            return False
            
        version_path = Path('kcptube') / self.version_manager.kcptube_version
        exe_path = version_path / 'kcptube.exe'
        
        if not exe_path.exists():
            logger.error(f"執行檔不存在: {exe_path}")
            return False
            
        try:
            # 建立輸出日誌檔案
            output_log = Path('logs/kcptube_output.log')
            error_log = Path('logs/kcptube_error.log')
            
            # 寫入啟動時間戳記
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for log_file in [output_log, error_log]:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n=== KCPTube 啟動於 {timestamp} ===\n")
            
            logger.info(f"正在啟動 KCPTube，設定檔: {config_path}")
            
            # 啟動程序
            self.process = subprocess.Popen(
                [str(exe_path), str(config_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
                bufsize=1,
                universal_newlines=True
            )
            
            # 開始監控輸出
            self._start_output_monitor(output_log, error_log)
            
            logger.info("KCPTube 啟動成功")
            return True
        except Exception as e:
            logger.error(f"KCPTube 啟動失敗: {str(e)}")
            return False
    
    def _start_output_monitor(self, output_log, error_log):
        """開始監控程序輸出"""
        def monitor_output(pipe, log_file, is_error=False):
            while self.process and not self.process.poll():
                try:
                    line = pipe.readline()
                    if not line:
                        time.sleep(0.1)  # 避免過度消耗 CPU
                        continue
                    
                    # 移除尾部的空白字元
                    line = line.rstrip()
                    
                    # 寫入到對應的日誌檔案
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"{line}\n")
                        f.flush()
                    
                    # 同時記錄到主日誌
                    if is_error:
                        logger.error(f"KCPTube: {line}")
                    else:
                        logger.info(f"KCPTube: {line}")
                except Exception as e:
                    if self.process and not self.process.poll():
                        logger.error(f"監控輸出時發生錯誤: {str(e)}")
                    break
        
        # 清除舊的監控執行緒
        self.monitor_threads.clear()
        
        # 監控標準輸出
        stdout_thread = threading.Thread(
            target=monitor_output,
            args=(self.process.stdout, output_log, False),
            daemon=True
        )
        stdout_thread.start()
        self.monitor_threads.append(stdout_thread)
        
        # 監控錯誤輸出
        stderr_thread = threading.Thread(
            target=monitor_output,
            args=(self.process.stderr, error_log, True),
            daemon=True
        )
        stderr_thread.start()
        self.monitor_threads.append(stderr_thread)
    
    def stop_kcptube(self):
        """停止 KCPTube"""
        if not self.process:
            logger.warning("嘗試停止未運行的 KCPTube")
            return False
        
        try:
            logger.info("正在停止 KCPTube")
            
            # 記錄停止時間
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for log_file in ['logs/kcptube_output.log', 'logs/kcptube_error.log']:
                try:
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"\n=== KCPTube 停止於 {timestamp} ===\n")
                except Exception as e:
                    logger.error(f"寫入停止時間戳記失敗: {str(e)}")
            
            # 停止程序
            process = self.process  # 保存引用
            self.process = None  # 先清除引用，這樣監控執行緒就會結束
            
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            # 等待監控執行緒結束
            for thread in self.monitor_threads:
                thread.join(timeout=1)
            self.monitor_threads.clear()
            
            logger.info("KCPTube 已停止")
            return True
        except Exception as e:
            logger.error(f"停止 KCPTube 時發生錯誤: {str(e)}")
            return False

class MainWindow:
    """主視窗"""
    def __init__(self, root):
        self.root = root
        self.root.title('KCPTube 啟動器')
        self.root.geometry('600x500')  # 加大視窗尺寸
        self.root.resizable(True, True)  # 允許調整視窗大小
        
        logger.info("啟動器開始運行")
        
        # 初始化 KCPTube 管理器
        self.kcptube = KCPTubeManager()
        
        self.init_ui()
        self.setup_log_monitor()
        
        # 同步設定檔
        self.sync_configs()
        
        logger.info("使用者介面初始化完成")
    
    def sync_configs(self):
        """同步設定檔"""
        logger.info("正在同步設定檔...")
        try:
            self.kcptube.sync_configs()
            self.load_nodes()  # 重新載入節點列表
            logger.info("設定檔同步完成")
        except Exception as e:
            logger.error(f"同步設定檔失敗: {str(e)}")
            messagebox.showerror('錯誤', '同步設定檔失敗，請檢查網路連接')
    
    def init_ui(self):
        """初始化使用者介面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 上半部分（控制區）
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 版本資訊
        version_frame = ttk.Frame(control_frame)
        version_frame.pack(fill=tk.X, pady=(0, 10))
        self.version_label = ttk.Label(
            version_frame,
            text=(
                f'啟動器版本: {self.kcptube.version_manager.launcher_version} | '
                f'KCPTube 版本: {self.kcptube.version_manager.kcptube_version}'
            )
        )
        self.version_label.pack(side=tk.LEFT)
        
        # 同步按鈕
        self.sync_button = ttk.Button(
            version_frame,
            text='同步設定',
            command=self.sync_configs,
            width=10
        )
        self.sync_button.pack(side=tk.RIGHT)
        
        # 節點選擇
        node_frame = ttk.Frame(control_frame)
        node_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(node_frame, text='節點選擇:').pack(side=tk.LEFT)
        self.node_combo = ttk.Combobox(node_frame, state='readonly')
        self.node_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 控制按鈕
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        self.start_button = ttk.Button(
            button_frame,
            text='啟動',
            command=self.start_service,
            width=15
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        self.stop_button = ttk.Button(
            button_frame,
            text='停止',
            command=self.stop_service,
            state='disabled',
            width=15
        )
        self.stop_button.pack(side=tk.LEFT)
        
        # 狀態顯示
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        self.status_label = ttk.Label(
            status_frame,
            text='狀態: 未啟動',
            font=('微軟正黑體', 9)
        )
        self.status_label.pack(side=tk.LEFT)
        
        # 下半部分（日誌顯示區）
        log_frame = ttk.LabelFrame(main_frame, text="日誌", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日誌文字框
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            background='black',
            foreground='white'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 載入節點列表
        self.load_nodes()
        
        # 設定樣式
        style = ttk.Style()
        style.configure('TButton', font=('微軟正黑體', 9))
        style.configure('TLabel', font=('微軟正黑體', 9))
        style.configure('TCombobox', font=('微軟正黑體', 9))
        style.configure('TLabelframe', font=('微軟正黑體', 9))
        style.configure('TLabelframe.Label', font=('微軟正黑體', 9))
    
    def setup_log_monitor(self):
        """設置日誌監控"""
        def check_log_queue():
            # 檢查佇列中的新日誌
            try:
                while True:
                    record = logger.get_gui_queue().get_nowait()
                    msg = self.format_log_message(record)
                    self.log_text.insert(tk.END, msg + '\n')
                    self.log_text.see(tk.END)  # 自動滾動到最新的日誌
                    
                    # 根據日誌等級設定顏色
                    tag = f"level_{record.levelname}"
                    last_line = f"{self.log_text.get('end-2c linestart', 'end-1c')}\n"
                    self.log_text.tag_add(tag, f"end-{len(last_line)}c", "end-1c")
            except Empty:
                pass
            finally:
                # 每 100ms 檢查一次佇列
                self.root.after(100, check_log_queue)
        
        # 設定不同日誌等級的顏色
        self.log_text.tag_config('level_ERROR', foreground='red')
        self.log_text.tag_config('level_WARNING', foreground='yellow')
        self.log_text.tag_config('level_INFO', foreground='white')
        self.log_text.tag_config('level_DEBUG', foreground='gray')
        
        # 開始監控
        check_log_queue()
    
    def format_log_message(self, record):
        """格式化日誌訊息"""
        return f"{record.asctime} [{record.levelname}] {record.message}"
    
    def load_nodes(self):
        """載入節點列表"""
        conf_dir = Path("conf")
        self.node_configs = {}
        
        if conf_dir.exists():
            for file in conf_dir.glob("*.conf"):
                name = file.stem
                self.node_configs[name] = str(file)
                logger.debug(f"找到節點設定檔: {name} -> {file}")
            
            if self.node_configs:
                self.node_combo['values'] = list(self.node_configs.keys())
                self.node_combo.current(0)
                logger.info(f"載入了 {len(self.node_configs)} 個節點設定")
            else:
                logger.warning("未找到任何節點設定檔")
    
    def start_service(self):
        """啟動服務"""
        selected = self.node_combo.get()
        if not selected:
            logger.warning("未選擇節點就嘗試啟動")
            messagebox.showwarning('錯誤', '請選擇節點')
            return
            
        logger.info(f"嘗試啟動節點: {selected}")
        config_path = self.node_configs.get(selected)
        if self.kcptube.start_kcptube(config_path):
            self.status_label['text'] = '狀態: 運行中'
            self.start_button['state'] = 'disabled'
            self.stop_button['state'] = 'normal'
            self.sync_button['state'] = 'disabled'
            logger.info(f"節點 {selected} 啟動成功")
        else:
            logger.error(f"節點 {selected} 啟動失敗")
            messagebox.showwarning('錯誤', '啟動失敗')
    
    def stop_service(self):
        """停止服務"""
        logger.info("嘗試停止服務")
        if self.kcptube.stop_kcptube():
            self.status_label['text'] = '狀態: 已停止'
            self.start_button['state'] = 'normal'
            self.stop_button['state'] = 'disabled'
            self.sync_button['state'] = 'normal'
            logger.info("服務已停止")

if __name__ == '__main__':
    try:
        root = tk.Tk()
        app = MainWindow(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"程式啟動失敗: {str(e)}")
        sys.exit(1)
