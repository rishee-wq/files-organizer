"""
RishFlow v2.0 - Smart File Organizer
Complete implementation with AI sorting, duplicates, previews, themes
Python 3.13 compatible - NO sklearn dependency
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
import sqlite3
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False
import cv2
import numpy as np
from PIL import Image
import pytesseract

# Import AI Sorter and Duplicate Finder
from ai_sorter import AISmartSorter
from duplicate_finder import DuplicateFinder

# App paths
APP_ICON = "logo.ico"
APP_LOGO = "Logo.jpg"
UI_HTML = os.path.join(os.path.dirname(__file__), "stitch_rishflow_dashboard_home (1)", "code.html")

class DuplicateThread(QThread):
    scan_complete = pyqtSignal(list)
    
    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
    
    def run(self):
        finder = DuplicateFinder()
        duplicates = finder.find_duplicates(self.folder_path)
        self.scan_complete.emit(duplicates)


class OrganizerThread(QThread):
    progress_updated = pyqtSignal(int)
    log_message = pyqtSignal(str)
    preview_image = pyqtSignal(str)
    files_moved = pyqtSignal(list)  # Emit list of (source, dest) tuples
    
    def __init__(self, source_path, dest_path, sort_mode):
        super().__init__()
        self.source_path = source_path
        self.dest_path = dest_path
        self.sort_mode = sort_mode
        self.ai_sorter = AISmartSorter() if sort_mode == "AI Smart" else None
        self.is_running = True
        
    def run(self):
        source = Path(self.source_path)
        files = list(source.rglob('*'))
        image_files = [f for f in files if f.suffix.lower() in AISmartSorter.IMAGE_EXTS]
        
        total_files = len([f for f in files if f.is_file()])
        processed = 0
        
        self.log_message.emit(f"Found {total_files} files to organize...")
        
        moved_files = []
        
        for file_path in files:
            if not self.is_running:
                break
                
            if file_path.is_file():
                try:
                    category = self.get_category(file_path)
                    dest_file = Path(self.dest_path) / category / file_path.name
                    
                    # Create destination directory
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Skip if already exists (avoid overwrite)
                    if dest_file.exists():
                        counter = 1
                        while (dest_file.parent / f"{file_path.stem}_{counter}{file_path.suffix}").exists():
                            counter += 1
                        dest_file = dest_file.parent / f"{file_path.stem}_{counter}{file_path.suffix}"
                    
                    shutil.move(str(file_path), str(dest_file))
                    moved_files.append((str(file_path), str(dest_file)))
                    
                    if file_path.suffix.lower() in AISmartSorter.IMAGE_EXTS:
                        self.preview_image.emit(str(dest_file))
                    
                    self.log_message.emit(f"✅ {file_path.name} → {category}/")
                    
                except Exception as e:
                    self.log_message.emit(f"⚠️ Error moving {file_path.name}: {str(e)}")
                
                processed += 1
                progress = int((processed / total_files) * 100)
                self.progress_updated.emit(progress)
        
        self.log_message.emit(f"🎉 Complete! Moved {len(moved_files)} files.")
        self.files_moved.emit(moved_files)  # Send moved files to main window for undo
        
    def get_category(self, file_path):
        if self.sort_mode == "AI Smart" and self.ai_sorter:
            return self.ai_sorter.classify_file(file_path)
        elif self.sort_mode == "Extension":
            return self.extension_category(file_path)
        elif self.sort_mode == "Date":
            timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
            return timestamp.strftime(f"ByDate/%Y/%m/%d")
        else:
            return "Misc"
    
    def extension_category(self, file_path):
        ext = file_path.suffix.lower()
        categories = {
            '.jpg': 'Images/Photos', '.jpeg': 'Images/Photos', '.png': 'Images/Photos',
            '.gif': 'Images/Photos', '.bmp': 'Images/Others', '.webp': 'Images/Photos',
            '.pdf': 'Documents/PDFs', '.docx': 'Documents/Word', '.txt': 'Documents/Text',
            '.mp4': 'Videos', '.avi': 'Videos', '.mkv': 'Videos', '.mov': 'Videos',
            '.mp3': 'Audio', '.wav': 'Audio', '.flac': 'Audio',
            '.zip': 'Archives', '.rar': 'Archives', '.7z': 'Archives',
            '.py': 'Code/Python', '.js': 'Code/JavaScript', '.cpp': 'Code/C++',
            '.exe': 'Executables', '.msi': 'Executables'
        }
        return categories.get(ext, 'Misc')

class RishFlow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 RishFlow v2.0 - Smart File Organizer")
        self.setGeometry(100, 100, 1400, 900)
        # Set window icon
        if os.path.exists(APP_ICON):
            self.setWindowIcon(QIcon(APP_ICON))
        self.undo_stack = []
        self.organizer_thread = None
        self.init_database()
        self.init_ui()
        self.apply_theme('dark')
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left Panel - Controls (30%)
        left_panel = self.create_left_panel()
        main_layout.addLayout(left_panel, 1)
        
        # Right Panel - Preview & Log (70%)
        right_panel = self.create_right_panel()
        main_layout.addLayout(right_panel, 2)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
    def create_left_panel(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.addStretch()
        
        # Logo
        if os.path.exists(APP_LOGO):
            logo = QLabel()
            pixmap = QPixmap(APP_LOGO)
            pixmap = pixmap.scaledToWidth(200, Qt.SmoothTransformation)
            logo.setPixmap(pixmap)
            logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo)
        
        # Title
        title = QLabel("RishFlow v2.0")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Source Folder
        layout.addWidget(QLabel("📁 Source Folder:"))
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Browse to select Downloads, Desktop, etc.")
        source_layout = QHBoxLayout()
        source_layout.addWidget(self.source_input)
        self.source_btn = QPushButton("📂 Browse")
        self.source_btn.clicked.connect(self.browse_source)
        source_layout.addWidget(self.source_btn)
        layout.addLayout(source_layout)
        
        # Destination Folder
        layout.addWidget(QLabel("📂 Destination Folder:"))
        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Where organized files will go")
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(self.dest_input)
        self.dest_btn = QPushButton("📂 Browse")
        self.dest_btn.clicked.connect(self.browse_dest)
        dest_layout.addWidget(self.dest_btn)
        layout.addLayout(dest_layout)
        
        # Sort Mode
        layout.addWidget(QLabel("🧠 Sort By:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Extension", "Date", "AI Smart"])
        layout.addWidget(self.sort_combo)
        
        # Main Action Buttons
        button_layout = QVBoxLayout()
        
        self.start_btn = QPushButton("🚀 START ORGANIZING")
        self.start_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.start_btn.clicked.connect(self.start_organizing)
        button_layout.addWidget(self.start_btn)
        
        self.undo_btn = QPushButton("↶ UNDO LAST ACTION")
        self.undo_btn.clicked.connect(self.undo_last)
        self.undo_btn.setEnabled(False)
        button_layout.addWidget(self.undo_btn)
        
        self.duplicates_btn = QPushButton("🔍 FIND DUPLICATES")
        self.duplicates_btn.clicked.connect(self.find_duplicates)
        button_layout.addWidget(self.duplicates_btn)
        
        layout.addLayout(button_layout)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        return layout
    
    def create_right_panel(self):
        layout = QVBoxLayout()
        
        # Try to load HTML UI if WebEngine is available
        if HAS_WEBENGINE and os.path.exists(UI_HTML):
            web_view = QWebEngineView()
            web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(UI_HTML)))
            layout.addWidget(web_view)
        else:
            # Fallback to original Qt UI
            # Preview Panel
            preview_group = QGroupBox("👁️ Preview")
            preview_layout = QVBoxLayout(preview_group)
            
            self.preview_label = QLabel("No file selected for preview")
            self.preview_label.setMinimumHeight(300)
            self.preview_label.setAlignment(Qt.AlignCenter)
            self.preview_label.setStyleSheet("border: 2px dashed #666; border-radius: 10px; background: #2a2a2a;")
            preview_layout.addWidget(self.preview_label)
            
            layout.addWidget(preview_group)
            
            # Activity Log
            log_group = QGroupBox("📋 Activity Log")
            log_layout = QVBoxLayout(log_group)
            
            self.log_list = QListWidget()
            self.log_list.setMaximumHeight(400)
            log_layout.addWidget(self.log_list)
            
            layout.addWidget(log_group)
        
        return layout
    
    def init_database(self):
        """Initialize SQLite activity log"""
        self.db_path = "rishflow_activity.db"
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                action TEXT,
                source_path TEXT,
                dest_path TEXT,
                file_count INTEGER
            )
        ''')
        self.conn.commit()
    
    def browse_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_input.setText(folder)
    
    def browse_dest(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_input.setText(folder)
    
    def start_organizing(self):
        if not self.source_input.text() or not self.dest_input.text():
            self.log_message("❌ Please select both source and destination folders!")
            return
        
        self.start_btn.setEnabled(False)
        self.undo_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Organizing files...")
        
        self.organizer_thread = OrganizerThread(
            self.source_input.text(),
            self.dest_input.text(),
            self.sort_combo.currentText()
        )
        self.organizer_thread.progress_updated.connect(self.progress_bar.setValue)
        self.organizer_thread.log_message.connect(self.log_message)
        self.organizer_thread.preview_image.connect(self.show_preview)
        self.organizer_thread.files_moved.connect(self.on_files_moved)
        self.organizer_thread.finished.connect(self.organizing_complete)
        self.organizer_thread.start()
    
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        self.log_list.addItem(full_message)
        self.log_list.scrollToBottom()
        
        # Save to database
        self.conn.execute(
            "INSERT INTO activity (timestamp, action, source_path, dest_path, file_count) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), message, self.source_input.text(), self.dest_input.text(), 1)
        )
        self.conn.commit()
    
    def show_preview(self, image_path):
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled)
        else:
            self.preview_label.setText("Cannot preview this file")
    
    def organizing_complete(self):
        self.start_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.undo_btn.setEnabled(True)
        self.status_bar.showMessage("✅ Organization complete!")
        self.log_message("🎉 All files organized successfully!")
    
    def on_files_moved(self, moved_files):
        """Store moved files for undo functionality"""
        self.undo_stack.append(moved_files)
    
    def undo_last(self):
        if not self.undo_stack:
            self.log_message("❌ Nothing to undo!")
            return
        
        moved_files = self.undo_stack.pop()
        undo_count = 0
        undo_errors = 0
        dest_folders = set()  # Track destination folders to clean up
        
        self.log_message(f"↶ Undoing {len(moved_files)} file(s)...")
        
        # Reverse the moves (destination back to source)
        for source_path, dest_path in moved_files:
            try:
                # Move file back to original source location
                src = Path(dest_path)
                dst = Path(source_path)
                
                if src.exists():
                    # Track the destination folder for cleanup
                    dest_folders.add(src.parent)
                    
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                    undo_count += 1
                    self.log_message(f"↶ Restored: {Path(source_path).name}")
            except Exception as e:
                undo_errors += 1
                self.log_message(f"⚠️ Failed to restore {Path(source_path).name}: {str(e)}")
        
        # Clean up empty folders that were created during organization
        folders_deleted = 0
        for folder in dest_folders:
            try:
                # Remove empty directories starting from the deepest level
                for parent in [folder, *folder.parents]:
                    if parent.exists() and not list(parent.iterdir()):
                        try:
                            parent.rmdir()
                            folders_deleted += 1
                            self.log_message(f"🗑️ Removed empty folder: {parent.name}")
                        except OSError:
                            break  # Stop if folder is not empty
            except Exception as e:
                self.log_message(f"⚠️ Could not remove folder {folder.name}: {str(e)}")
        
        self.log_message(f"✅ Undo complete! Restored {undo_count} file(s). Removed {folders_deleted} folder(s). Errors: {undo_errors}")
        
        if not self.undo_stack:
            self.undo_btn.setEnabled(False)
    
    def find_duplicates(self):
        if not self.source_input.text():
            self.log_message("❌ Please select a source folder first!")
            return
        
        self.log_message("🔍 Scanning for duplicate files...")
        
        # Run duplicate finder in background
        self.duplicate_thread = DuplicateThread(self.source_input.text())
        self.duplicate_thread.scan_complete.connect(self.show_duplicates_dialog)
        self.duplicate_thread.start()
    
    def show_duplicates_dialog(self, duplicates):
        """Display found duplicates in a dialog"""
        if not duplicates:
            QMessageBox.information(self, "Duplicate Finder", "✅ No duplicates found!")
            self.log_message("✅ No duplicate files found.")
            return
        
        self.log_message(f"Found {len(duplicates)} duplicate group(s). Displaying results...")
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("🔍 Duplicate Files Found")
        dialog.setGeometry(200, 200, 900, 600)
        layout = QVBoxLayout()
        
        # Summary
        total_duplicates = sum(len(d['files']) - 1 for d in duplicates)
        layout.addWidget(QLabel(f"Found {total_duplicates} duplicate file(s) in {len(duplicates)} group(s):"))
        
        # List of duplicates
        list_widget = QListWidget()
        for idx, dup_group in enumerate(duplicates):
            size_mb = dup_group['size'] / (1024 * 1024)
            group_text = f"Group {idx+1} ({size_mb:.2f} MB):"
            item = QListWidgetItem(group_text)
            item.setFont(QFont('Arial', 10, QFont.Bold))
            list_widget.addItem(item)
            
            for file_path in dup_group['files']:
                file_item = QListWidgetItem(f"  → {file_path}")
                file_item.setFont(QFont('Arial', 9))
                list_widget.addItem(file_item)
        
        layout.addWidget(list_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def apply_theme(self, theme_name):
        if theme_name == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #404040;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 10px;
                    background-color: #2a2a2a;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
                QPushButton {
                    background-color: #404040;
                    border: 1px solid #555;
                    border-radius: 6px;
                    padding: 10px;
                    font-weight: bold;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #303030;
                }
                QPushButton:disabled {
                    background-color: #252525;
                    color: #666;
                }
                QLineEdit, QComboBox {
                    background-color: #2d2d2d;
                    border: 2px solid #555;
                    border-radius: 6px;
                    padding: 8px;
                    color: white;
                    font-size: 12px;
                }
                QLineEdit:focus, QComboBox:focus {
                    border-color: #4CAF50;
                }
                QListWidget {
                    background-color: #2d2d2d;
                    border: 2px solid #555;
                    border-radius: 6px;
                    color: white;
                    font-size: 11px;
                }
                QProgressBar {
                    border: 2px solid #555;
                    border-radius: 6px;
                    text-align: center;
                    background-color: #2d2d2d;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 4px;
                }
                QLabel {
                    color: #ffffff;
                    font-size: 12px;
                }
            """)
    
    def keyPressEvent(self, event):
        # Keyboard shortcuts
        if event.key() == Qt.Key_F5:
            self.start_organizing()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() == Qt.ControlModifier:
            self.undo_last()
        super().keyPressEvent(event)

def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("RishFlow")
    app.setApplicationName("RishFlow v2.0")
    
    # Set application icon
    if os.path.exists(APP_ICON):
        app.setWindowIcon(QIcon(APP_ICON))
    
    # Modern dark theme
    app.setStyle('Fusion')
    
    window = RishFlow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
    print("🚀 Starting RishFlow v2.0...")