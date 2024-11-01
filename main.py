import sys
import ttkbootstrap as ttk
from logger import logger
from kcptube_manager import KCPTubeManager
from speed_test_manager import SpeedTestManager
from pz_manager import ProjectZomboidManager
from gui.main_window import MainWindow
from config_manager import ConfigManager

if __name__ == '__main__':
    try:
        # 初始化根視窗
        root = ttk.Window(themename="superhero")
        
        # 初始化設定檔管理器並執行一次性的清理
        config_manager = ConfigManager("Minidoracat", "minidoracat_server_launch")
        config_manager.remove_legacy_configs()
        
        # 初始化管理器
        kcptube = KCPTubeManager()
        speedtest = SpeedTestManager()
        pz = ProjectZomboidManager()
        
        # 建立主視窗
        app = MainWindow(root, kcptube, speedtest, pz)
        
        # 啟動主迴圈
        root.mainloop()
    except Exception as e:
        logger.error(f"程式啟動失敗: {str(e)}")
        sys.exit(1)
