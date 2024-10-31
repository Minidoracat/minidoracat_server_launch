import json
from datetime import datetime
from pathlib import Path
import threading
from logger import logger

class SpeedTestManager:
    """速度測試管理類"""
    def __init__(self):
        self._speedtest = None
        self._running = False
        self._current_test = None
        self.config_file = Path('config.json')
        self._load_config()
        logger.info("速度測試管理器初始化完成")
    
    def _load_config(self):
        """載入設定檔"""
        try:
            if self.config_file.exists():
                self.config = json.loads(self.config_file.read_text(encoding='utf-8'))
                logger.info("成功載入速度設定")
            else:
                self.config = {
                    'download_speed': 0,  # Mbps
                    'upload_speed': 0,    # Mbps
                    'last_test': None,
                    'manual_mode': False  # 是否使用手動設定的速度
                }
                self._save_config()
        except Exception as e:
            logger.error(f"載入速度設定失敗: {str(e)}")
            self.config = {
                'download_speed': 0,
                'upload_speed': 0,
                'last_test': None,
                'manual_mode': False
            }
    
    def _save_config(self):
        """儲存設定檔"""
        try:
            self.config_file.write_text(
                json.dumps(self.config, indent=4, ensure_ascii=False),
                encoding='utf-8'
            )
            logger.info("成功儲存速度設定")
        except Exception as e:
            logger.error(f"儲存速度設定失敗: {str(e)}")
    
    def set_manual_speeds(self, download_speed: float, upload_speed: float):
        """手動設定速度"""
        self.config['download_speed'] = download_speed
        self.config['upload_speed'] = upload_speed
        self.config['manual_mode'] = True
        self.config['last_test'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_config()
        logger.info(f"手動設定速度 - 下載: {download_speed}M, 上傳: {upload_speed}M")
    
    def get_current_speeds(self):
        """獲取當前速度設定"""
        return {
            'download_speed': self.config['download_speed'],
            'upload_speed': self.config['upload_speed'],
            'manual_mode': self.config['manual_mode'],
            'last_test': self.config.get('last_test', None)
        }
    
    def _initialize_speedtest(self):
        """初始化 speedtest"""
        try:
            # 延遲導入 speedtest-cli，避免啟動時就載入
            import speedtest
            self._speedtest = speedtest.Speedtest(secure=True)
            logger.info("Speedtest 初始化成功")
            return True
        except ImportError:
            logger.error("無法載入 speedtest-cli 模組")
            return False
        except Exception as e:
            logger.error(f"Speedtest 初始化失敗: {str(e)}")
            return False
    
    def _get_best_server(self):
        """獲取最佳伺服器"""
        try:
            if not self._speedtest:
                return None
            
            logger.info("正在尋找最佳伺服器...")
            best_server = self._speedtest.get_best_server()
            logger.info(f"找到最佳伺服器: {best_server['host']} ({best_server['country']})")
            return best_server
        except Exception as e:
            logger.error(f"尋找最佳伺服器失敗: {str(e)}")
            return None
    
    def _test_download(self):
        """測試下載速度"""
        try:
            if not self._speedtest:
                return 0
            
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
            if not self._speedtest:
                return 0
            
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
                    raise Exception("Speedtest 初始化失敗")
                
                # 獲取最佳伺服器
                server = self._get_best_server()
                if not server:
                    raise Exception("無法找到合適的測試伺服器")
                
                # 測試下載速度
                result['download_speed'] = self._test_download()
                
                # 測試上傳速度
                result['upload_speed'] = self._test_upload()
                
                # 儲存結果
                self.config['download_speed'] = result['download_speed']
                self.config['upload_speed'] = result['upload_speed']
                self.config['last_test'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.config['manual_mode'] = False
                self._save_config()
                
                logger.info("速度測試完成")
            except Exception as e:
                logger.error(f"速度測試過程中發生錯誤: {str(e)}")
            finally:
                self._running = False
                self._speedtest = None  # 清理 speedtest 實例
                callback(result)
        
        # 在新執行緒中運行測試
        self._current_test = threading.Thread(target=run_test, daemon=True)
        self._current_test.start()
        return True
    
    def is_running(self):
        """檢查是否正在進行測試"""
        return self._running
    
    def update_conf_files(self):
        """更新所有設定檔中的頻寬設定"""
        try:
            conf_dir = Path('conf')
            if not conf_dir.exists():
                logger.error("找不到設定檔目錄")
                return False
            
            # 獲取當前速度設定
            speeds = self.get_current_speeds()
            download = int(speeds['download_speed'])
            upload = int(speeds['upload_speed'])
            
            # 遍歷所有 .conf 檔案
            for conf_file in conf_dir.glob('*.conf'):
                try:
                    # 讀取原始內容
                    content = conf_file.read_text(encoding='utf-8').splitlines()
                    
                    # 更新內容
                    new_content = []
                    for line in content:
                        if line.startswith('inbound_bandwidth='):
                            line = f'inbound_bandwidth={download}M'
                        elif line.startswith('outbound_bandwidth='):
                            line = f'outbound_bandwidth={upload}M'
                        new_content.append(line)
                    
                    # 寫回檔案
                    conf_file.write_text('\n'.join(new_content) + '\n', encoding='utf-8')
                    logger.info(f"已更新設定檔: {conf_file.name}")
                except Exception as e:
                    logger.error(f"更新設定檔 {conf_file.name} 失敗: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"更新設定檔時發生錯誤: {str(e)}")
            return False
