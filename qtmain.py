'''
Created on Feb 1, 2018

@author: skydeo

Qt GUI main for renamer.py
Heavily borrowed from Brian Grivna's work on the rgbaggregator at https://github.com/sorghumking/rgbaggregator
'''

import os
import sys

from PyQt5 import QtWidgets

import renamer

class RenamerWindow(QtWidgets.QWidget):
    def __init__(self, app):
        self.app = app
        self.lastFileDialogPath = os.path.expanduser("~/PyRename/")
        QtWidgets.QWidget.__init__(self)
        self.setWindowTitle("CSDCO/LacCore MSCL CoreID Applier {0}".format(renamer.version))
        
        self.inputPathText = LabeledLineText(self, "Input File")
        self.chooseInputFileButton = QtWidgets.QPushButton("...", self)
        self.chooseInputFileButton.clicked.connect(self.chooseInputFile)
        self.coreListPathText = LabeledLineText(self, "Core List File")
        self.chooseCoreListFileButton = QtWidgets.QPushButton("...", self)
        self.chooseCoreListFileButton.clicked.connect(self.chooseCoreListFile)
        self.outputPathText = LabeledLineText(self, "Output File")
        self.chooseOutputFileButton = QtWidgets.QPushButton("...", self)
        self.chooseOutputFileButton.clicked.connect(self.chooseOutputFile)
        
        vlayout = QtWidgets.QVBoxLayout(self)
        inputLayout = self.makeFileLayout(self.inputPathText, self.chooseInputFileButton, "Combined MSCL file that has section numbers and needs CoreIDs applied.")
        vlayout.addLayout(inputLayout)
        coreListLayout = self.makeFileLayout(self.coreListPathText, self.chooseCoreListFileButton, "Core list in the formation sectionNum,CoreID")
        vlayout.addLayout(coreListLayout)
        outputlayout = self.makeFileLayout(self.outputPathText, self.chooseOutputFileButton, "File to which all section RGB data will be written.")
        vlayout.addLayout(outputlayout)
        
        # header row
        headerLayout = QtWidgets.QHBoxLayout()
        self.headerRowCheckbox = QtWidgets.QCheckBox(self)
        headerLayout.addWidget(self.headerRowCheckbox)        
        self.headerRowCheckbox.clicked.connect(self.headerRowChecked)
        self.headerRowLabel1 = QtWidgets.QLabel("Header row:")
        headerLayout.addWidget(self.headerRowLabel1)
        self.headerRowText = QtWidgets.QLineEdit(self)
        self.headerRowText.setMaximumWidth(25)
        self.headerRowText.setText('1')
        headerLayout.addWidget(self.headerRowText)
        self.headerRowChecked() # disable controls to match checkbox state
        headerLayout.addStretch(1) # push widgets to left
        vlayout.addLayout(headerLayout)

        # unit row
        unitLayout = QtWidgets.QHBoxLayout()
        self.unitRowCheckbox = QtWidgets.QCheckBox(self)
        unitLayout.addWidget(self.unitRowCheckbox)        
        self.unitRowCheckbox.clicked.connect(self.unitRowChecked)
        self.unitRowLabel1 = QtWidgets.QLabel("Unit row:")
        unitLayout.addWidget(self.unitRowLabel1)
        self.unitRowText = QtWidgets.QLineEdit(self)
        self.unitRowText.setMaximumWidth(25)
        self.unitRowText.setText('2')
        unitLayout.addWidget(self.unitRowText)
        self.unitRowChecked() # disable controls to match checkbox state
        unitLayout.addStretch(1) # push widgets to left
        vlayout.addLayout(unitLayout)

        # start row
        startLayout = QtWidgets.QHBoxLayout()
        self.startRowCheckbox = QtWidgets.QCheckBox(self)
        startLayout.addWidget(self.startRowCheckbox)        
        self.startRowCheckbox.clicked.connect(self.startRowChecked)
        self.startRowLabel1 = QtWidgets.QLabel("Start row:")
        startLayout.addWidget(self.startRowLabel1)
        self.startRowText = QtWidgets.QLineEdit(self)
        self.startRowText.setMaximumWidth(25)
        self.startRowText.setText('3')
        startLayout.addWidget(self.startRowText)
        self.startRowChecked() # disable controls to match checkbox state
        startLayout.addStretch(1) # push widgets to left
        vlayout.addLayout(startLayout)

        vlayout.addWidget(QtWidgets.QLabel("Log", self))
        self.logArea = QtWidgets.QTextEdit(self)
        self.logArea.setReadOnly(True)
        self.logArea.setToolTip("Renaming log.")
        vlayout.addWidget(self.logArea)
        
        self.renameButton = QtWidgets.QPushButton("Apply CoreIDs")
        self.renameButton.clicked.connect(self.rename)
        vlayout.addWidget(self.renameButton, stretch=1)

    def rename(self):
        inFile = self.inputPathText.text()
        if not os.path.isfile(inFile):
            self._warnbox("Badness", "Input file {0} does not exist".format(inputPathText))
            return

        coreListFile = self.coreListPathText.text()
        if not os.path.isfile(coreListFile):
            self._warnbox("Badness", "Core list file {0} does not exist".format(coreListFile))
            return

        outFile = self.outputPathText.text()
        if not os.path.exists(os.path.dirname(outFile)):
            self._warnbox("Badness", "Output file {0} does not exist".format(outputPathText))
            return
        
        unmatchedFile = '.'.join(outFile.split('.')[:-1]) + '_UNMATCHED.csv'
        if not os.path.exists(os.path.dirname(unmatchedFile)):
            self._warnbox("Badness", "Output file {0} does not exist".format(outputPathText))
            return

        headerRow = None
        if self.headerRowCheckbox.isChecked():
            try:
                headerRow = int(self.headerRowText.text())-1
            except ValueError:
                self._warnbox("Badness", "Header row must be an integer.")
                return
        else:
            headerRow = 0
            # if headerRow < 2:
                # self._warnbox("Badness", "Average Rows must be an integer > 1")
                # return

        unitRow = None
        if self.unitRowCheckbox.isChecked():
            try:
                unitRow = int(self.unitRowText.text())-1
            except ValueError:
                self._warnbox("Badness", "Unit row must be an integer.")
                return
        else:
            unitRow = 1
            # if unitRow < 2:
                # self._warnbox("Badness", "Average Rows must be an integer > 1")
                # return

        startRow = None
        if self.startRowCheckbox.isChecked():
            try:
                startRow = int(self.startRowText.text())-1
            except ValueError:
                self._warnbox("Badness", "Start row must be an integer.")
                return
        else:
            startRow = 2
            # if startRow < 2:
                # self._warnbox("Badness", "Average Rows must be an integer > 1")
                # return

        self.renameButton.setEnabled(False)
        # self.logArea.clear()
        try:
            renamer.apply_names(inFile, coreListFile, outputfilename=outFile, unmatchedfilename=unmatchedFile, headerrow=headerRow, unitrow=unitRow, startrow=startRow)
        except Exception as err:
            self.report("\nSUPER FATAL ERROR: " + str(err))
            print('infile: {}\ncoreListFile: {}\noutputfilename: {}\nunmatchedfilename: {}\nheaderrow: {}\nunitrow: {}\nstartrow: {}'.format(inFile, coreListFile, outFile, unmatchedFile, headerRow, unitRow, startRow))            
        self.renameButton.setEnabled(True)
        
    def report(self, text, newline=True):
        text += '\n' if newline else ''
        self.logArea.insertPlainText(text)
        self.app.processEvents() # force GUI update
        
    def _warnbox(self, title, message):
        QtWidgets.QMessageBox.warning(self, title, message)
        
    def chooseInputFile(self):
        dlg = QtWidgets.QFileDialog(self, "Choose input file", self.lastFileDialogPath)
        selectedFile, dummyFilter = dlg.getOpenFileName(self)
        if selectedFile != '':
            self.report("Selected input file {0}".format(selectedFile))
            self.inputPathText.setText(selectedFile)

    def chooseCoreListFile(self):
        dlg = QtWidgets.QFileDialog(self, "Choose core list file", self.lastFileDialogPath)
        selectedFile, dummyFilter = dlg.getOpenFileName(self)
        if selectedFile != '':
            self.report("Selected core list file {0}".format(selectedFile))
            self.coreListPathText.setText(selectedFile)
    
    def chooseOutputFile(self):
        dlg = QtWidgets.QFileDialog(self, "Choose output file", self.lastFileDialogPath)
        selectedFile, dummyFilter = dlg.getSaveFileName(self)
        if selectedFile != '':
            self.report("Selected output file {0}".format(selectedFile))
            self.outputPathText.setText(selectedFile)
            
    def headerRowChecked(self):
        checked = self.headerRowCheckbox.isChecked()
        self.headerRowText.setEnabled(checked)
        self.headerRowLabel1.setEnabled(checked)
    
    def unitRowChecked(self):
        checked = self.unitRowCheckbox.isChecked()
        self.unitRowText.setEnabled(checked)
        self.unitRowLabel1.setEnabled(checked)
    
    def startRowChecked(self):
        checked = self.startRowCheckbox.isChecked()
        self.startRowText.setEnabled(checked)
        self.startRowLabel1.setEnabled(checked)
    
    def makeDescLabel(self, desc):
        label = QtWidgets.QLabel(desc)
        label.setStyleSheet("QLabel {font-size: 11pt;}")
        return label
    
    # return layout with editText (includes label) and chooserButton on one line,
    # descText on the next with minimal vertical space between the two
    def makeFileLayout(self, editText, chooserButton, descText):
        layout = QtWidgets.QVBoxLayout()
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(editText)
        hlayout.addSpacing(10)
        hlayout.addWidget(chooserButton)
        layout.addLayout(hlayout)
        layout.setSpacing(0)
        layout.addWidget(self.makeDescLabel(descText))
        return layout

class LabeledLineText(QtWidgets.QWidget):
    def __init__(self, parent, label):
        QtWidgets.QWidget.__init__(self, parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.label = QtWidgets.QLabel(label, parent)
        self.edit = QtWidgets.QLineEdit(parent)
        layout.addWidget(self.label)
        layout.addSpacing(10)
        layout.addWidget(self.edit)
        
    def text(self):
        return self.edit.text()
    
    def setText(self, newText):
        self.edit.setText(newText)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = RenamerWindow(app)
    window.show()
    sys.exit(app.exec_())
