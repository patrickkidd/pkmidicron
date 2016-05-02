# -*- mode: python -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['/Users/patrick/Documents/dev/pkmidicron'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

if os.name == 'nt':
    console = False
    icon = 'icon.ico'
else:
    console = False
    icon = 'icon.icns'
             
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='PKMidiCron',
          debug=False,
          strip=False,
          upx=True,
          console=console, icon=icon)

if os.name == 'nt':
    pass
else:
    app = BUNDLE(exe,
                 name='PKMidiCron.app',
                 icon='icon.icns',
                 bundle_identifier='com.vedanamedia.PKMidiCron',
                 info_plist={
                     'NSHighResolutionCapable': True
                 })
