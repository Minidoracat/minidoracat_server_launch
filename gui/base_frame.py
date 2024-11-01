import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class BaseFrame(ttk.Frame):
    """基礎框架類別，所有頁面都繼承此類別"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.init_ui()
    
    def init_ui(self):
        """初始化使用者介面，子類別必須實作此方法"""
        raise NotImplementedError("子類別必須實作 init_ui 方法")
