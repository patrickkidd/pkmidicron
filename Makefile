all: pkmidicron

pkmidicron: dist/PKMidiCron.app/Contents/MacOS/PKMidiCron

dist/PKMidiCron.app/Contents/MacOS/PKMidiCron: resources pkmidicron/*.py
	pyinstaller pkmidicron.spec
	cp Info.plist dist/PKMidiCron.app/Contents/

install: pkmidicron
	cp -Rf build/PKMidiCron.app /Applications

resources: pkmidicron/mainwindow_form.py pkmidicron/preferencesdialog_form.py pkmidicron/resources.py

pkmidicron/mainwindow_form.py: pkmidicron/mainwindow.ui
	pyuic5 pkmidicron/mainwindow.ui -o pkmidicron/mainwindow_form.py

pkmidicron/preferencesdialog_form.py: pkmidicron/preferencesdialog.ui
	pyuic5 pkmidicron/preferencesdialog.ui -o pkmidicron/preferencesdialog_form.py

pkmidicron/resources.py: resources/resources.qrc resources/*
	pyrcc5 resources/resources.qrc -o pkmidicron/resources.py

clean:
	rm -rf pkmidicron/*_form.py resources/resources.py
	rm -rf `find . -name __pycache__`
	rm -rf build dist
