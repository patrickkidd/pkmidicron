# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pkmidicron/preferencesdialog.ui'
#
# Created: Wed Oct 29 11:31:59 2014
#      by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_PreferencesDialog(object):
    def setupUi(self, PreferencesDialog):
        PreferencesDialog.setObjectName("PreferencesDialog")
        PreferencesDialog.setWindowModality(QtCore.Qt.WindowModal)
        PreferencesDialog.resize(400, 300)
        self.horizontalLayout = QtWidgets.QHBoxLayout(PreferencesDialog)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.stackedWidget = QtWidgets.QStackedWidget(PreferencesDialog)
        self.stackedWidget.setObjectName("stackedWidget")
        self.generalPage = QtWidgets.QWidget()
        self.generalPage.setObjectName("generalPage")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.generalPage)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout_2.addItem(spacerItem)
        self.groupBox = QtWidgets.QGroupBox(self.generalPage)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.iconOnlyButton = QtWidgets.QRadioButton(self.groupBox)
        self.iconOnlyButton.setObjectName("iconOnlyButton")
        self.verticalLayout.addWidget(self.iconOnlyButton)
        self.iconPlusNameButton = QtWidgets.QRadioButton(self.groupBox)
        self.iconPlusNameButton.setObjectName("iconPlusNameButton")
        self.verticalLayout.addWidget(self.iconPlusNameButton)
        self.verticalLayout_2.addWidget(self.groupBox)
        spacerItem1 = QtWidgets.QSpacerItem(20, 133, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem1)
        self.stackedWidget.addWidget(self.generalPage)
        self.page_2 = QtWidgets.QWidget()
        self.page_2.setObjectName("page_2")
        self.stackedWidget.addWidget(self.page_2)
        self.horizontalLayout.addWidget(self.stackedWidget)

        self.retranslateUi(PreferencesDialog)
        self.stackedWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(PreferencesDialog)

    def retranslateUi(self, PreferencesDialog):
        _translate = QtCore.QCoreApplication.translate
        PreferencesDialog.setWindowTitle(_translate("PreferencesDialog", "Dialog"))
        self.groupBox.setTitle(_translate("PreferencesDialog", "Toolbar Icons"))
        self.iconOnlyButton.setText(_translate("PreferencesDialog", "Icon Only"))
        self.iconPlusNameButton.setText(_translate("PreferencesDialog", "Icon + Name"))

