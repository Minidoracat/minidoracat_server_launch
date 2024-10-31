import os
import shutil
import subprocess
import time
from pathlib import Path

def ensure_dir(path):
    """確保目錄存在"""
    if not os.path.exists(path):
        os.makedirs(path)

def safe_remove(path):
    """安全地移除檔案或目錄"""
    max_retries = 3
    retry_delay = 1  # 秒

    for attempt in range(max_retries):
        try:
            if os.path.isfile(path):
                os.unlink(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            return True
        except PermissionError:
            if attempt < max_retries - 1:
                print(f"無法刪除 {path}，可能正在使用中。等待 {retry_delay} 秒後重試...")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指數退避
            else:
                print(f"警告: 無法刪除 {path}，跳過...")
                return False
        except Exception as e:
            print(f"刪除 {path} 時發生錯誤: {str(e)}")
            return False
    return False

def main():
    print("開始建置...")
    
    # 清理舊的建置檔案
    paths_to_clean = ['dist', 'build', 'release']
    for path in paths_to_clean:
        if os.path.exists(path):
            print(f"清理 {path}...")
            if not safe_remove(path):
                print(f"警告: 無法完全清理 {path}，繼續建置...")
    
    # 使用 PyInstaller 打包
    print("正在打包程式...")
    try:
        subprocess.run([
            'pyinstaller',
            '--noconfirm',
            '--onefile',
            '--windowed',
            '--add-data', 'version.json;.',
            'main.py'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"打包失敗: {str(e)}")
        return
    
    # 建立發布目錄並只保留執行檔
    print("正在建立發布套件...")
    try:
        ensure_dir('release')
        
        # 只複製執行檔
        shutil.copy('dist/main.exe', 'release/kcptube_launcher.exe')
        
        # 清理其他建置檔案
        print("清理建置檔案...")
        for path in ['dist', 'build']:
            if os.path.exists(path):
                safe_remove(path)
        
        # 移除 spec 檔案
        if os.path.exists('main.spec'):
            os.unlink('main.spec')
        
        print("建置完成！執行檔在 release/kcptube_launcher.exe")
    except Exception as e:
        print(f"建立發布套件時發生錯誤: {str(e)}")

if __name__ == '__main__':
    main()
