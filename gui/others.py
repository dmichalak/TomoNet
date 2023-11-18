import logging
import os.path
import shutil
import mrcfile
import math

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QTabWidget, QMessageBox


from TomoNet.util import browse
import os, glob
from TomoNet.util.utils import check_log_file, getLogContent, string2float, getRGBs
from TomoNet.util.utils import mkfolder

from TomoNet.util.geometry import get_raw_shifts_PEET, apply_slicerRot_PEET, PEET2Relion, Relion2ChimeraX, getNeighbors

import numpy as np
import math
import starfile

from scipy.spatial import distance_matrix
from scipy.spatial.distance import pdist, squareform

class OtherUtils(QTabWidget):
    def __init__(self):
        super().__init__()
        
        self.setting_file ="OtherUtils/otherUtils.setting"
        
        self.log_file = "OtherUtils/otherUtils.log"

        self.others_folder = "OtherUtils"
        
        check_log_file(self.log_file, "OtherUtils")
        
        self.logger = logging.getLogger(__name__)
        handler = logging.FileHandler(filename=self.log_file, mode='a')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        formatter.datefmt = "%y-%m-%d %H:%M:%S"
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        self.fileSystemWatcher = QtCore.QFileSystemWatcher(self)
        self.fileSystemWatcher.addPath(self.log_file)
        self.fileSystemWatcher.fileChanged.connect(self.update_log_window)

        self.setupUi()

    def setupUi(self):
        scriptDir = os.path.dirname(os.path.realpath(__file__))

        self.icon = QtGui.QIcon()
        self.icon.addPixmap(QtGui.QPixmap("{}/icons/icon_folder.png".format(scriptDir)), QtGui.QIcon.Normal, QtGui.QIcon.Off)


        self.setUI_tab1()

        self.setUI_tab2()

        self.addTab(self.tab, "Recenter {} Rotate {} Assemble to .star file".format("|","|"))

        self.addTab(self.tab2, "3D Subtomogram Place Back")


        for child in self.findChildren(QtWidgets.QLineEdit):
            child.textChanged.connect(self.save_setting)

        self.pushButton_expand_result_folder.clicked.connect\
             (lambda: browse.browseFolderSlot(self.lineEdit_expand_result_folder)) 
        
        self.pushButton_data_star_file.clicked.connect\
            (lambda: browse.browseSlot(self.lineEdit_data_star_file, 'star')) 
        self.pushButton_fitin_map_file.clicked.connect\
            (lambda: browse.browseSlot(self.lineEdit_fitin_map_file, 'map')) 

        self.pushButton_assemble.clicked.connect(self.assemble)
        self.pushButton_place_back.clicked.connect(self.placeback)

        self.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.retranslateUi_tab1()
        self.retranslateUi_tab2()
        self.read_settting()
    
    def setUI_tab1(self):
        #tab 1
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")

        self.horizontalLayout_1 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_1.setContentsMargins(10, 5, 10, 5)

        self.label_expand_result_folder = QtWidgets.QLabel(self.tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_expand_result_folder.sizePolicy().hasHeightForWidth())
        self.label_expand_result_folder.setSizePolicy(sizePolicy)
        self.label_expand_result_folder.setMinimumSize(QtCore.QSize(120, 0))
        self.label_expand_result_folder.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_expand_result_folder.setObjectName("label_expand_result_folder")
        self.horizontalLayout_1.addWidget(self.label_expand_result_folder)

        self.lineEdit_expand_result_folder = QtWidgets.QLineEdit(self.tab)
        self.lineEdit_expand_result_folder.setInputMask("")
        self.lineEdit_expand_result_folder.setObjectName("lineEdit_expand_result_folder")

        self.horizontalLayout_1.addWidget(self.lineEdit_expand_result_folder)

        self.pushButton_expand_result_folder = QtWidgets.QPushButton(self.tab)
        self.pushButton_expand_result_folder.setText("")
        self.pushButton_expand_result_folder.setIcon(self.icon)
        self.pushButton_expand_result_folder.setIconSize(QtCore.QSize(24, 24))
        self.pushButton_expand_result_folder.setMaximumSize(QtCore.QSize(160, 24))
        self.pushButton_expand_result_folder.setMinimumSize(QtCore.QSize(60, 24))
        self.pushButton_expand_result_folder.setObjectName("pushButton_expand_result_folder")
        self.horizontalLayout_1.addWidget(self.pushButton_expand_result_folder)

        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(10, 5, 10, 5)

        self.label_assemble_output_folder = QtWidgets.QLabel(self.tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_assemble_output_folder.sizePolicy().hasHeightForWidth())
        self.label_assemble_output_folder.setSizePolicy(sizePolicy)
        self.label_assemble_output_folder.setMinimumSize(QtCore.QSize(120, 0))
        self.label_assemble_output_folder.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_assemble_output_folder.setObjectName("label_assemble_output_folder")
        self.horizontalLayout_2.addWidget(self.label_assemble_output_folder)

        self.lineEdit_assemble_output_folder = QtWidgets.QLineEdit(self.tab)
        self.lineEdit_assemble_output_folder.setInputMask("")
        self.lineEdit_assemble_output_folder.setObjectName("lineEdit_assemble_output_folder")
        self.horizontalLayout_2.addWidget(self.lineEdit_assemble_output_folder)

        self.label_bin_factor = QtWidgets.QLabel(self.tab)
        self.label_bin_factor.setSizePolicy(sizePolicy)
        self.label_bin_factor.setMinimumSize(QtCore.QSize(120, 0))
        self.label_bin_factor.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_bin_factor.setObjectName("label_bin_factor")
        self.horizontalLayout_2.addWidget(self.label_bin_factor)

        self.lineEdit_bin_factor = QtWidgets.QLineEdit(self.tab)
        self.lineEdit_bin_factor.setInputMask("")
        self.lineEdit_bin_factor.setObjectName("lineEdit_bin_factor")
        self.horizontalLayout_2.addWidget(self.lineEdit_bin_factor)
        
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(10, 5, 10, 5)
        
        self.label_recenter = QtWidgets.QLabel(self.tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_recenter.sizePolicy().hasHeightForWidth())
        self.label_recenter.setSizePolicy(sizePolicy)
        self.label_recenter.setMinimumSize(QtCore.QSize(200, 0))
        self.label_recenter.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_recenter.setObjectName("label_recenter")
        self.horizontalLayout_3.addWidget(self.label_recenter)

        self.label_recenter_x = QtWidgets.QLabel(self.tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_recenter_x.sizePolicy().hasHeightForWidth())
        self.label_recenter_x.setSizePolicy(sizePolicy)
        self.label_recenter_x.setMinimumSize(QtCore.QSize(120, 0))
        self.label_recenter_x.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_recenter_x.setObjectName("label_recenter_x")
        self.horizontalLayout_3.addWidget(self.label_recenter_x)

        self.lineEdit_recenter_x = QtWidgets.QLineEdit(self.tab)
        self.lineEdit_recenter_x.setInputMask("")
        self.lineEdit_recenter_x.setObjectName("lineEdit_recenter_x")
        self.horizontalLayout_3.addWidget(self.lineEdit_recenter_x)

        self.label_recenter_y = QtWidgets.QLabel(self.tab)
        self.label_recenter_y.setSizePolicy(sizePolicy)
        self.label_recenter_y.setMinimumSize(QtCore.QSize(120, 0))
        self.label_recenter_y.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_recenter_y.setObjectName("label_recenter_y")
        self.horizontalLayout_3.addWidget(self.label_recenter_y)

        self.lineEdit_recenter_y = QtWidgets.QLineEdit(self.tab)
        self.lineEdit_recenter_y.setInputMask("")
        self.lineEdit_recenter_y.setObjectName("lineEdit_recenter_y")
        self.horizontalLayout_3.addWidget(self.lineEdit_recenter_y)

        self.label_recenter_z = QtWidgets.QLabel(self.tab)
        self.label_recenter_z.setSizePolicy(sizePolicy)
        self.label_recenter_z.setMinimumSize(QtCore.QSize(120, 0))
        self.label_recenter_z.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_recenter_z.setObjectName("label_recenter_z")
        self.horizontalLayout_3.addWidget(self.label_recenter_z)

        self.lineEdit_recenter_z = QtWidgets.QLineEdit(self.tab)
        self.lineEdit_recenter_z.setInputMask("")
        self.lineEdit_recenter_z.setObjectName("lineEdit_recenter_z")
        self.horizontalLayout_3.addWidget(self.lineEdit_recenter_z)

        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setContentsMargins(10, 5, 10, 5)
        
        self.label_rotation = QtWidgets.QLabel(self.tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_rotation.sizePolicy().hasHeightForWidth())
        self.label_rotation.setSizePolicy(sizePolicy)
        self.label_rotation.setMinimumSize(QtCore.QSize(200, 0))
        self.label_rotation.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_rotation.setObjectName("label_rotation")
        self.horizontalLayout_4.addWidget(self.label_rotation)

        self.label_rotation_x = QtWidgets.QLabel(self.tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_rotation_x.sizePolicy().hasHeightForWidth())
        self.label_rotation_x.setSizePolicy(sizePolicy)
        self.label_rotation_x.setMinimumSize(QtCore.QSize(120, 0))
        self.label_rotation_x.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_rotation_x.setObjectName("label_rotation_x")
        self.horizontalLayout_4.addWidget(self.label_rotation_x)

        self.lineEdit_rotation_x = QtWidgets.QLineEdit(self.tab)
        self.lineEdit_rotation_x.setInputMask("")
        self.lineEdit_rotation_x.setObjectName("lineEdit_rotation_x")
        self.horizontalLayout_4.addWidget(self.lineEdit_rotation_x)

        self.label_rotation_y = QtWidgets.QLabel(self.tab)
        self.label_rotation_y.setSizePolicy(sizePolicy)
        self.label_rotation_y.setMinimumSize(QtCore.QSize(120, 0))
        self.label_rotation_y.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_rotation_y.setObjectName("label_rotation_y")
        self.horizontalLayout_4.addWidget(self.label_rotation_y)

        self.lineEdit_rotation_y = QtWidgets.QLineEdit(self.tab)
        self.lineEdit_rotation_y.setInputMask("")
        self.lineEdit_rotation_y.setObjectName("lineEdit_rotation_y")
        self.horizontalLayout_4.addWidget(self.lineEdit_rotation_y)

        self.label_rotation_z = QtWidgets.QLabel(self.tab)
        self.label_rotation_z.setSizePolicy(sizePolicy)
        self.label_rotation_z.setMinimumSize(QtCore.QSize(120, 0))
        self.label_rotation_z.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_rotation_z.setObjectName("label_rotation_z")
        self.horizontalLayout_4.addWidget(self.label_rotation_z)

        self.lineEdit_rotation_z = QtWidgets.QLineEdit(self.tab)
        self.lineEdit_rotation_z.setInputMask("")
        self.lineEdit_rotation_z.setObjectName("lineEdit_rotation_z")
        self.horizontalLayout_4.addWidget(self.lineEdit_rotation_z)

        self.horizontalLayout_last = QtWidgets.QHBoxLayout()
        self.horizontalLayout_last.setObjectName("horizontalLayout_last")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_last.addItem(spacerItem1)
        self.pushButton_assemble = QtWidgets.QPushButton(self.tab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_assemble.sizePolicy().hasHeightForWidth())
        self.pushButton_assemble.setSizePolicy(sizePolicy)
        self.pushButton_assemble.setMinimumSize(QtCore.QSize(98, 50))
        self.pushButton_assemble.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.pushButton_assemble.setObjectName("run")
        self.horizontalLayout_last.addWidget(self.pushButton_assemble)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_last.addItem(spacerItem2)

        self.gridLayout_run_tab_1 = QtWidgets.QGridLayout(self.tab)

        self.gridLayout_run_tab_1.addLayout(self.horizontalLayout_1, 0, 0, 1, 1)
        self.gridLayout_run_tab_1.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)
        self.gridLayout_run_tab_1.addLayout(self.horizontalLayout_4, 2, 0, 1, 1)
        self.gridLayout_run_tab_1.addLayout(self.horizontalLayout_3, 3, 0, 1, 1)

        self.spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_run_tab_1.addItem(self.spacerItem3, 4, 0, 1, 1)

        self.gridLayout_run_tab_1.addLayout(self.horizontalLayout_last, 5, 0, 1, 1)
    
    def retranslateUi_tab1(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Form", "Form"))
        
        self.label_expand_result_folder.setText(_translate("Form", "Expand Result Folder:"))
        self.label_expand_result_folder.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            </span></p></body></html>"))
        
        self.lineEdit_expand_result_folder.setPlaceholderText(_translate("Form", "Expand/result_xxx"))
        self.lineEdit_expand_result_folder.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">The folder path store all the Expand results:TomoName_final folders\
            </span></p></body></html>"))
        
        self.label_assemble_output_folder.setText(_translate("Form", "Output Folder Name:"))
        self.label_assemble_output_folder.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            </span></p></body></html>"))
        
        self.lineEdit_assemble_output_folder.setPlaceholderText(_translate("Form", "assemble_01"))
        self.lineEdit_assemble_output_folder.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">The output folder name for assemble results. User customized.\
            </span></p></body></html>"))
        
        self.label_bin_factor.setText(_translate("Form", "Bin factor:"))
        self.label_bin_factor.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            </span></p></body></html>"))
        
        self.lineEdit_bin_factor.setPlaceholderText(_translate("Form", "1"))
        self.lineEdit_bin_factor.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">The binning factor for the tomogram used for picking. \
                The Relion particle.star file store no binned coords info.\
            </span></p></body></html>"))
        
        self.label_recenter.setText(_translate("Form", "Re-center shifts (pixel) on"))
        self.label_recenter.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\"\
                font-size:9pt;\"> In the average/reference, \
                use the new center's coords minus density map center.\
                For example (48,54,48) - (48,48,48) = 0,6,0\
            </span></p></body></html>"))
        
        self.label_recenter_x.setText(_translate("Form", "X-axis:"))
        self.label_recenter_x.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            </span></p></body></html>"))
        
        self.lineEdit_recenter_x.setPlaceholderText(_translate("Form", "0"))
        self.lineEdit_recenter_x.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">Recenter Shifts on X-axis after rotation.\
            </span></p></body></html>"))
        
        self.label_recenter_y.setText(_translate("Form", "Y-axis:"))
        self.label_recenter_y.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            </span></p></body></html>"))
        
        self.lineEdit_recenter_y.setPlaceholderText(_translate("Form", "0"))
        self.lineEdit_recenter_y.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">Recenter Shifts on Y-axis after rotation.\
            </span></p></body></html>"))
        
        self.label_recenter_z.setText(_translate("Form", "Z-axis:"))
        self.label_recenter_z.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            </span></p></body></html>"))
        
        self.lineEdit_recenter_z.setPlaceholderText(_translate("Form", "0"))
        self.lineEdit_recenter_z.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">Recenter Shifts on Z-axis after rotation.\
            </span></p></body></html>"))
        
        self.label_rotation.setText(_translate("Form", "Rotation (degree) apply on "))
        self.label_rotation.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\"\
                font-size:9pt;\"> In 3dmod, use slicer view to rotate on X and/or Y and/or Z to get the expected orientation. Use the value showed in the slicer view for each axis.\
            This is essential if you want to apply symmetry reconstruction later: aligning the symmetry axis to new Z-axis. And try the parameter with \
            rotatevol command in PEET to see if the rotation is expected before Relion refinement.\
            </span></p></body></html>"))
        
        self.label_rotation_x.setText(_translate("Form", "X-axis:"))
        self.label_rotation_x.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            </span></p></body></html>"))
        
        self.lineEdit_rotation_x.setPlaceholderText(_translate("Form", "0"))
        self.lineEdit_rotation_x.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">rotation apply on X-axis.\
            </span></p></body></html>"))
        
        self.label_rotation_y.setText(_translate("Form", "Y-axis:"))
        self.label_rotation_y.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            </span></p></body></html>"))
        
        self.lineEdit_rotation_y.setPlaceholderText(_translate("Form", "0"))
        self.lineEdit_rotation_y.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">rotation apply on Y-axis.\
            </span></p></body></html>"))
        
        self.label_rotation_z.setText(_translate("Form", "Z-axis:"))
        self.label_rotation_z.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            </span></p></body></html>"))
        
        self.lineEdit_rotation_z.setPlaceholderText(_translate("Form", "0"))
        self.lineEdit_rotation_z.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">rotation apply on Z-axis.\
            </span></p></body></html>"))
        
        
        self.pushButton_assemble.setText(_translate("Form", "RUN"))

    def setUI_tab2(self):
        self.tab2 = QtWidgets.QWidget()
        self.tab2.setObjectName("tab")

        self.horizontalLayout_2_1 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2_1.setContentsMargins(10, 5, 10, 5)

        self.label_data_star_file = QtWidgets.QLabel(self.tab2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_data_star_file.sizePolicy().hasHeightForWidth())
        self.label_data_star_file.setSizePolicy(sizePolicy)
        self.label_data_star_file.setMinimumSize(QtCore.QSize(120, 0))
        self.label_data_star_file.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_data_star_file.setObjectName("label_data_star_file")
        self.horizontalLayout_2_1.addWidget(self.label_data_star_file)

        self.lineEdit_data_star_file = QtWidgets.QLineEdit(self.tab2)
        self.lineEdit_data_star_file.setInputMask("")
        self.lineEdit_data_star_file.setObjectName("lineEdit_data_star_file")
        self.horizontalLayout_2_1.addWidget(self.lineEdit_data_star_file)

        self.pushButton_data_star_file = QtWidgets.QPushButton(self.tab2)
        self.pushButton_data_star_file.setText("")
        self.pushButton_data_star_file.setIcon(self.icon)
        self.pushButton_data_star_file.setIconSize(QtCore.QSize(24, 24))
        self.pushButton_data_star_file.setMaximumSize(QtCore.QSize(160, 24))
        self.pushButton_data_star_file.setMinimumSize(QtCore.QSize(60, 24))
        self.pushButton_data_star_file.setObjectName("pushButton_data_star_file")
        self.horizontalLayout_2_1.addWidget(self.pushButton_data_star_file)

        self.horizontalLayout_2_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2_2.setContentsMargins(10, 5, 10, 5)

        self.label_fitin_map_file = QtWidgets.QLabel(self.tab2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_fitin_map_file.sizePolicy().hasHeightForWidth())
        self.label_fitin_map_file.setSizePolicy(sizePolicy)
        self.label_fitin_map_file.setMinimumSize(QtCore.QSize(120, 0))
        self.label_fitin_map_file.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_fitin_map_file.setObjectName("label_fitin_map_file")
        self.horizontalLayout_2_2.addWidget(self.label_fitin_map_file)

        self.lineEdit_fitin_map_file = QtWidgets.QLineEdit(self.tab2)
        self.lineEdit_fitin_map_file.setInputMask("")
        self.lineEdit_fitin_map_file.setObjectName("lineEdit_fitin_map_file")
        self.horizontalLayout_2_2.addWidget(self.lineEdit_fitin_map_file)

        self.pushButton_fitin_map_file = QtWidgets.QPushButton(self.tab2)
        self.pushButton_fitin_map_file.setText("")
        self.pushButton_fitin_map_file.setIcon(self.icon)
        self.pushButton_fitin_map_file.setIconSize(QtCore.QSize(24, 24))
        self.pushButton_fitin_map_file.setMaximumSize(QtCore.QSize(160, 24))
        self.pushButton_fitin_map_file.setMinimumSize(QtCore.QSize(60, 24))
        self.pushButton_fitin_map_file.setObjectName("pushButton_fitin_map_file")
        self.horizontalLayout_2_2.addWidget(self.pushButton_fitin_map_file)
        
        self.horizontalLayout_2_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2_3.setContentsMargins(10, 5, 10, 5)

        self.label_tomo_name = QtWidgets.QLabel(self.tab2)
        self.label_tomo_name.setSizePolicy(sizePolicy)
        self.label_tomo_name.setMinimumSize(QtCore.QSize(130, 0))
        self.label_tomo_name.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_tomo_name.setObjectName("label_tomo_name")
        self.horizontalLayout_2_3.addWidget(self.label_tomo_name)

        self.lineEdit_tomo_name = QtWidgets.QLineEdit(self.tab2)
        self.lineEdit_tomo_name.setInputMask("")
        self.lineEdit_tomo_name.setObjectName("lineEdit_tomo_name")
        self.horizontalLayout_2_3.addWidget(self.lineEdit_tomo_name)

        self.label_pixel_size_unbinned = QtWidgets.QLabel(self.tab2)
        self.label_pixel_size_unbinned.setSizePolicy(sizePolicy)
        self.label_pixel_size_unbinned.setMinimumSize(QtCore.QSize(150, 0))
        self.label_pixel_size_unbinned.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_pixel_size_unbinned.setObjectName("label_pixel_size_unbinned")
        self.horizontalLayout_2_3.addWidget(self.label_pixel_size_unbinned)

        self.lineEdit_pixel_size_unbinned = QtWidgets.QLineEdit(self.tab2)
        self.lineEdit_pixel_size_unbinned.setInputMask("")
        self.lineEdit_pixel_size_unbinned.setObjectName("lineEdit_pixel_size_unbinned")
        self.horizontalLayout_2_3.addWidget(self.lineEdit_pixel_size_unbinned)

        self.label_pixel_size_fitin_map = QtWidgets.QLabel(self.tab2)
        self.label_pixel_size_fitin_map.setSizePolicy(sizePolicy)
        self.label_pixel_size_fitin_map.setMinimumSize(QtCore.QSize(150, 0))
        self.label_pixel_size_fitin_map.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_pixel_size_fitin_map.setObjectName("label_pixel_size_fitin_map")
        self.horizontalLayout_2_3.addWidget(self.label_pixel_size_fitin_map)

        self.lineEdit_pixel_size_fitin_map = QtWidgets.QLineEdit(self.tab2)
        self.lineEdit_pixel_size_fitin_map.setInputMask("")
        self.lineEdit_pixel_size_fitin_map.setObjectName("lineEdit_pixel_size_fitin_map")
        self.horizontalLayout_2_3.addWidget(self.lineEdit_pixel_size_fitin_map)

        self.label_unit_size_cxs = QtWidgets.QLabel(self.tab2)
        self.label_unit_size_cxs.setSizePolicy(sizePolicy)
        self.label_unit_size_cxs.setMinimumSize(QtCore.QSize(150, 0))
        self.label_unit_size_cxs.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_unit_size_cxs.setObjectName("label_unit_size_cxs")
        self.horizontalLayout_2_3.addWidget(self.label_unit_size_cxs)

        self.lineEdit_unit_size_cxs = QtWidgets.QLineEdit(self.tab2)
        self.lineEdit_unit_size_cxs.setInputMask("")
        self.lineEdit_unit_size_cxs.setObjectName("lineEdit_unit_size_cxs")
        self.horizontalLayout_2_3.addWidget(self.lineEdit_unit_size_cxs)
 
        # the last H layout
        self.horizontalLayout_last_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_last_2.setObjectName("horizontalLayout_last_2")
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_last_2.addItem(spacerItem4)
        self.pushButton_place_back = QtWidgets.QPushButton(self.tab2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_place_back.sizePolicy().hasHeightForWidth())
        self.pushButton_place_back.setSizePolicy(sizePolicy)
        self.pushButton_place_back.setMinimumSize(QtCore.QSize(98, 50))
        self.pushButton_place_back.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.pushButton_place_back.setObjectName("run")
        self.horizontalLayout_last_2.addWidget(self.pushButton_place_back)
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_last_2.addItem(spacerItem5)
        
        
        self.gridLayout_pick_params = QtWidgets.QGridLayout(self.tab2)

        self.gridLayout_pick_params.addLayout(self.horizontalLayout_2_1, 0, 0, 1, 1)
        self.gridLayout_pick_params.addLayout(self.horizontalLayout_2_2, 1, 0, 1, 1)
        self.gridLayout_pick_params.addLayout(self.horizontalLayout_2_3, 2, 0, 1, 1)


        self.spacerItem6 = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_pick_params.addItem(self.spacerItem6, 3, 0, 1, 1)

        self.gridLayout_pick_params.addLayout(self.horizontalLayout_last_2, 4, 0, 1, 1)
    
    def retranslateUi_tab2(self):
        _translate = QtCore.QCoreApplication.translate
        
        self.label_data_star_file.setText(_translate("Form", "Particles star file:"))
        self.label_data_star_file.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\""))
        
        self.lineEdit_data_star_file.setPlaceholderText(_translate("Form", ""))
        self.lineEdit_data_star_file.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">The input data.star file from refinement result of Relion. </span></p></body></html>"))
        
        self.label_fitin_map_file.setText(_translate("Form", "Average density map:"))
        self.label_fitin_map_file.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\""))
        
        self.lineEdit_fitin_map_file.setPlaceholderText(_translate("Form", ""))
        self.lineEdit_fitin_map_file.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">The average density map or simplified model for your sub-tomogram to be place back to the raw tomogram.</span></p></body></html>"))
        
        self.label_tomo_name.setText(_translate("Form", "Tomogram name:"))
        self.label_tomo_name.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\""))
        
        self.lineEdit_tomo_name.setPlaceholderText(_translate("Form", ""))
        self.lineEdit_tomo_name.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">The target tomogram name.</span></p></body></html>"))
        
        self.label_pixel_size_unbinned.setText(_translate("Form", "Unbinned pixel size:"))
        self.label_pixel_size_unbinned.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\""))
        
        self.lineEdit_pixel_size_unbinned.setPlaceholderText(_translate("Form", ""))
        self.lineEdit_pixel_size_unbinned.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">The unbinned pixel size.</span></p></body></html>"))
        
        self.label_pixel_size_fitin_map.setText(_translate("Form", "Fitin map pixel size:"))
        self.label_pixel_size_fitin_map.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\""))
        
        self.lineEdit_pixel_size_fitin_map.setPlaceholderText(_translate("Form", ""))
        self.lineEdit_pixel_size_fitin_map.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">average density map's pixel size or target pixel size </span></p></body></html>"))
        
        self.label_unit_size_cxs.setText(_translate("Form", "Repeating Unit (Å):"))
        self.label_unit_size_cxs.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\""))
        
        self.lineEdit_unit_size_cxs.setPlaceholderText(_translate("Form", ""))
        self.lineEdit_unit_size_cxs.setToolTip(_translate("MainWindow", \
            "<html><head/><body><p><span style=\" \
            font-size:9pt;\">Distance between two repeating unit.</span></p></body></html>"))

        self.pushButton_place_back.setText(_translate("Form", "RUN"))
          
    @QtCore.pyqtSlot(str)
    def update_log_window(self, txt):
        in_current_page = True
        for x in self.parentWidget().parentWidget().children():
            if x.objectName() == "listWidget":
                if not x.currentRow() == 6:
                    in_current_page = False
            elif x.objectName() == "log_window":
                if in_current_page:
                    self.log_window = x
                    self.log_window.setText(getLogContent(txt))
                    self.log_window.moveCursor(QtGui.QTextCursor.End)

                    custom_font = QtGui.QFont()
                    custom_font.setPointSize(11)
                    self.log_window.setCurrentFont(custom_font)


        # self.log_window = self.parentWidget().parentWidget().children()[3] 
        # self.log_window.setText(getLogContent(txt))
        # self.log_window.moveCursor(QtGui.QTextCursor.End)

        # custom_font = QtGui.QFont()
        # custom_font.setPointSize(11)
        # self.log_window.setCurrentFont(custom_font)

    def read_settting(self):
        if not os.path.exists(self.setting_file):
            try:
                f = open(self.setting_file)
            except:
                pass        
        data = {}
        data['expand_result_folder'] = ""
        data['assemble_output_folder'] = ""
        data['bin_factor'] = ""
        data['recenter_x'] = ""
        data['recenter_y'] = ""
        data['recenter_z'] = ""
        data['rotation_x'] = ""
        data['rotation_y'] = ""
        data['rotation_z'] = ""

        data['data_star_file'] =""
        data['fitin_map_file'] =""
        data['tomo_name'] =""
        data['pixel_size_unbinned'] =""
        data['pixel_size_fitin_map'] =""
        data['unit_size_cxs'] =""

        try:
            with open(self.setting_file) as f:
                for line in f:
                    (k, v) = line.split(":")
                    if v.strip() == "True":
                        data[k] = True
                    elif v.strip() == "False":
                        data[k] = False
                    else:
                        data[k] = v.strip()
        except:
            pass
        self.lineEdit_expand_result_folder.setText(data['expand_result_folder'])
        self.lineEdit_assemble_output_folder.setText(data['assemble_output_folder'])
        self.lineEdit_bin_factor.setText(data['bin_factor'])
        self.lineEdit_recenter_x.setText(data['recenter_x'])
        self.lineEdit_recenter_y.setText(data['recenter_y'])
        self.lineEdit_recenter_z.setText(data['recenter_z'])
        self.lineEdit_rotation_x.setText(data['rotation_x'])
        self.lineEdit_rotation_y.setText(data['rotation_y'])
        self.lineEdit_rotation_z.setText(data['rotation_z'])

        self.lineEdit_data_star_file.setText(data['data_star_file'])
        self.lineEdit_fitin_map_file.setText(data['fitin_map_file'])
        self.lineEdit_tomo_name.setText(data['tomo_name'])
        self.lineEdit_pixel_size_unbinned.setText(data['pixel_size_unbinned'])
        self.lineEdit_pixel_size_fitin_map.setText(data['pixel_size_fitin_map'])
        self.lineEdit_unit_size_cxs.setText(data['unit_size_cxs'])
          
    def save_setting(self):
        param = {}
        param['expand_result_folder'] = self.lineEdit_expand_result_folder.text()
        param['assemble_output_folder'] = self.lineEdit_assemble_output_folder.text()
        param['bin_factor'] = self.lineEdit_bin_factor.text()
        param['recenter_x'] = self.lineEdit_recenter_x.text()
        param['recenter_y'] = self.lineEdit_recenter_y.text()
        param['recenter_z'] = self.lineEdit_recenter_z.text()
        param['rotation_x'] = self.lineEdit_rotation_x.text()
        param['rotation_y'] = self.lineEdit_rotation_y.text()
        param['rotation_z'] = self.lineEdit_rotation_z.text()

        param['data_star_file'] = self.lineEdit_data_star_file.text()
        param['fitin_map_file'] = self.lineEdit_fitin_map_file.text()
        param['tomo_name'] = self.lineEdit_tomo_name.text()
        param['pixel_size_unbinned'] = self.lineEdit_pixel_size_unbinned.text()
        param['pixel_size_fitin_map'] = self.lineEdit_pixel_size_fitin_map.text()
        param['unit_size_cxs'] = self.lineEdit_unit_size_cxs.text()
        try:
            with open(self.setting_file, 'w') as f: 
                for key, value in param.items(): 
                    f.write("{}:{}\n".format(key,value))
        except:
            print("error writing {}!".format(self.setting_file))     
    
    def get_assemble_params(self):
        
        if not len(self.lineEdit_expand_result_folder.text()) > 0:
            return "Please specify the expand result folder!"
        else:
            expand_result_folder = self.lineEdit_expand_result_folder.text()

        if not len(self.lineEdit_assemble_output_folder.text()) > 0:
            return "Please specify the assemble result folder!"
        else:
            assemble_output_folder = "{}/{}".format(self.others_folder, self.lineEdit_assemble_output_folder.text())

        if len(self.lineEdit_bin_factor.text()) > 0:
            if not string2float(self.lineEdit_bin_factor.text()) == None:
                bin_factor = string2float(self.lineEdit_bin_factor.text())
            else:
                return "Please use the valid format for the bin factor!"
        else:
            bin_factor = 1

        if len(self.lineEdit_recenter_x.text()) > 0:
            if not string2float(self.lineEdit_recenter_x.text()) == None:
                recenter_x = string2float(self.lineEdit_recenter_x.text())
            else:
                return "Please use the valid format for the x shift!"
        else:
            recenter_x = 0
        
        if len(self.lineEdit_recenter_y.text()) > 0:
            if not string2float(self.lineEdit_recenter_y.text()) == None:
                recenter_y = string2float(self.lineEdit_recenter_y.text())
            else:
                return "Please use the valid format for the x shift!"
        else:
            recenter_y = 0
        
        if len(self.lineEdit_recenter_z.text()) > 0:
            if not string2float(self.lineEdit_recenter_z.text()) == None:
                recenter_z = string2float(self.lineEdit_recenter_z.text())
            else:
                return "Please use the valid format for the x shift!"
        else:
            recenter_z = 0

        if len(self.lineEdit_rotation_x.text()) > 0:
            if not string2float(self.lineEdit_rotation_x.text()) == None:
                rotation_x = string2float(self.lineEdit_rotation_x.text())
            else:
                return "Please use the valid format for the x shift!"
        else:
            rotation_x = 0
        
        if len(self.lineEdit_rotation_y.text()) > 0:
            if not string2float(self.lineEdit_rotation_y.text()) == None:
                rotation_y = string2float(self.lineEdit_rotation_y.text())
            else:
                return "Please use the valid format for the x shift!"
        else:
            rotation_y = 0
        
        if len(self.lineEdit_rotation_z.text()) > 0:
            if not string2float(self.lineEdit_rotation_z.text()) == None:
                rotation_z = string2float(self.lineEdit_rotation_z.text())
            else:
                return "Please use the valid format for the x shift!"
        else:
            rotation_z = 0
                
        if not os.path.exists(assemble_output_folder):
            mkfolder(assemble_output_folder)

        params = {}
        params['expand_result_folder'] = expand_result_folder
        params['assemble_output_folder'] = assemble_output_folder
        params['bin_factor'] = bin_factor
        params['recenter_x'] = recenter_x
        params['recenter_y'] = recenter_y
        params['recenter_z'] = recenter_z
        params['rotation_x'] = rotation_x
        params['rotation_y'] = rotation_y
        params['rotation_z'] = rotation_z

        return params
    
    def get_final_folder_list(self, folder):
        final_folder_list = [os.path.basename(x).split(".")[0] for x in sorted(glob.glob("{}/*_final".format(folder)))]
        tomo_list = [x.split("_final")[0] for x in final_folder_list]
        
        return tomo_list

    def transform_coords_euler(self, tomo, origin_coords_file, origin_motl_file, output_coords_file, output_euler_file, shifts, rotation):
        with open(origin_coords_file, 'r') as f:
            origin_coords_lines = np.array([ x.split() for x in f.readlines()])
        #print(origin_coords_lines.shape)
        random_euler = False
        if os.path.exists(origin_motl_file):
            with open(origin_motl_file, 'r') as f:
                origin_motl_lines = np.array([ x.split(',') for x in f.readlines()][1:])
        else:
            random_euler = True
            self.logger.warning("MOTL.csv file is not detected for tomogram {}, use random euler angles instead!".format(tomo))

        if len(origin_coords_lines) <=0 or origin_coords_lines.shape[1] <3 or origin_coords_lines.shape[1] >4:
            self.logger.warning(".pts file format is wrong for tomogram {}, skip it!".format(tomo))
        else:
            with open(output_coords_file, 'w') as w_c:
                with open(output_euler_file, 'w') as w_e:
                    
                    for i, line in enumerate(origin_coords_lines):
                        if not random_euler:
                            zxz_euler = np.array([float(origin_motl_lines[i][16]),float(origin_motl_lines[i][18]),float(origin_motl_lines[i][17])])
                        else:
                            zxz_euler = np.random.rand(3,) * 360-180
                        real_shifts = get_raw_shifts_PEET(zxz_euler, shifts)

                        if origin_coords_lines.shape[1] ==4:
                            pid = line[0]
                            new_coords = np.array([float(v) for v in line[1:]]) + real_shifts
                        else:
                            pid = 1
                            new_coords = np.array([float(v) for v in line]) + real_shifts
                        
                        new_coords_line = "{} {} {} {}\n".format(pid, round(new_coords[0],2), round(new_coords[1],2), round(new_coords[2],2))
                        w_c.write(new_coords_line)
                        
                        new_zxz_euler = apply_slicerRot_PEET(zxz_euler, rotation)
                        zyz_euler = PEET2Relion(new_zxz_euler)
                        new_euler_line = "{},{},{}\n".format(round(zyz_euler[0],2), round(zyz_euler[1],2), round(zyz_euler[2],2))
                        w_e.write(new_euler_line)

        self.logger.info("coords and euler files are generated for {}!".format(tomo))

    def combine_all(self, tomo_list, folder, bin_factor=1):
        out_file = "{}/particles.star".format(folder)
        with open(out_file,"w") as f:
            header ="{}\n\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n".format(\
            "data_particles",\
            "loop_",\
            "_rlnTomoName #1",\
            "_rlnTomoParticleId #2",\
            "_rlnTomoManifoldIndex #3",\
            "_rlnCoordinateX #4",\
            "_rlnCoordinateY #5",\
            "_rlnCoordinateZ #6",\
            "_rlnOriginXAngst #7",\
            "_rlnOriginYAngst #8",\
            "_rlnOriginZAngst #9",\
            "_rlnAngleRot #10",\
            "_rlnAngleTilt #11",\
            "_rlnAnglePsi #12",\
            "_rlnClassNumber #13",\
            "_rlnRandomSubset #14")
            f.write(header)
            particle_index = 1
            #tomo_index = 1
            manifold_id = 0
            for tomo in tomo_list:
                #print(coords)
                #tomo_name = coords.split(".")[0]
                #coord_file=open(coords)
                pid = -1
                coords_file = "{}/{}.coords".format(folder,tomo)
                try:
                    with open(coords_file,'r') as r:
                        coords_data=r.readlines()
                    euler_file = "{}/{}.euler".format(folder,tomo)
                    with open(euler_file,'r') as r:
                        euler_data=r.readlines()
                    for i in range(0, len(coords_data)):
                        
                        pair_euler = [float(x) for x in euler_data[i].strip().split(',')]
                        pair_coords = [float(x) for x in coords_data[i].strip().split()]
                        pid_now = int(pair_coords[0])
                        if pid_now > pid:
                            manifold_id +=1
                            pid = pid_now
                        line = "{} {} {} {} {} {} {} {} {} {} {} {} {} {} \n".format(tomo, particle_index, manifold_id, \
                                pair_coords[1]*bin_factor, pair_coords[2]*bin_factor, pair_coords[3]*bin_factor, \
                                0, 0, 0,\
                                pair_euler[0], pair_euler[1], pair_euler[2], \
                                1, particle_index%2+1)
                        f.write(line)
                        particle_index +=1
                except:
                    self.logger.warning("{} has invalid final result, skip it!".format(tomo))
    def assemble(self):
        params = self.get_assemble_params()
        #print(params)
        if type(params) is str:
            self.logger.error(params)
        elif type(params) is dict:
            ret = QMessageBox.question(self, 'Reformatting!', \
                    "Continue?\n"\
                    , QMessageBox.Yes | QMessageBox.No, \
                    QMessageBox.No)
                
            if ret == QMessageBox.Yes:
                self.pushButton_assemble.setText("STOP")
                self.pushButton_assemble.setStyleSheet('QPushButton {color: red;}')
                self.logger.info("Start transform!")
                tomo_list = self.get_final_folder_list(params['expand_result_folder'])

                # rotations = "{},{},{}".format(-1*params['rotation_x'],-1*params['rotation_y'],-1*params['rotation_z'])
                # shifts = "{},{},{}".format(-1*params['recenter_x'], -1*params['recenter_y'], -1*params['recenter_z'])
                rotations = [params['rotation_x'],params['rotation_y'],params['rotation_z']]
                shifts = [params['recenter_x'], params['recenter_y'], params['recenter_z']]
                for tomo in tomo_list:
                    pts_file = "{}/{}_final/{}.pts".format(params['expand_result_folder'], tomo, tomo)
                    motl_file = "{}/{}_final/{}_MOTL.csv".format(params['expand_result_folder'], tomo, tomo)
                    #motl_convert_file = "{}/{}_final/{}_convert_MOTL.csv".format(params['assemble_output_folder'], tomo, tomo)

                    coords_file = "{}/{}.coords".format(params['assemble_output_folder'], tomo)
                    euler_file = "{}/{}.euler".format(params['assemble_output_folder'], tomo)
                    
                    if os.path.exists(pts_file):
                        self.transform_coords_euler(tomo, pts_file, motl_file, coords_file, euler_file, shifts, rotations)
                    else:
                        self.logger.warning(".pts (coords) file {} is missing for tomogram {}, skip it!".format(pts_file, tomo))
                        continue
                self.combine_all(tomo_list, params['assemble_output_folder'], params["bin_factor"])
                self.logger.info("Done transform!")
                
                self.cmd_finished(self.pushButton_assemble)

    def get_placeback_params(self):
        if not len(self.lineEdit_data_star_file.text()) > 0:
            return "Please provide the data star file!"
        else:
            data_star_file = self.lineEdit_data_star_file.text()

        if not len(self.lineEdit_fitin_map_file.text()) > 0:
            return "Please provide the the fitin map!"
        else:
            fitin_map_file = self.lineEdit_fitin_map_file.text()

        if not len(self.lineEdit_tomo_name.text()) > 0:
            return "Please provide the tomogram name!"
        else:
            tomo_name = self.lineEdit_tomo_name.text()

        if len(self.lineEdit_pixel_size_unbinned.text()) > 0:
            if not string2float(self.lineEdit_pixel_size_unbinned.text()) == None:
                pixel_size_unbinned = string2float(self.lineEdit_pixel_size_unbinned.text())
            else:
                return "Please use the valid format for the unbinned pixel size!"
        else:
            return "Please provide the unbinned pixel size!"
        
        if len(self.lineEdit_pixel_size_fitin_map.text()) > 0:
            if not string2float(self.lineEdit_pixel_size_fitin_map.text()) == None:
                pixel_size_fitin_map = string2float(self.lineEdit_pixel_size_fitin_map.text())
            else:
                return "Please use the valid format for the unbinned pixel size!"
        else:
            return "Please provide the unbinned pixel size!"
        
        if len(self.lineEdit_unit_size_cxs.text()) > 0:
            if not string2float(self.lineEdit_unit_size_cxs.text()) == None:
                unit_size_cxs = string2float(self.lineEdit_unit_size_cxs.text())
            else:
                return "Please use the valid format for the repeating unit!"
        else:
            unit_size_cxs = 10000.0

        params = {}
        params['result_folder'] = "{}/placeback_result".format(self.others_folder)
        params['data_star_file'] = data_star_file
        params['fitin_map_file'] = fitin_map_file
        params['tomo_name'] = tomo_name
        params['pixel_size_unbinned'] = pixel_size_unbinned
        params['pixel_size_fitin_map'] = pixel_size_fitin_map
        params['unit_size_cxs'] = unit_size_cxs
        
        
        return params
    
    def generate_cxs_file(self, params):
        #self.logger.info(params)

        star_file = params['data_star_file']
        tomo_name = params['tomo_name']
        average_map = params['fitin_map_file']
        output_file_name = "{}/placeback_tomo_{}.cxc".format(self.others_folder, tomo_name)
        clean_version_star = "{}/clean_tomo_{}.star".format(self.others_folder, tomo_name)
        bin_factor = params['pixel_size_fitin_map']/params['pixel_size_unbinned']
        
        with mrcfile.open(average_map) as mrcData:
            orig_data = mrcData.data.astype(np.float32)

        map_dimension = orig_data.shape

        dis_unit = params['unit_size_cxs']
        dis_ratio = 1.2

        apix = params['pixel_size_unbinned']

        df_particles = starfile.read(star_file,  always_dict=True)['particles']
        df_particles = df_particles.loc[df_particles['rlnTomoName']==tomo_name]
        df_particles = df_particles.reset_index()
        pNum = df_particles.shape[0]


        manifoldIndex_start = df_particles['rlnTomoManifoldIndex'].astype(int).min()
        #print(manifoldIndex_start)
        manifold_num = df_particles['rlnTomoManifoldIndex'].astype(int).max() - manifoldIndex_start + 1
        #print(manifold_num)
        try:
            shutil.copy(average_map, self.others_folder)
        except:
            pass
        
        global_id = 0
        real_patch_num = 0
        clean_i = 0
        average_map_basename = os.path.basename(average_map)
        if not manifold_num or math.isnan(manifold_num):
            self.logger.warning("No Tomo Name: {}.".format(tomo_name))
            return 0
        else:
            with open(output_file_name, "w") as outfile:
                with open(clean_version_star, "w") as c_star_file:
                    
                    for i in range(int(manifold_num)):
                        current_manifold_id = manifoldIndex_start+i
                        manifold_df = df_particles.loc[df_particles['rlnTomoManifoldIndex']==current_manifold_id]
                        manifold_df = manifold_df.reset_index()
                        pNum_i = manifold_df.shape[0]
                        if pNum_i > 0:
                            real_patch_num+=1
                            global_id+=pNum_i
                            
                            open_line = "open"
                            move_cmds = ""
                            turn_cmds = ""

                            centers = []
                            new_vectors = []

                            for j in range(pNum_i):
                                
                                xp, yp, zp = [manifold_df['rlnCoordinateX'][j], manifold_df['rlnCoordinateY'][j], manifold_df['rlnCoordinateZ'][j]]
                                xt, yt, zt = [manifold_df['rlnOriginXAngst'][j], manifold_df['rlnOriginYAngst'][j], manifold_df['rlnOriginZAngst'][j]]
                                rot, tilt, psi = [manifold_df['rlnAngleRot'][j], manifold_df['rlnAngleTilt'][j], manifold_df['rlnAnglePsi'][j]]
                                
                                output_eulers, output_vector = Relion2ChimeraX(np.array([rot, tilt, psi]))

                                x = round(xp*apix + xt,3)
                                y = round(yp*apix + yt,3)
                                z = round(zp*apix + zt,3)

                                centers.append([x,y,z])
                                new_vectors.append([output_vector[0],output_vector[1],output_vector[2]])

                                if pNum_i == 1:
                                    model_id = "{}".format(real_patch_num, j+1)
                                else:
                                    model_id = "{}.{}".format(real_patch_num, j+1)
                                
                                open_line = "{} {}".format(open_line, average_map_basename)

                                move_cmds = "{}move x {} models #{}; move y {} models #{}; move z {} models #{};\n"\
                                            .format(move_cmds, x, model_id, y, model_id, z, model_id)
                                
                                turn_cmds = "{}turn z {} center 0,0,0 models #{} coordinateSystem #{}; turn y {} center 0,0,0 models #{} coordinateSystem #{}; turn z {} center 0,0,0  models #{} coordinateSystem #{};\n"\
                                            .format(turn_cmds, output_eulers[0], model_id, model_id, output_eulers[1], model_id, model_id, \
                                                output_eulers[2], model_id, model_id)

                            mat_coords = np.array(distance_matrix(centers, centers))
                            mat_norm = squareform(pdist(new_vectors, "cosine"))
                            
                            color_cmds = ""

                            for j in range(pNum_i):
                                neignbors = getNeighbors(mat_coords[j], j, dis_unit*dis_ratio)
                                sum = 0
                                avg_angle = 0
                                for n in neignbors:		
                                    sum += math.acos(1-mat_norm[j][n])/math.pi*180
                                if len(neignbors) > 0:
                                    avg_angle =  sum/len(neignbors) 
                                r,g,b = getRGBs(avg_angle, max_angle=30)
                                
                                if len(neignbors) > 1 and avg_angle <= 30:
                                    c_star_line = " ".join([str(x) for x in manifold_df.loc[j].values.flatten().tolist()][2:]) + "\n"
                                    c_star_file.write(c_star_line)
                                    clean_i+=1
                                if pNum_i == 1:
                                    model_id = "{}".format(real_patch_num, j+1)
                                else:
                                    model_id = "{}.{}".format(real_patch_num, j+1)

                                color_cmds = "{}color #{} rgb({},{},{});\n".format(color_cmds, model_id, r, g, b)

                            recenter_line = "vop #{} originIndex {},{},{};\n".format(real_patch_num, map_dimension[2]/2, map_dimension[1]/2, map_dimension[0]/2)
                            
                            outfile.write(open_line+";\n\n")
                            outfile.write(recenter_line+"\n")
                            outfile.write(move_cmds+"\n")
                            outfile.write(turn_cmds+"\n")
                            outfile.write(color_cmds+"\n")

                outfile.write("view\n")  

            self.logger.info("Original: {}; Clean version: {}.".format(global_id, clean_i))
            return 1
    
    def placeback(self):
        params = self.get_placeback_params()
        if type(params) is str:
            self.logger.error(params)
        elif type(params) is dict:
            ret = QMessageBox.question(self, 'Get placeback ChimeraX session!', \
                    "Continue?\n"\
                    , QMessageBox.Yes | QMessageBox.No, \
                    QMessageBox.No)   
            if ret == QMessageBox.Yes:
                self.pushButton_place_back.setText("STOP")
                self.pushButton_place_back.setStyleSheet('QPushButton {color: red;}')
                
                result = self.generate_cxs_file(params)

                if result == 1:
                    self.logger.info("Done getting placeback session file for ChimeraX: {}!".format(params['tomo_name']))
                
                self.cmd_finished(self.pushButton_place_back)
    
    def cmd_finished(self, button, text="RUN"):
        button.setText(text)
        button.setStyleSheet("QPushButton {color: black;}")
