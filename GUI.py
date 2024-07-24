import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QMessageBox, QStatusBar, 
                             QGridLayout, QAction)
from PyQt5.QtCore import Qt, QMimeData, QSize, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QIcon, QPalette, QColor, QPixmap, QPainter, QPen, QBrush



# Import the conversion functions from your scripts
from nifti_to_jpg import nifti_to_jpg
from json_to_nift import convert_annotations_to_rotated_nii



class DropArea(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setText("\nDrop files here\nor click to browse")
        self.setStyleSheet("""
            QLabel {
                background-color: #2C3E50;
                border: 2px dashed #3498DB;
                border-radius: 10px;
                padding: 20px;
                color: #ECF0F1;
                font-size: 14px;
            }
        """)
        self.setAcceptDrops(True)
        self.setFixedSize(300, 200)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet("""
                QLabel {
                    background-color: #34495E;
                    border: 2px solid #3498DB;
                    border-radius: 10px;
                    padding: 20px;
                    color: #ECF0F1;
                    font-size: 14px;
                }
            """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                background-color: #2C3E50;
                border: 2px dashed #3498DB;
                border-radius: 10px;
                padding: 20px;
                color: #ECF0F1;
                font-size: 14px;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        print(f"Debug: Dropped files: {files}")
        if files and os.path.isdir(files[0]):
            full_path = os.path.abspath(files[0])
            print(f"Debug: Full path of dropped folder: {full_path}")
            self.setText(f"Folder: {os.path.basename(full_path)}")
            self.setToolTip(full_path)
            if isinstance(self.parent(), MainWindow):
                self.parent().json_folder = full_path
                print(f"Debug: Updated MainWindow json_folder: {self.parent().json_folder}")
        elif files and files[0].endswith('.nii.gz'):
            self.setText(f"File: {os.path.basename(files[0])}")
            self.setToolTip(files[0])
            if isinstance(self.parent(), MainWindow):
                self.parent().input_nifti_file = files[0]
        self.setStyleSheet("""
            QLabel {
                background-color: #2C3E50;
                border: 2px dashed #3498DB;
                border-radius: 10px;
                padding: 20px;
                color: #ECF0F1;
                font-size: 14px;
            }
        """)

    def elide_text(self, text, max_length):
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NIfTI to NIFTI Converter")
        self.setGeometry(100, 100, 800, 500)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1A2530;
            }
            QLabel {
                color: #ECF0F1;
                font-size: 16px;
            }
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
                text-align: left;
                padding-right: 40px;  /* Space for the icon */
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QStatusBar {
                background-color: #34495E;
                color: #ECF0F1;
            }
        """)

        self.input_nifti_file = None
        self.json_folder = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        
        h_layout = QHBoxLayout()
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        # NIfTI to JPG area
        nifti_label = QLabel("NIfTI to JPG")
        nifti_label.setAlignment(Qt.AlignCenter)
        self.nifti_drop_area = DropArea()
        self.nifti_drop_area.mousePressEvent = self.browse_nifti_file
        self.nifti_button = QPushButton("Convert NIfTI to JPG")
        self.nifti_button.clicked.connect(self.convert_nifti_to_jpg)
        self.nifti_button.setToolTip("Convert the selected NIfTI file to JPG images")

        # JSON to NIfTI area
        json_label = QLabel("JSON to NIfTI")
        json_label.setAlignment(Qt.AlignCenter)
        self.json_drop_area = DropArea()
        self.json_drop_area.mousePressEvent = self.browse_json_folder
        self.json_button = QPushButton("Convert JSON to NIfTI")
        self.json_button.clicked.connect(self.convert_json_to_nifti)
        self.json_button.setToolTip("Convert the selected JSON files to a NIfTI file")

        # Add widgets to the grid layout
        grid_layout.addWidget(nifti_label, 0, 0)
        grid_layout.addWidget(self.nifti_drop_area, 1, 0)
        grid_layout.addWidget(self.nifti_button, 2, 0)
        grid_layout.addWidget(json_label, 0, 1)
        grid_layout.addWidget(self.json_drop_area, 1, 1)
        grid_layout.addWidget(self.json_button, 2, 1)

        h_layout.addStretch(1)
        h_layout.addLayout(grid_layout)
        h_layout.addStretch(1)

        main_layout.addStretch(1)
        main_layout.addLayout(h_layout)
        main_layout.addStretch(1)

        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Timers for success icons
        self.nifti_success_timer = QTimer(self)
        self.nifti_success_timer.timeout.connect(lambda: self.hide_success_icon(self.nifti_button))
        self.json_success_timer = QTimer(self)
        self.json_success_timer.timeout.connect(lambda: self.hide_success_icon(self.json_button))

    def browse_nifti_file(self, event):
        file, _ = QFileDialog.getOpenFileName(self, "Select NIfTI file", "", "NIfTI files (*.nii.gz)")
        if file:
            self.nifti_drop_area.setText(self.nifti_drop_area.elide_text(file, 30))
            self.input_nifti_file = file
            self.statusBar.showMessage(f"NIfTI file selected: {file}")

    def browse_json_folder(self, event):
        folder = QFileDialog.getExistingDirectory(self, "Select JSON folder")
        print(f"Debug: Selected folder from dialog: {folder}")
        if folder:
            self.json_folder = folder
            print(f"Debug: Stored json_folder: {self.json_folder}")
            self.json_drop_area.setText(f"Folder: {os.path.basename(folder)}")
            self.json_drop_area.setToolTip(folder)
            self.statusBar.showMessage(f"JSON folder selected: {folder}")

    def convert_nifti_to_jpg(self):
        if self.input_nifti_file and self.input_nifti_file.endswith('.nii.gz'):
            output_folder = os.path.splitext(os.path.splitext(self.input_nifti_file)[0])[0] + '_jpg'
            nifti_to_jpg(self.input_nifti_file, output_folder)
            self.nifti_drop_area.setText(self.nifti_drop_area.elide_text(f"Converted: {self.input_nifti_file}", 30))
            self.statusBar.showMessage(f"NIfTI to JPG conversion complete. Output: {output_folder}")
            self.show_success_icon(self.nifti_button)
            self.nifti_success_timer.start(10000)  # 10 seconds
        else:
            QMessageBox.warning(self, "Invalid File", "Please select a valid .nii.gz file")

    def convert_json_to_nifti(self):
        print(f"Debug: Current json_folder: {self.json_folder}")
        if not self.input_nifti_file:
            QMessageBox.warning(self, "Missing Input", "Please select a NIfTI file first.")
            return

        if not self.json_folder:
            QMessageBox.warning(self, "Missing Input", "Please select a folder containing JSON files.")
            return

        try:
            print(f"Debug: Attempting conversion with json_folder: {self.json_folder}")
            output_nii_file = os.path.join(os.path.dirname(self.input_nifti_file), 'segmentation.nii.gz')
            convert_annotations_to_rotated_nii(self.json_folder, self.input_nifti_file, output_nii_file)
            self.statusBar.showMessage(f"JSON to NIfTI conversion complete. Output: {output_nii_file}")
            self.show_success_icon(self.json_button)
            self.json_success_timer.start(10000)  # 10 seconds
            #QMessageBox.information(self, "Conversion Complete", f"JSON to NIfTI conversion complete.\nInput folder: {self.json_folder}\nOutput: {output_nii_file}")
        except Exception as e:
            error_message = f"An error occurred during conversion: {str(e)}"
            print(f"Debug: {error_message}")
            QMessageBox.critical(self, "Conversion Error", error_message)

    def show_success_icon(self, button):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        
        # Draw green circle
        painter.setBrush(QBrush(QColor("#2ecc71")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 24, 24)
        
        # Draw white checkmark
        painter.setPen(QPen(Qt.white, 2, Qt.SolidLine))
        painter.drawLine(5, 12, 10, 17)
        painter.drawLine(10, 17, 19, 8)
        
        painter.end()
        
        icon = QIcon(pixmap)
        button.setIcon(icon)
        button.setIconSize(QSize(24, 24))

    def hide_success_icon(self, button):
        button.setIcon(QIcon())
        
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set fusion style for better look
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
