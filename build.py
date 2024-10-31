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
    
    # 檢查圖標檔案
    ico_path = Path('image/app.ico').absolute()
    if not ico_path.exists():
        print("警告: 找不到 app.ico 檔案，將不會設定應用程式圖標")
    else:
        print(f"找到圖標檔案: {ico_path}")
    
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
        spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('version.json', '.'),
        ('image/*.png', 'image'),
        ('image/app.ico', 'image'),
    ],
    hiddenimports=[
        'speedtest',
        'PIL',
        'PIL._imagingtk',
        'PIL._tkinter_finder',
        'ttkbootstrap',
        'ttkbootstrap.themes',
        'ttkbootstrap.style',
        'ttkbootstrap.widgets',
        'ttkbootstrap.window',
        'ttkbootstrap.dialogs',
        'ttkbootstrap.localization',
        'pkg_resources.py2_warn'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='minidoracat_server_launch',
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
    version='version.txt',
    icon=r'{ico_path}',
)
"""
        
        # 建立版本資訊檔案
        version_content = """
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 2, 2),
    prodvers=(1, 0, 2, 2),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Minidoracat'),
         StringStruct(u'FileDescription', u'Minidoracat 伺服器專用優化工具'),
         StringStruct(u'FileVersion', u'1.0.2.2'),
         StringStruct(u'InternalName', u'minidoracat_server_launch'),
         StringStruct(u'LegalCopyright', u'Copyright (c) 2024 Minidoracat'),
         StringStruct(u'OriginalFilename', u'minidoracat_server_launch.exe'),
         StringStruct(u'ProductName', u'Minidoracat 伺服器專用優化工具'),
         StringStruct(u'ProductVersion', u'1.0.2.2')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
        
        # 寫入版本資訊檔案
        with open('version.txt', 'w', encoding='utf-8') as f:
            f.write(version_content)
        
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
        shutil.copy('dist/minidoracat_server_launch.exe', 'release/minidoracat_server_launch.exe')
        
        # 清理其他建置檔案
        print("清理建置檔案...")
        for path in ['dist', 'build', 'version.txt']:
            if os.path.exists(path):
                safe_remove(path)
        
        # 移除 spec 檔案
        if os.path.exists('main.spec'):
            os.unlink('main.spec')
        
        print("建置完成！執行檔在 release/minidoracat_server_launch.exe")
    except Exception as e:
        print(f"建立發布套件時發生錯誤: {str(e)}")

if __name__ == '__main__':
    main()
