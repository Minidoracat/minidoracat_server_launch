import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import re
from pathlib import Path
from .base_frame import BaseFrame
from logger import logger

class NodeFrame(BaseFrame):
    """節點設定頁面"""
    def __init__(self, master, kcptube_manager, **kwargs):
        self.kcptube = kcptube_manager
        self.node_configs = {}
        super().__init__(master, padding=15, **kwargs)
    
    def init_ui(self):
        """初始化節點設定頁面"""
        # 節點選擇
        node_select_frame = ttk.Frame(self)
        node_select_frame.pack(fill=X, pady=(0, 10))
        
        self.node_combo = ttk.Combobox(
            node_select_frame,
            state='readonly',
            font=('微軟正黑體', 10),
            width=30
        )
        self.node_combo.pack(side=LEFT, padx=(0, 15))
        self.node_combo.bind('<<ComboboxSelected>>', self.on_node_selected)
        
        # 節點資訊
        node_info_frame = ttk.Frame(self)
        node_info_frame.pack(fill=X, pady=(0, 10))
        
        self.node_speed_label = ttk.Label(
            node_info_frame,
            text="節點速度設定: 未選擇",
            style='info'
        )
        self.node_speed_label.pack(side=LEFT)
        
        self.node_connect_label = ttk.Label(
            node_info_frame,
            text="連線資訊: 未選擇",
            style='info'
        )
        self.node_connect_label.pack(side=RIGHT)

        # 速度設定提示
        speed_tip_frame = ttk.Frame(self)
        speed_tip_frame.pack(fill=X, pady=(0, 10))
        
        speed_tip_label = ttk.Label(
            speed_tip_frame,
            text="提示：您可以在「速度設定」頁面測試或設定網路頻寬。本工具使用頻寬設定來優化連線，降低延遲並提升穩定性，建議依據您的實際網路頻寬進行設定。",
            style='info',
            wraplength=700  # 設定文字換行寬度
        )
        speed_tip_label.pack(fill=X)
        
        # 控制按鈕
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=X, pady=(0, 10))
        
        self.start_button = ttk.Button(
            control_frame,
            text='啟動加速',
            command=self.start_service,
            style='success',
            width=15
        )
        self.start_button.pack(side=LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(
            control_frame,
            text='停止加速',
            command=self.stop_service,
            state='disabled',
            style='danger-outline',
            width=15
        )
        self.stop_button.pack(side=LEFT)
        
        self.status_label = ttk.Label(
            control_frame,
            text='狀態: 未啟動',
            style='info'
        )
        self.status_label.pack(side=RIGHT)
        
        # 載入節點列表
        self.load_nodes()
    
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
                # 觸發節點選擇事件來更新顯示
                self.on_node_selected(None)
                logger.info(f"載入了 {len(self.node_configs)} 個節點設定")
            else:
                logger.warning("未找到任何節點設定檔")
    
    def on_node_selected(self, event):
        """當選擇節點時更新顯示"""
        selected = self.node_combo.get()
        if selected:
            config_path = self.node_configs.get(selected)
            info = self.get_node_info(config_path)
            
            # 更新節點速度資訊
            self.node_speed_label['text'] = (
                f"節點速度設定: 下載 {info['inbound']}M | "
                f"上傳 {info['outbound']}M"
            )
            
            # 更新節點連線資訊
            self.node_connect_label['text'] = (
                f"連線資訊 - IP地址: 127.0.0.1 | "
                f"端口: {info['port']}"
            )
    
    def get_node_info(self, config_path):
        """讀取節點的設定資訊"""
        try:
            content = Path(config_path).read_text(encoding='utf-8')
            
            # 使用正則表達式找到設定
            inbound_match = re.search(r'inbound_bandwidth=(\d+)M', content)
            outbound_match = re.search(r'outbound_bandwidth=(\d+)M', content)
            port_match = re.search(r'listen_port=(\d+)', content)
            
            inbound = int(inbound_match.group(1)) if inbound_match else 0
            outbound = int(outbound_match.group(1)) if outbound_match else 0
            port = port_match.group(1) if port_match else "未知"
            
            return {
                'inbound': inbound,
                'outbound': outbound,
                'port': port
            }
        except Exception as e:
            logger.error(f"讀取節點設定失敗: {str(e)}")
            return {
                'inbound': 0,
                'outbound': 0,
                'port': "未知"
            }
    
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
            logger.info("服務已停止")
