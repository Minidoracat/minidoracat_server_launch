import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from queue import Queue
import threading

class QueueHandler(logging.Handler):
    """將日誌訊息發送到佇列的處理器"""
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        self.queue.put(record)

class Logger:
    """日誌管理類"""
    _instance = None
    _gui_queue = Queue()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        """設置日誌系統"""
        # 確保日誌目錄存在
        os.makedirs('logs', exist_ok=True)
        
        # 設定主日誌記錄器
        self.logger = logging.getLogger('KCPTubeLauncher')
        self.logger.setLevel(logging.DEBUG)
        
        # 如果已經有處理器，不要重複添加
        if self.logger.handlers:
            return
        
        # 設定日誌格式
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 檔案處理器 (每個檔案最大 5MB，保留 5 個備份)
        file_handler = RotatingFileHandler(
            'logs/launcher.log',
            maxBytes=5*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # 終端處理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # GUI 佇列處理器
        queue_handler = QueueHandler(self._gui_queue)
        queue_handler.setLevel(logging.INFO)  # 只發送 INFO 以上的訊息到 GUI
        queue_handler.setFormatter(formatter)
        
        # 加入處理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(queue_handler)
    
    def get_gui_queue(self):
        """獲取 GUI 日誌佇列"""
        return self._gui_queue
    
    def info(self, message):
        """記錄一般資訊"""
        self.logger.info(message)
    
    def error(self, message):
        """記錄錯誤"""
        self.logger.error(message)
    
    def debug(self, message):
        """記錄除錯資訊"""
        self.logger.debug(message)
    
    def warning(self, message):
        """記錄警告"""
        self.logger.warning(message)
    
    def log_kcptube_output(self, message, is_error=False):
        """記錄 KCPTube 的輸出"""
        if is_error:
            self.error(f"KCPTube: {message}")
        else:
            self.info(f"KCPTube: {message}")

# 全域日誌實例
logger = Logger()
