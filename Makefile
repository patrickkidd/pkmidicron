all: pkmidicron

ifeq ($(OS), Windows_NT)
pkmidicron: dist/PKMidiCron.exe
else
pkmidicron: dist/PKMidiCron.app/Contents/MacOS/PKMidiCron
endif

dist/PKMidiCron.exe:  resources pkmidicron/*.py main.py
	pyinstaller pkmidicron.spec
    
dist/PKMidiCron.app/Contents/MacOS/PKMidiCron: resources pkmidicron/*.py main.py
	pyinstaller pkmidicron.spec
	cp Info.plist dist/PKMidiCron.app/Contents/

install: pkmidicron
	rm -rf /Applications/PKMidiCron.app
	cp -Rf dist/PKMidiCron.app /Applications

resources: pkmidicron/mainwindow_form.py pkmidicron/preferencesdialog_form.py pkmidicron/resources.py

pkmidicron/mainwindow_form.py: pkmidicron/mainwindow.ui
	pyuic5 pkmidicron/mainwindow.ui -o pkmidicron/mainwindow_form.py

pkmidicron/preferencesdialog_form.py: pkmidicron/preferencesdialog.ui
	pyuic5 pkmidicron/preferencesdialog.ui -o pkmidicron/preferencesdialog_form.py

pkmidicron/resources.py: resources/resources.qrc resources/*
	pyrcc5 resources/resources.qrc -o pkmidicron/resources.py

clean:
ifeq ($(OS), Windows_NT)
	del pkmidicron\*_form.py 2>NUL
	del resources\resources.py 2>NUL
	rd /s/q build dist
else
	rm -rf pkmidicron/*_form.py resources/resources.py
	rm -rf `find . -name __pycache__`
	rm -rf build dist
endif
    
