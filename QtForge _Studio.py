"""
Dynamic Source Loader and Renderer Host
A professional Qt application for embedding external Python-Qt modules at runtime.
Complete with auto-reload functionality and detachable renderer.
"""

import sys
import os
import ast
import importlib.util
import configparser
import traceback
from pathlib import Path
from typing import Optional, Any

from PyQt6.QtCore import (
    Qt, QTimer, QSettings, pyqtSlot,
    QFileSystemWatcher
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QMessageBox, QFileDialog,
    QCheckBox, QGroupBox, QProgressBar, 
)
from PyQt6.QtGui import (
    QAction, QFont, QIcon
)

from libs.Detachablerenderer import DetachableRenderer
from libs.Sourcevalidator import SourceValidator


class MainWindow(QMainWindow):
    """Main orchestrator window for dynamic source loading."""
    
    def __init__(self):
        super().__init__()
        self.current_source: Optional[Path] = None
        self.current_module: Any = None
        self.validator_thread: Optional[SourceValidator] = None
        
        # File watcher for auto-reload
        self.file_watcher = QFileSystemWatcher()
        self.watched_files = set()
        self.last_modification = {}
        
        # Debounce timer to prevent multiple reloads
        self.reload_timer = QTimer()
        self.reload_timer.setSingleShot(True)
        self.reload_timer.setInterval(1500)  # 1.5 second debounce
        self.reload_timer.timeout.connect(self.debounced_reload)
        
        # Track if we're currently reloading
        self.is_reloading = False
        
        self.setup_window()
        self.setup_ui()
        self.setup_connections()
        self.apply_main_stylesheet()
        
    def setup_window(self):
        """Configure main window properties."""
        self.setWindowIcon(QIcon("img/QtForge Studio.png"))
        self.setWindowTitle("Dynamic Source Loader Host")
        self.setGeometry(100, 100, 1400, 900)
        
        # Application settings
        self.settings = QSettings("DynamicLoader", "HostApp")
        
        # Restore window state
        if self.settings.contains("window/geometry"):
            self.restoreGeometry(self.settings.value("window/geometry"))
        if self.settings.contains("window/state"):
            self.restoreState(self.settings.value("window/state"))
            
    def apply_main_stylesheet(self):
        """Apply QSS styling to main UI only."""
        self.setStyleSheet("""
            /* Main window background */
            QMainWindow {
                background-color: #1a202c;
            }
            
            /* Central widget */
            QWidget#CentralWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #2d3748, stop: 1 #1a202c
                );
            }
            
            /* Menu bar */
            QMenuBar {
                background-color: #2d3748;
                color: #e2e8f0;
                border-bottom: 1px solid #4a5568;
                padding: 4px;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 12px;
                border-radius: 3px;
            }
            
            QMenuBar::item:selected {
                background-color: #4a5568;
            }
            
            QMenuBar::item:pressed {
                background-color: #5a6578;
            }
            
            /* Menus */
            QMenu {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                color: #e2e8f0;
                padding: 4px;
            }
            
            QMenu::item {
                padding: 6px 24px 6px 24px;
            }
            
            QMenu::item:selected {
                background-color: #4a5568;
            }
            
            QMenu::separator {
                height: 1px;
                background-color: #4a5568;
                margin: 4px 8px;
            }
            
            /* Toolbar */
            QToolBar {
                background-color: #2d3748;
                border: none;
                border-bottom: 1px solid #4a5568;
                spacing: 4px;
                padding: 4px;
            }
            
            QToolBar::separator {
                width: 1px;
                background-color: #4a5568;
                margin: 4px 8px;
            }
            
            /* Status bar */
            QStatusBar {
                background-color: #2d3748;
                color: #a0aec0;
                border-top: 1px solid #4a5568;
            }
            
            /* Control panel */
            QFrame#ControlPanel {
                background-color: rgba(45, 55, 72, 0.95);
                border: 1px solid #4a5568;
                border-radius: 8px;
                padding: 5px;
            }
            
            /* Buttons */
            QPushButton#BtnSelect {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4299e1, stop:1 #3182ce);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 140px;
            }
            
            QPushButton#BtnSelect:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #63b3ed, stop:1 #4299e1);
            }
            
            QPushButton#BtnSelect:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3182ce, stop:1 #2c5282);
            }
            
            QPushButton#BtnReload {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #48bb78, stop:1 #38a169);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 140px;
            }
            
            QPushButton#BtnReload:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #68d391, stop:1 #48bb78);
            }
            
            QPushButton#BtnReload:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #38a169, stop:1 #2f855a);
            }
            
            QPushButton#BtnReload:disabled {
                background: #4a5568;
                color: #a0aec0;
            }
            
            /* Status label */
            QLabel#StatusLabel {
                color: #e2e8f0;
                font-size: 11px;
                padding: 4px 8px;
                background-color: rgba(26, 32, 44, 0.7);
                border-radius: 3px;
                border: 1px solid #4a5568;
            }
            
            /* Progress bar */
            QProgressBar#ValidationProgress {
                border: 1px solid #4a5568;
                border-radius: 3px;
                text-align: center;
                color: #e2e8f0;
                font-size: 10px;
            }
            
            QProgressBar#ValidationProgress::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4299e1, stop:1 #805ad5);
                border-radius: 2px;
            }
            
            /* Checkbox */
            QCheckBox#AutoReloadCheck {
                color: #cbd5e0;
                font-size: 11px;
            }
            
            QCheckBox#AutoReloadCheck::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #4a5568;
                border-radius: 3px;
                background-color: #2d3748;
            }
            
            QCheckBox#AutoReloadCheck::indicator:checked {
                background-color: #4299e1;
                border-color: #3182ce;
                image: url(checkbox.png);
            }
            
            QCheckBox#AutoReloadCheck::indicator:hover {
                border-color: #63b3ed;
            }
            
            /* Group boxes */
            QGroupBox#SourceInfoGroup {
                color: #cbd5e0;
                border: 1px solid #4a5568;
                border-radius: 4px;
                margin-top: 12px;
                font-size: 11px;
                font-weight: bold;
            }
            
            QGroupBox#SourceInfoGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            /* Info labels */
            QLabel#SourceInfoLabel {
                color: #a0aec0;
                font-size: 10px;
                padding: 2px;
                background-color: rgba(45, 55, 72, 0.5);
                border-radius: 2px;
            }
            
            /* Watcher status */
            QLabel#WatcherStatus {
                color: #ed8936;
                font-size: 10px;
                padding: 2px 6px;
                background-color: rgba(237, 137, 54, 0.1);
                border-radius: 2px;
                border: 1px solid rgba(237, 137, 54, 0.3);
            }
        """)
        
    def setup_ui(self):
        """Initialize the user interface."""
        # Create central widget
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create detachable renderer
        self.renderer = DetachableRenderer(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.renderer)
        
        # Control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Add stretch to push control panel to top
        main_layout.addStretch()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.create_status_bar()
        
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Source Folder", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.select_source_folder)
        file_menu.addAction(open_action)
        
        reload_action = QAction("&Reload Source", self)
        reload_action.setShortcut("F5")
        reload_action.triggered.connect(self.reload_source)
        file_menu.addAction(reload_action)
        
        file_menu.addSeparator()
        
        # Auto-reload submenu
        auto_reload_menu = file_menu.addMenu("&Auto-reload")
        
        enable_auto_action = QAction("&Enable Auto-reload", self)
        enable_auto_action.setCheckable(True)
        enable_auto_action.setChecked(False)
        enable_auto_action.triggered.connect(lambda: self.auto_reload_check.setChecked(True))
        auto_reload_menu.addAction(enable_auto_action)
        
        disable_auto_action = QAction("&Disable Auto-reload", self)
        disable_auto_action.triggered.connect(lambda: self.auto_reload_check.setChecked(False))
        auto_reload_menu.addAction(disable_auto_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        toggle_renderer_action = QAction("&Toggle Renderer", self)
        toggle_renderer_action.setShortcut("Ctrl+R")
        toggle_renderer_action.triggered.connect(self.toggle_renderer)
        view_menu.addAction(toggle_renderer_action)
        
        detach_renderer_action = QAction("&Detach/Attach Renderer", self)
        detach_renderer_action.setShortcut("Ctrl+D")
        detach_renderer_action.triggered.connect(self.toggle_detach_renderer)
        view_menu.addAction(detach_renderer_action)
        
        view_menu.addSeparator()
        
        reset_layout_action = QAction("&Reset Layout", self)
        reset_layout_action.triggered.connect(self.reset_layout)
        view_menu.addAction(reset_layout_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("&Settings")
        
        theme_action = QAction("&Toggle Theme", self)
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self.toggle_theme)
        settings_menu.addAction(theme_action)
        
    def create_toolbar(self):
        """Create the application toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.setObjectName("MainToolbar")  # ADD THIS LINE
        toolbar.setMovable(False)
        
        # Open button
        open_btn = QPushButton("📂 Open")
        open_btn.clicked.connect(self.select_source_folder)
        toolbar.addWidget(open_btn)
        
        # Reload button
        reload_btn = QPushButton("🔄 Reload")
        reload_btn.clicked.connect(self.reload_source)
        reload_btn.setEnabled(False)
        self.reload_btn = reload_btn
        toolbar.addWidget(reload_btn)
        
        toolbar.addSeparator()
        
        # Detach button
        detach_btn = QPushButton("⤢ Detach")
        detach_btn.clicked.connect(self.toggle_detach_renderer)
        toolbar.addWidget(detach_btn)
        
        toolbar.addSeparator()
        
        # Auto-reload indicator
        self.auto_reload_indicator = QLabel("⏰ OFF")
        self.auto_reload_indicator.setToolTip("Auto-reload status")
        toolbar.addWidget(self.auto_reload_indicator)
        
    def create_status_bar(self):
        """Create the application status bar."""
        status_bar = self.statusBar()
        
        # Ready label
        self.ready_label = QLabel("Ready")
        status_bar.addWidget(self.ready_label)
        
        # File watcher status
        self.watcher_status_label = QLabel("🔒 No files watched")
        self.watcher_status_label.setObjectName("WatcherStatus")
        status_bar.addWidget(self.watcher_status_label)
        
        # Memory usage
        self.memory_label = QLabel("")
        status_bar.addPermanentWidget(self.memory_label)
        
        # Update memory usage periodically
        self.memory_timer = QTimer()
        self.memory_timer.timeout.connect(self.update_memory_usage)
        self.memory_timer.start(5000)
        self.update_memory_usage()
        
    def update_memory_usage(self):
        """Update memory usage display."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.setText(f"🧠 {memory_mb:.1f} MB")
        except ImportError:
            self.memory_label.setText("🧠 N/A")
        
    def create_control_panel(self):
        """Create the main control panel."""
        control_panel = QFrame()
        control_panel.setObjectName("ControlPanel")
        
        # Main layout
        panel_layout = QVBoxLayout(control_panel)
        panel_layout.setSpacing(12)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Dynamic Source Loader")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #ffffff; padding: 10px;")
        panel_layout.addWidget(title)
        
        # Description
        desc = QLabel("Load and host external Python-Qt applications dynamically")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #cbd5e0; padding-bottom: 15px;")
        panel_layout.addWidget(desc)
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.btn_select = QPushButton("📂 Select Source Folder")
        self.btn_select.setObjectName("BtnSelect")
        self.btn_select.setFixedHeight(36)
        
        self.btn_reload = QPushButton("🔄 Reload Source")
        self.btn_reload.setObjectName("BtnReload")
        self.btn_reload.setFixedHeight(36)
        self.btn_reload.setEnabled(False)
        
        button_layout.addWidget(self.btn_select)
        button_layout.addWidget(self.btn_reload)
        button_layout.addStretch()
        
        panel_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("ValidationProgress")
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        panel_layout.addWidget(self.progress_bar)
        
        # Status area
        status_layout = QHBoxLayout()
        
        self.lbl_status = QLabel("No source loaded")
        self.lbl_status.setObjectName("StatusLabel")
        self.lbl_status.setFixedHeight(24)
        
        # Auto-reload checkbox
        self.auto_reload_check = QCheckBox("⏰ Auto-reload on file change")
        self.auto_reload_check.setObjectName("AutoReloadCheck")
        self.auto_reload_check.setChecked(False)
        
        status_layout.addWidget(self.lbl_status)
        status_layout.addStretch()
        status_layout.addWidget(self.auto_reload_check)
        
        panel_layout.addLayout(status_layout)
        
        # Source info group
        source_group = QGroupBox("📄 Source Information")
        source_group.setObjectName("SourceInfoGroup")
        group_layout = QVBoxLayout()
        
        self.source_info_label = QLabel("No source selected")
        self.source_info_label.setObjectName("SourceInfoLabel")
        self.source_info_label.setWordWrap(True)
        group_layout.addWidget(self.source_info_label)
        
        # Watched files info
        self.watched_files_label = QLabel("Watching 0 files")
        self.watched_files_label.setObjectName("SourceInfoLabel")
        group_layout.addWidget(self.watched_files_label)
        
        source_group.setLayout(group_layout)
        panel_layout.addWidget(source_group)
        
        return control_panel
        
    def setup_connections(self):
        """Connect signals and slots."""
        self.btn_select.clicked.connect(self.select_source_folder)
        self.btn_reload.clicked.connect(self.reload_source)
        self.auto_reload_check.stateChanged.connect(self.on_auto_reload_changed)
        
    def select_source_folder(self):
        """Open dialog to select source folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Source Folder",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            self.load_source(Path(folder))
            
    def load_source(self, folder_path: Path):
        """Load a source from the specified folder."""
        # Look for .ini files first
        ini_files = list(folder_path.glob("*.ini"))
        if not ini_files:
            QMessageBox.warning(
                self,
                "No Config Files",
                f"No .ini config files found in {folder_path}"
            )
            return
            
        # Use the first .ini file as config
        config_file = ini_files[0]
        
        # Parse config to find the module
        config = configparser.ConfigParser()
        config.read(config_file)
        
        if 'source' not in config:
            QMessageBox.warning(
                self,
                "Invalid Config",
                f"Missing [source] section in {config_file.name}"
            )
            return
            
        module_name = config.get('source', 'module', fallback=None)
        if not module_name:
            QMessageBox.warning(
                self,
                "Invalid Config",
                f"No module specified in {config_file.name}"
            )
            return
            
        # Find the Python file
        module_path = folder_path / f"{module_name}.py"
        if not module_path.exists():
            QMessageBox.warning(
                self,
                "Module Not Found",
                f"Module file {module_name}.py not found in {folder_path}"
            )
            return
            
        self.current_source = module_path
        
        # Update source info
        self.source_info_label.setText(
            f"📄 Source: {module_path.name}\n"
            f"⚙️ Config: {config_file.name}\n"
            f"📁 Path: {module_path.parent}"
        )
        
        # Start validation
        self.start_validation(module_path)
        
    def start_validation(self, source_path: Path):
        """Start background validation of source."""
        if self.validator_thread and self.validator_thread.isRunning():
            self.validator_thread.terminate()
            self.validator_thread.wait()
            
        # Reset UI for new validation
        self.btn_select.setEnabled(False)
        self.btn_reload.setEnabled(False)
        self.lbl_status.setText("Validating source...")
        self.progress_bar.hide() #show()
        self.progress_bar.setValue(0)
        
        # Create and start validation thread
        self.validator_thread = SourceValidator(source_path)
        self.validator_thread.preflight_check.connect(self.on_preflight_check)
        self.validator_thread.validation_complete.connect(self.on_validation_complete)
        self.validator_thread.progress_update.connect(self.on_progress_update)
        self.validator_thread.finished.connect(self.on_validation_finished)
        self.validator_thread.start()
        
    @pyqtSlot(int, str)
    def on_progress_update(self, progress: int, message: str):
        """Handle progress updates."""
        self.progress_bar.setValue(progress)
        if progress < 100:
            self.lbl_status.setText(message)
            
    @pyqtSlot(bool, str)
    def on_preflight_check(self, success: bool, message: str):
        """Handle preflight check results."""
        color = "#48bb78" if success else "#f56565"
        self.lbl_status.setText(f"<span style='color:{color}'>{message}</span>")
        
    @pyqtSlot(bool, str, object)
    def on_validation_complete(self, success: bool, message: str, module: Any):
        """Handle validation completion."""
        if success and module:
            self.current_module = module
            self.instantiate_widget(module)
            self.lbl_status.setText(f"<span style='color:#48bb78'>{message}</span>")
            self.btn_reload.setEnabled(True)
            self.reload_btn.setEnabled(True)
            
            # Enable file watching if auto-reload is checked
            if self.auto_reload_check.isChecked():
                QTimer.singleShot(1000, self.enable_file_watching)  # Delay to ensure widget is loaded
        else:
            QMessageBox.critical(self, "Load Failed", message)
            self.lbl_status.setText(f"<span style='color:#f56565'>Load failed</span>")
            
    @pyqtSlot()
    def on_validation_finished(self):
        """Handle validation thread completion."""
        self.btn_select.setEnabled(True)
        self.progress_bar.hide()
        self.ready_label.setText("Ready")
        
    def instantiate_widget(self, module):
        """Instantiate and host the widget from loaded module."""
        try:
            # Get entry point from config
            config_path = self.current_source.parent / f"{self.current_source.stem}.ini"
            config = configparser.ConfigParser()
            config.read(config_path)
            entry_point = config.get('source', 'entry_point', fallback='main_widget')
            
            # Get widget factory function
            widget_factory = getattr(module, entry_point)
            
            # Instantiate widget
            widget = widget_factory()
            
            if isinstance(widget, QWidget):
                # Host in renderer
                self.renderer.host_widget(widget)
                
                # Store reference
                self.hosted_widget = widget
                
                # Update status
                self.ready_label.setText(f"✅ Hosting: {widget.__class__.__name__}")
            else:
                raise TypeError(f"Entry point must return QWidget, got {type(widget)}")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Widget Instantiation Failed",
                f"Failed to create widget: {str(e)}\n\n{traceback.format_exc()}"
            )
            self.lbl_status.setText("<span style='color:#f56565'>Widget creation failed</span>")
            
    # ==================== AUTO-RELOAD FUNCTIONALITY ====================
    
    def on_auto_reload_changed(self, state):
        """Handle auto-reload checkbox state change."""
        if state == Qt.CheckState.Checked.value:
            # Enable file watcher
            if self.current_source:
                self.enable_file_watching()
            self.auto_reload_indicator.setText("⏰ ON")
            self.lbl_status.setText("<span style='color:#4299e1'>Auto-reload enabled</span>")
        else:
            # Disable file watcher
            self.disable_file_watching()
            self.auto_reload_indicator.setText("⏰ OFF")
            self.lbl_status.setText("Auto-reload disabled")
            
    def enable_file_watching(self):
        """Start watching files for changes."""
        if not self.current_source or self.is_reloading:
            return
            
        # Clear existing watched files
        if self.file_watcher.files():
            self.file_watcher.removePaths(self.file_watcher.files())
            
        files_to_watch = []
        
        # Watch the source Python file
        source_file = str(self.current_source)
        if os.path.exists(source_file):
            files_to_watch.append(source_file)
            self.last_modification[source_file] = os.path.getmtime(source_file)
            
        # Watch the config file
        config_path = self.current_source.parent / f"{self.current_source.stem}.ini"
        config_file = str(config_path)
        if os.path.exists(config_file):
            files_to_watch.append(config_file)
            self.last_modification[config_file] = os.path.getmtime(config_file)
            
        # Try to find and watch dependencies
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        # Check for local Python files
                        dep_path = self.current_source.parent / f"{module_name}.py"
                        if dep_path.exists() and str(dep_path) not in files_to_watch:
                            dep_file = str(dep_path)
                            files_to_watch.append(dep_file)
                            self.last_modification[dep_file] = os.path.getmtime(dep_file)
        except:
            pass
            
        # Add files to watcher
        if files_to_watch:
            self.file_watcher.addPaths(files_to_watch)
            
        # Connect file changed signal
        self.file_watcher.fileChanged.connect(self.on_file_changed)
        
        # Update UI
        self.watcher_status_label.setText(f"👁️ Watching {len(files_to_watch)} files")
        self.watched_files_label.setText(f"Watching {len(files_to_watch)} file(s) for changes")
        
    def disable_file_watching(self):
        """Stop watching files for changes."""
        if self.file_watcher.files():
            self.file_watcher.removePaths(self.file_watcher.files())
        try:
            self.file_watcher.fileChanged.disconnect()
        except:
            pass
            
        self.watcher_status_label.setText("🔒 No files watched")
        self.watched_files_label.setText("Watching 0 files")
        
    def on_file_changed(self, path):
        """Handle file change events."""
        if self.is_reloading or not self.auto_reload_check.isChecked():
            return
            
        # Check if file still exists (it might have been temporarily deleted)
        if not os.path.exists(path):
            # File was deleted, re-add when it comes back
            QTimer.singleShot(1000, lambda: self.reenable_file_watching(path))
            return
            
        # Check if file was actually modified (not just accessed)
        try:
            current_mtime = os.path.getmtime(path)
            last_mtime = self.last_modification.get(path, 0)
            
            # Only trigger if modification time increased
            if current_mtime > last_mtime + 0.1:  # Small buffer
                self.last_modification[path] = current_mtime
                
                # Determine what changed
                filename = os.path.basename(path)
                if path.endswith('.py'):
                    file_type = "Python source"
                    icon = "🐍"
                elif path.endswith('.ini'):
                    file_type = "config"
                    icon = "⚙️"
                else:
                    file_type = "file"
                    icon = "📄"
                    
                # Show notification
                self.lbl_status.setText(
                    f"<span style='color:#ed8936'>{icon} {file_type} changed: {filename}</span>"
                )
                self.ready_label.setText(f"{icon} Detected change in {filename}")
                
                # Start debounced reload
                if not self.reload_timer.isActive():
                    self.reload_timer.start()
        except Exception as e:
            print(f"Error checking file modification: {e}")
            
    def reenable_file_watching(self, path):
        """Re-add a file to the watcher after it was temporarily removed."""
        if os.path.exists(path) and self.auto_reload_check.isChecked():
            try:
                self.file_watcher.addPath(path)
                self.last_modification[path] = os.path.getmtime(path)
            except:
                pass
                
    def debounced_reload(self):
        """Perform reload after debounce period."""
        if self.auto_reload_check.isChecked() and self.current_source and not self.is_reloading:
            self.lbl_status.setText(
                f"<span style='color:#4299e1'>🔄 Auto-reloading source...</span>"
            )
            self.is_reloading = True
            
            # Temporarily disable file watching to prevent recursion
            self.disable_file_watching()
            
            # Schedule the reload
            QTimer.singleShot(500, self.perform_auto_reload)
            
    def perform_auto_reload(self):
        """Perform the actual auto-reload."""
        try:
            # Clear current widget
            self.renderer.clear()
            
            # Force Python to release module references
            if self.current_source:
                module_name = self.current_source.stem
                if module_name in sys.modules:
                    del sys.modules[module_name]
                    
            # Reload the source
            self.start_validation(self.current_source)
            
        except Exception as e:
            self.lbl_status.setText(f"<span style='color:#f56565'>Auto-reload failed: {str(e)}</span>")
        finally:
            self.is_reloading = False
            
            # Re-enable file watching after a delay
            if self.auto_reload_check.isChecked():
                QTimer.singleShot(2000, self.enable_file_watching)
                
    def reload_source(self):
        """Manual reload of the current source."""
        if self.current_source:
            # Temporarily disable file watching to prevent interference
            was_watching = self.auto_reload_check.isChecked()
            if was_watching:
                self.disable_file_watching()
                
            self.start_validation(self.current_source)
            
            # Re-enable if it was enabled
            if was_watching:
                QTimer.singleShot(2000, self.enable_file_watching)
                
    # ==================== UTILITY FUNCTIONS ====================
    
    def toggle_renderer(self):
        """Toggle renderer visibility."""
        self.renderer.setVisible(not self.renderer.isVisible())
        
    def toggle_detach_renderer(self):
        """Toggle renderer detached state."""
        self.renderer.toggle_detached()
        
    def toggle_theme(self):
        """Toggle between dark and light themes (placeholder)."""
        # This is a placeholder - you can extend this to switch between themes
        reply = QMessageBox.question(
            self, 
            "Toggle Theme", 
            "Switch to light theme?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Light theme would be implemented here
            self.lbl_status.setText("<span style='color:#4299e1'>Light theme selected (not implemented)</span>")
            
    def reset_layout(self):
        """Reset the window layout to default."""
        # Reset dock widget
        self.removeDockWidget(self.renderer)
        self.renderer.deleteLater()
        
        # Create new renderer
        self.renderer = DetachableRenderer(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.renderer)
        
        # Reset main window
        self.setGeometry(100, 100, 1400, 900)
        
        self.lbl_status.setText("<span style='color:#48bb78'>Layout reset</span>")
        
    def closeEvent(self, event):
        """Handle application close event."""
        # Save window state
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("window/state", self.saveState())
        
        # Clean up
        self.disable_file_watching()
        self.reload_timer.stop()
        self.memory_timer.stop()
        
        # Clean up background thread
        if self.validator_thread and self.validator_thread.isRunning():
            self.validator_thread.terminate()
            self.validator_thread.wait()
            
        event.accept()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    
    # Set application style and properties
    app.setApplicationName("Dynamic Source Loader")
    app.setOrganizationName("DeveloperTools")
    app.setApplicationDisplayName("Dynamic Source Loader Host")
    
    # Set application-wide font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()