pkmidicron/mainwindow_form.py: pkmidicron/mainwindow.ui
	pyuic5 pkmidicron/mainwindow.ui -o pkmidicron/mainwindow_form.py


clean:
	rm -rf pkmidicron/*_form.py
