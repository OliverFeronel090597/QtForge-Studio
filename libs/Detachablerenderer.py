
from PyQt6.QtCore import (
    Qt
    )
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QDockWidget
)

from typing import Optional

class DetachableRenderer(QDockWidget):
    """Detachable renderer panel that can float as its own window."""
    
    def __init__(self, parent=None):
        super().__init__("Renderer", parent)
        self.setObjectName("DetachableRenderer")
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        
        # Create central widget for the dock
        self.container = QWidget()
        self.container.setObjectName("RendererContainer")
        self.setWidget(self.container)
        
        # Layout for the container
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Header with title and close button
        self.header = QWidget()
        self.header.setObjectName("RendererHeader")
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(10, 5, 10, 5)
        
        self.title_label = QLabel("Renderer")
        self.title_label.setObjectName("RendererTitle")
        self.header_layout.addWidget(self.title_label)
        
        self.header_layout.addStretch()
        
        self.detach_button = QPushButton("⤢")
        self.detach_button.setObjectName("DetachButton")
        self.detach_button.setFixedSize(24, 24)
        self.detach_button.setToolTip("Detach/Attach Renderer")
        self.header_layout.addWidget(self.detach_button)
        
        self.layout.addWidget(self.header)
        
        # Content area
        self.content_widget = QWidget()
        self.content_widget.setObjectName("RendererContent")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder
        self.placeholder = QLabel("No source loaded")
        self.placeholder.setObjectName("RendererPlaceholder")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.placeholder)
        
        self.layout.addWidget(self.content_widget, 1)
        
        # Current hosted widget
        self.current_widget: Optional[QWidget] = None
        
        # Connect signals
        self.detach_button.clicked.connect(self.toggle_detached)
        self.topLevelChanged.connect(self.on_top_level_changed)
        
        # Apply initial style
        self.apply_style()
        
    def apply_style(self):
        """Apply renderer-specific styling."""
        self.setStyleSheet("""
            /* This style only applies to the renderer dock widget */
            QDockWidget#DetachableRenderer {
                border: 2px solid #4a5568;
                border-radius: 6px;
                titlebar-close-icon: url(close.png);
                titlebar-normal-icon: url(float.png);
            }
            
            QWidget#RendererContainer {
                background-color: #ffffff;
            }
            
            QWidget#RendererHeader {
                background-color: #2d3748;
                border-bottom: 1px solid #4a5568;
            }
            
            QLabel#RendererTitle {
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
            }
            
            QPushButton#DetachButton {
                background-color: #4a5568;
                color: #ffffff;
                border: none;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            
            QPushButton#DetachButton:hover {
                background-color: #5a6578;
            }
            
            QPushButton#DetachButton:pressed {
                background-color: #3a4558;
            }
            
            QWidget#RendererContent {
                background-color: #ffffff;
            }
            
            QLabel#RendererPlaceholder {
                color: #a0aec0;
                font-size: 14px;
                padding: 60px;
                background-color: #f7fafc;
                border: 2px dashed #cbd5e0;
                border-radius: 4px;
                margin: 10px;
            }
        """)
        
    def toggle_detached(self):
        """Toggle between docked and detached state."""
        if self.isFloating():
            # Re-dock
            self.setFloating(False)
            self.detach_button.setText("⤢")
        else:
            # Detach
            self.setFloating(True)
            self.detach_button.setText("⊡")
            # Set reasonable size when detached
            self.resize(800, 600)
            
    def on_top_level_changed(self, floating):
        """Handle floating state change."""
        if floating:
            self.detach_button.setText("⊡")
            self.setWindowTitle("Renderer - Detached")
        else:
            self.detach_button.setText("⤢")
            self.setWindowTitle("Renderer")
            
    def host_widget(self, widget: QWidget):
        """Host an external widget in the renderer."""
        # Clear previous widget
        if self.current_widget:
            self.current_widget.setParent(None)
            self.content_layout.removeWidget(self.current_widget)
            self.current_widget.deleteLater()
            
        # Add new widget
        self.placeholder.hide()
        self.current_widget = widget
        self.content_layout.addWidget(widget)
        
        # Update title if widget has window title
        if hasattr(widget, 'windowTitle') and widget.windowTitle():
            title = widget.windowTitle()
            self.title_label.setText(f"Renderer: {title}")
            if self.isFloating():
                self.setWindowTitle(f"Renderer - {title}")
                
    def clear(self):
        """Clear the hosted widget."""
        if self.current_widget:
            self.current_widget.setParent(None)
            self.content_layout.removeWidget(self.current_widget)
            self.current_widget.deleteLater()
            self.current_widget = None
            
        self.placeholder.show()
        self.title_label.setText("Renderer")
        if self.isFloating():
            self.setWindowTitle("Renderer - Detached")