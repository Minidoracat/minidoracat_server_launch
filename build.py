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
        # 建立 spec 檔案
        spec_content = """
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('version.json', '.')],
    hiddenimports=[
        'speedtest',
        'speedtest.api',
        'speedtest.cli',
        'speedtest.config',
        'speedtest.constants',
        'speedtest.database',
        'speedtest.errors',
        'speedtest.results',
        'speedtest.upload',
        'speedtest.utils',
        'pkg_resources.py2_warn'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
        
        # 寫入 spec 檔案
        with open('main.spec', 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        # 使用 spec 檔案打包
        subprocess.run([
            'pyinstaller',
            '--noconfirm',
            '--clean',  # 清理快取
            'main.spec'
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
