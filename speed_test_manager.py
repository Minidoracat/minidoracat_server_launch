import threading
from datetime import datetime
import traceback
import sys
import os
import time
from logger import logger

class SpeedTestManager:
    """速度測試管理類"""
    def __init__(self, config_manager):
        self._speedtest = None
        self._running = False
        self._current_test = None
        self.config_manager = config_manager
        logger.info("速度測試管理器初始化完成")
    
    def _initialize_speedtest(self):
        """初始化 speedtest"""
        try:
            logger.info("開始初始化 Speedtest...")
            
            # 設定環境變數
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            if sys.platform == 'win32':
                os.environ['NO_PROXY'] = '*'
            
            # 添加 Python 2.x 相容性
            if 'builtins' in sys.modules:
                sys.modules['__builtin__'] = sys.modules['builtins']
            
            logger.info("已設定環境變數和相容性")
            
            # 延遲導入 speedtest 模組
            import speedtest
            logger.info("成功導入 speedtest 模組")
            
            # 初始化 speedtest
            logger.info("正在初始化 Speedtest 實例...")
            self._speedtest = speedtest.Speedtest(
                secure=True,
                timeout=30  # 增加超時時間
            )
            logger.info("成功創建 Speedtest 實例")
            
            # 預先載入設定
            logger.info("正在載入 Speedtest 設定...")
            self._speedtest.get_config()
            logger.info("成功載入設定")
            
            logger.info("Speedtest 初始化成功")
            return True
        except ImportError as e:
            logger.error(f"無法載入 speedtest 模組: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Speedtest 初始化失敗: {str(e)}")
            return False
    
    def _get_best_server(self, max_retries=3):
        """獲取最佳伺服器"""
        for attempt in range(max_retries):
            try:
                logger.info(f"正在尋找最佳伺服器 (嘗試 {attempt + 1}/{max_retries})...")
                
                # 先獲取伺服器列表
                logger.info("正在獲取伺服器列表...")
                servers = self._speedtest.get_servers()
                
                server_count = sum(len(servers_by_id) for servers_by_id in servers.values())
                logger.info(f"找到 {server_count} 個伺服器")
                
                if server_count == 0:
                    logger.warning("未找到可用的伺服器，將在稍後重試")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        logger.info(f"等待 {wait_time} 秒後重試...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("已達到最大重試次數，仍未找到可用的伺服器")
                        return None
                
                # 選擇最佳伺服器
                logger.info("正在選擇最佳伺服器...")
                best_server = self._speedtest.get_best_server()
                logger.info(f"找到最佳伺服器: {best_server['host']} ({best_server['country']})")
                return best_server
            except Exception as e:
                logger.warning(f"尋找最佳伺服器時發生錯誤 (嘗試 {attempt + 1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                else:
                    logger.error("已達到最大重試次數")
                    return None
        
        return None
    
    def _test_download(self):
        """測試下載速度"""
        try:
            logger.info("正在測試下載速度...")
            download_speed = self._speedtest.download() / 1_000_000  # 轉換為 Mbps
            logger.info(f"下載速度: {download_speed:.2f} Mbps")
            return download_speed
        except Exception as e:
            logger.error(f"測試下載速度失敗: {str(e)}")
            return 0
    
    def _test_upload(self):
        """測試上傳速度"""
        try:
            logger.info("正在測試上傳速度...")
            upload_speed = self._speedtest.upload() / 1_000_000  # 轉換為 Mbps
            logger.info(f"上傳速度: {upload_speed:.2f} Mbps")
            return upload_speed
        except Exception as e:
            logger.error(f"測試上傳速度失敗: {str(e)}")
            return 0
    
    def start_test(self, callback):
        """開始速度測試
        
        Args:
            callback: 回調函數，接收測試結果字典作為參數
                     結果字典包含: download_speed, upload_speed
        """
        if self._running:
            logger.warning("速度測試已在進行中")
            return False
        
        def run_test():
            self._running = True
            result = {
                'download_speed': 0,
                'upload_speed': 0
            }
            
            try:
                # 初始化
                if not self._initialize_speedtest():
                    logger.error("Speedtest 初始化失敗")
                    return
                
                # 獲取最佳伺服器
                server = self._get_best_server()
                if not server:
                    logger.error("無法找到合適的測試伺服器")
                    return
                
                # 測試下載速度
                result['download_speed'] = self._test_download()
                
                # 測試上傳速度
                result['upload_speed'] = self._test_upload()
                
                # 更新設定
                settings = {
                    'download_speed': int(result['download_speed']),
                    'upload_speed': int(result['upload_speed']),
                    'manual_mode': False,
                    'last_test': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.config_manager.set_speed_settings(settings)
                
                # 如果啟用了自動套用，則更新節點設定
                if self.config_manager.is_auto_apply_enabled():
                    self.config_manager.update_node_bandwidth(
                        settings['download_speed'],
                        settings['upload_speed']
                    )
                
                logger.info("速度測試完成")
            except Exception as e:
                logger.error(f"速度測試過程中發生錯誤: {str(e)}")
            finally:
                # 清理資源
                self._speedtest = None
                self._running = False
                callback(result)
        
        # 在新執行緒中運行測試
        self._current_test = threading.Thread(target=run_test, daemon=True)
        self._current_test.start()
        return True
    
    def is_running(self):
        """檢查是否正在進行測試"""
        return self._running
    
    def set_manual_speeds(self, download_speed: float, upload_speed: float):
        """手動設定速度"""
        settings = {
            'download_speed': int(download_speed),
            'upload_speed': int(upload_speed),
            'manual_mode': True,
            'last_test': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.config_manager.set_speed_settings(settings)
        logger.info(f"手動設定速度 - 下載: {int(download_speed)}M, 上傳: {int(upload_speed)}M")
        
        # 如果啟用了自動套用，則更新節點設定
        if self.config_manager.is_auto_apply_enabled():
            self.config_manager.update_node_bandwidth(
                settings['download_speed'],
                settings['upload_speed']
            )
    
    def get_current_speeds(self):
        """獲取當前速度設定"""
        return self.config_manager.get_speed_settings()
    
    def set_auto_apply(self, enabled: bool):
        """設定是否自動套用到節點設定"""
        self.config_manager.set_auto_apply(enabled)
