all: pkmidicron/mainwindow_form.py pkmidicron/resources.py

pkmidicron/mainwindow_form.py: pkmidicron/mainwindow.ui
	pyuic5 pkmidicron/mainwindow.ui -o pkmidicron/mainwindow_form.py

pkmidicron/resources.py: resources/resources.qrc
	pyrcc5 resources/resources.qrc -o pkmidicron/resources.py

clean:
	rm -rf pkmidicron/*_form.py resources/resources.py
