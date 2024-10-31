import threading
import json
from datetime import datetime
from pathlib import Path
from logger import logger
import traceback
import sys
import os
import time

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
                # 確保 speed_test 分類存在
                if 'speed_test' not in self.config:
                    self.config['speed_test'] = {
                        'download_speed': 0,
                        'upload_speed': 0,
                        'last_test': None,
                        'manual_mode': False,
                        'auto_apply': False
                    }
                    self._save_config()
                logger.info("成功載入速度設定")
            else:
                self.config = {
                    'speed_test': {
                        'download_speed': 0,  # Mbps
                        'upload_speed': 0,    # Mbps
                        'last_test': None,
                        'manual_mode': False,  # 是否使用手動設定的速度
                        'auto_apply': False    # 是否自動套用到節點設定
                    }
                }
                self._save_config()
        except Exception as e:
            logger.error(f"載入速度設定失敗: {str(e)}")
            self.config = {
                'speed_test': {
                    'download_speed': 0,
                    'upload_speed': 0,
                    'last_test': None,
                    'manual_mode': False,
                    'auto_apply': False
                }
            }
    
    def _save_config(self):
        """儲存設定檔"""
        try:
            # 確保速度值為整數
            self.config['speed_test']['download_speed'] = int(self.config['speed_test']['download_speed'])
            self.config['speed_test']['upload_speed'] = int(self.config['speed_test']['upload_speed'])
            
            self.config_file.write_text(
                json.dumps(self.config, indent=4, ensure_ascii=False),
                encoding='utf-8'
            )
            logger.info("成功儲存速度設定")
        except Exception as e:
            logger.error(f"儲存速度設定失敗: {str(e)}")
    
    def set_manual_speeds(self, download_speed: float, upload_speed: float):
        """手動設定速度"""
        self.config['speed_test']['download_speed'] = int(download_speed)
        self.config['speed_test']['upload_speed'] = int(upload_speed)
        self.config['speed_test']['manual_mode'] = True
        self.config['speed_test']['last_test'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_config()
        logger.info(f"手動設定速度 - 下載: {int(download_speed)}M, 上傳: {int(upload_speed)}M")
        
        # 如果啟用了自動套用，則更新節點設定
        if self.config['speed_test'].get('auto_apply', False):
            self.update_conf_files()
    
    def get_current_speeds(self):
        """獲取當前速度設定"""
        speed_test = self.config.get('speed_test', {})
        return {
            'download_speed': speed_test.get('download_speed', 0),
            'upload_speed': speed_test.get('upload_speed', 0),
            'manual_mode': speed_test.get('manual_mode', False),
            'last_test': speed_test.get('last_test', None),
            'auto_apply': speed_test.get('auto_apply', False)
        }
    
    def set_auto_apply(self, enabled: bool):
        """設定是否自動套用到節點設定"""
        self.config['speed_test']['auto_apply'] = enabled
        self._save_config()
        logger.info(f"{'啟用' if enabled else '停用'}自動套用速度設定到節點")
    
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
            logger.error(f"錯誤堆疊: {traceback.format_exc()}")
            return False
        except Exception as e:
            logger.error(f"Speedtest 初始化失敗: {str(e)}")
            logger.error(f"錯誤堆疊: {traceback.format_exc()}")
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
                    raise Exception("找不到可用的伺服器")
                
                # 選擇最佳伺服器
                logger.info("正在選擇最佳伺服器...")
                best_server = self._speedtest.get_best_server()
                logger.info(f"找到最佳伺服器: {best_server['host']} ({best_server['country']})")
                return best_server
            except Exception as e:
                logger.error(f"尋找最佳伺服器失敗 (嘗試 {attempt + 1}/{max_retries}): {str(e)}")
                logger.error(f"錯誤堆疊: {traceback.format_exc()}")
                
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
            logger.error(f"錯誤堆疊: {traceback.format_exc()}")
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
            logger.error(f"錯誤堆疊: {traceback.format_exc()}")
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
                
                # 儲存結果到 config.json
                self.config['speed_test']['download_speed'] = int(result['download_speed'])
                self.config['speed_test']['upload_speed'] = int(result['upload_speed'])
                self.config['speed_test']['manual_mode'] = False
                self.config['speed_test']['last_test'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._save_config()
                
                # 如果啟用了自動套用，則更新節點設定
                if self.config['speed_test'].get('auto_apply', False):
                    self.update_conf_files()
                
                logger.info("速度測試完成")
            except Exception as e:
                logger.error(f"速度測試過程中發生錯誤: {str(e)}")
                logger.error(f"錯誤堆疊: {traceback.format_exc()}")
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
