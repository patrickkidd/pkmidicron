# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pkmidicron/preferencesdialog.ui'
#
# Created: Fri Oct 31 17:28:29 2014
#      by: PyQt5 UI code generator 5.3.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_PreferencesDialog(object):
    def setupUi(self, PreferencesDialog):
        PreferencesDialog.setObjectName("PreferencesDialog")
        PreferencesDialog.setWindowModality(QtCore.Qt.WindowModal)
        PreferencesDialog.resize(409, 378)
        PreferencesDialog.setMinimumSize(QtCore.QSize(250, 0))
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(PreferencesDialog)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.stackedWidget = QtWidgets.QStackedWidget(PreferencesDialog)
        self.stackedWidget.setObjectName("stackedWidget")
        self.generalPage = QtWidgets.QWidget()
        self.generalPage.setObjectName("generalPage")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.generalPage)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        spacerItem = QtWidgets.QSpacerItem(17, 17, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout_4.addItem(spacerItem)
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
        self.verticalLayout_4.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(self.generalPage)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setContentsMargins(-1, -1, -1, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.portList = ListWidget(self.groupBox_2)
        self.portList.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.portList.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.portList.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.portList.setObjectName("portList")
        self.verticalLayout_3.addWidget(self.portList)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.addPortButton = QtWidgets.QPushButton(self.groupBox_2)
        self.addPortButton.setObjectName("addPortButton")
        self.horizontalLayout.addWidget(self.addPortButton)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout_4.addWidget(self.groupBox_2)
        self.stackedWidget.addWidget(self.generalPage)
        self.page_2 = QtWidgets.QWidget()
        self.page_2.setObjectName("page_2")
        self.stackedWidget.addWidget(self.page_2)
        self.verticalLayout_5.addWidget(self.stackedWidget)

        self.retranslateUi(PreferencesDialog)
        self.stackedWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(PreferencesDialog)

    def retranslateUi(self, PreferencesDialog):
        _translate = QtCore.QCoreApplication.translate
        PreferencesDialog.setWindowTitle(_translate("PreferencesDialog", "Dialog"))
        self.groupBox.setTitle(_translate("PreferencesDialog", "Toolbar Icons"))
        self.iconOnlyButton.setText(_translate("PreferencesDialog", "Icon Only"))
        self.iconPlusNameButton.setText(_translate("PreferencesDialog", "Icon + Name"))
        self.groupBox_2.setTitle(_translate("PreferencesDialog", "Ports"))
        self.addPortButton.setText(_translate("PreferencesDialog", "+"))

from .util import ListWidget