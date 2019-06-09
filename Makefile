UNAME := $(shell uname)


#	@echo "targets: ios, osx, simulator"

QMAKE = `which qmake` # $(SYSROOT)/build/qt5/bin/qmake


FORMS = pkmidicron/mainwindow_form.py \
		pkmidicron/preferencesdialog_form.py

SOURCES = pkmidicron.pdy pkmidicron/*.py pkmidicron/build_uuid.py


all: $(SOURCES) $(FORMS) pkmidicron/resources.py rtmidi

pkmidicron/mainwindow_form.py: pkmidicron/mainwindow.ui
	pyuic5 pkmidicron/mainwindow.ui -o pkmidicron/mainwindow_form.py

pkmidicron/preferencesdialog_form.py: pkmidicron/preferencesdialog.ui
	pyuic5 pkmidicron/preferencesdialog.ui -o pkmidicron/preferencesdialog_form.py

pkmidicron/resources.py: resources/resources.qrc resources/*
	pyrcc5 resources/resources.qrc -o pkmidicron/resources.py

pkmidicron/build_uuid.py: pkmidicron/version.py
	@python bin/update_build_uuid.py



forms: $(FORMS)

sources: $(SOURCES)

RTMIDI_PATH=pyrtmidi/build/`python bin/distutils_dir.py`

##
## rtmidi
##

$(RTMIDI_PATH)/rtmidi/_rtmidi.cpython-36m-darwin.so:
	cd pyrtmidi && python setup.py build

rtmidi: $(RTMIDI_PATH)/rtmidi/_rtmidi.cpython-36m-darwin.so

clean-rtmidi:
	rm -rf pyrtmidi/build

##
## Dev
##

run: all
	@ # QT_LOGGING_RULES=qt.qpa=true
	echo $(RTMIDI_PATH)
	@PYTHONPATH=$(RTMIDI_PATH) python main.py # 2>&1 | grep -v "_q_startOperation was called more than once"

module: $(SOURCES) $(FORMS) pkmidicron/resources.py
	@PYTHONPATH=`pwd`/vendor python main.py --module ${name} # 2>&1 | grep -v "QMacCGContext"


debug: $(SOURCES) $(FORMS)
	@python -m pudb.run main.py
	# @python -m pdb main.py # 2>&1 | grep -v "QMacCGContext"


profile: $(SOURCES) $(FORMS)
	# @python -m cProfile -s tottime main.py
	@python main_profile.py

run-tests:
	# https://coverage.readthedocs.io/en/v4.5.x/cmd.html
	PYTHONPATH=. pytest tests

tests-coverage:
	# https://coverage.readthedocs.io/en/v4.5.x/cmd.html
	PYTHONPATH=. pytest --cov=pkmidicron tests

tests: run-tests

##
## OS X
##

build/osx-config/Info.plist: pkmidicron/version.py
	@python bin/update_plist_version.py

build/osx/PKMidiCron.pro: pkmidicron.pdy $(SOURCES) $(FORMS) build/osx-config/Info.plist
	pyqtdeploy-build --verbose --sysroot ~/dev/vendor/sysroot-macos-64 --build-dir build/osx pkmidicron.pdy

build/osx/PKMidiCron.xcodeproj/project.pbxproj: build/osx/PKMidiCron.pro build/osx-config/Info.plist build/osx-config/PKMidicron.icns build/osx-config/PKMidicron-Document.icns
	rsync -avzq build/osx-config/* build/osx
	rsync -avzq resources/* build/osx/resources/pkmidicron/resources
	cd build/osx && qmake -spec macx-xcode CONFIG+=debug

osx: build/osx/PKMidiCron.xcodeproj/project.pbxproj
	# bin/filter_xcodeproj.rb osx "PKMidiCron" "darwin64.S" 2> /dev/null
	open build/osx/PKMidiCron.xcodeproj

osx-release:
	pyqtdeploy-build --verbose --sysroot ~/dev/vendor/sysroot-macos-64 --build-dir build/osx pkmidicron.pdy
	rsync -avzq build/osx-config/* build/osx
	rsync -avzq resources/* build/osx/resources/pkmidicron/resources
	cd build/osx && qmake -spec macx-xcode CONFIG-=debug CONFIG+=release
	bin/filter_xcodeproj.rb osx "PKMidiCron" "darwin64.S" 2> /dev/null
	xcodebuild -scheme "PKMidiCron" -configuration Release -project build/osx/PKMidiCron.xcodeproj build
	open build/osx/Release

clean-osx:
	rm -rf build/osx/*




##
## Windows
##

clean-win32:
	rm -rf build/win32




##
## clean
##

clean: clean-rtmidi clean-osx clean-win32
	rm -f pkmidicron/resources.py
	rm -rf `find . -name xcuserdata`
	rm -rf `find . -name __pycache__`
	rm -rf `find . -name .qmake.stash`



##
## test_pdy
##

test_pdy: test_pdy.pdy test_pdy.py
	pyqtdeploy-build test_pdy.pdy
	cd build-macos-64 && qmake -spec macx-xcode CONFIG+=debug && open test.xcodeproj

