import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
import requests
from logger import logger
from version_manager import VersionManager
from config_manager import ConfigManager

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
    
    def _download_kcptube(self, version):
        """下載 KCPTube 執行檔"""
        try:
            version_path = Path('kcptube') / version
            version_path.mkdir(exist_ok=True)
            exe_path = version_path / 'kcptube.exe'
            
            logger.info(f"正在從 GitHub 下載 KCPTube {version} 版本...")
            url = f"https://raw.githubusercontent.com/Minidoracat/kcptube_launch/main/kcptube/{version}/kcptube.exe"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            exe_path.write_bytes(response.content)
            logger.info(f"成功下載 KCPTube {version} 版本")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"下載 KCPTube {version} 版本失敗: {str(e)}")
            if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 404:
                logger.error(f"找不到 KCPTube {version} 版本，請確認版本號是否正確")
            return False
        except Exception as e:
            logger.error(f"下載 KCPTube {version} 版本時發生錯誤: {str(e)}")
            return False
    
    def _ensure_kcptube_exists(self, version):
        """確保指定版本的 KCPTube 存在"""
        version_path = Path('kcptube') / version
        exe_path = version_path / 'kcptube.exe'
        
        if not exe_path.exists():
            logger.info(f"未找到 KCPTube {version} 版本，嘗試下載...")
            return self._download_kcptube(version)
        
        return True
    
    def sync_configs(self):
        """同步設定檔"""
        return self.config_manager.sync_configs()
    
    def start_kcptube(self, config_path):
        """啟動 KCPTube"""
        if self.process:
            logger.warning("KCPTube 已在運行中")
            return False
        
        # 確保有正確版本的執行檔
        kcptube_version = self.version_manager.kcptube_version
        if not self._ensure_kcptube_exists(kcptube_version):
            logger.error("無法獲取 KCPTube 執行檔")
            return False
        
        version_path = Path('kcptube') / kcptube_version
        exe_path = version_path / 'kcptube.exe'
        
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
