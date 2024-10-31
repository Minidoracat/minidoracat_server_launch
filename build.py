import os
import shutil
import subprocess

def ensure_dir(path):
    """確保目錄存在"""
    if not os.path.exists(path):
        os.makedirs(path)

def main():
    print("開始建置...")
    
    # 清理舊的建置檔案
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('release'):
        shutil.rmtree('release')
    
    # 使用 PyInstaller 打包
    print("正在打包程式...")
    subprocess.run([
        'pyinstaller',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--add-data', 'kcptube/version.txt;kcptube',
        'main.py'
    ], check=True)
    
    # 建立發布目錄結構
    print("正在建立發布套件...")
    ensure_dir('release')
    ensure_dir('release/conf')
    
    # 複製檔案
    shutil.copy('dist/main.exe', 'release/kcptube_launcher.exe')
    shutil.copy('kcptube/version.txt', 'release/version.txt')
    shutil.copy('README.md', 'release/README.md')
    
    # 複製所有設定檔
    for file in os.listdir('conf'):
        if file.endswith('.conf'):
            shutil.copy(os.path.join('conf', file), os.path.join('release/conf', file))
    
    print("建置完成！檔案在 release 目錄中")

if __name__ == '__main__':
    main()
