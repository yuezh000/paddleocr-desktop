APP_STYLESHEET = """
QMainWindow, QWidget#appRoot {
    background: #f5f8fc;
    color: #172b4d;
    font-family: "SF Pro Text", "Segoe UI", "Microsoft YaHei UI", sans-serif;
    font-size: 14px;
}

QToolBar#actionBar {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #dfe7f2;
    padding: 8px 18px;
    spacing: 8px;
}
QToolBar#actionBar QToolButton {
    background: #ffffff;
    color: #244361;
    border: 1px solid #cbd8e8;
    border-radius: 7px;
    min-height: 32px;
    padding: 0 13px;
    font-weight: 500;
}
QToolBar#actionBar QToolButton::menu-indicator { image: none; }
QToolBar#actionBar QToolButton:hover {
    color: #1261c9;
    border-color: #77a9e8;
    background: #f1f7ff;
}
QToolBar#actionBar QToolButton:pressed { background: #e4f0ff; }
QToolBar#actionBar QToolButton:disabled {
    color: #9aa9ba;
    background: #f7f9fc;
    border-color: #e3e9f1;
}

QFrame#hero {
    background: #0b63ce;
    border: none;
    border-radius: 12px;
}
QLabel#heroTitle {
    color: #ffffff;
    font-size: 24px;
    font-weight: 700;
}
QLabel#heroSubtitle { color: #dbeaff; font-size: 13px; }
QLabel#engineBadge {
    color: #e8f2ff;
    background: #2477d8;
    border: 1px solid #5595e1;
    border-radius: 12px;
    padding: 5px 11px;
    font-size: 12px;
    font-weight: 600;
}

QFrame[class="card"] {
    background: #ffffff;
    border: 1px solid #dfe7f2;
    border-radius: 10px;
}
QLabel[class="panelTitle"] {
    color: #1d3551;
    font-size: 15px;
    font-weight: 650;
}
QLabel#fileLabel {
    color: #6a7f95;
    font-size: 12px;
    padding: 0;
}

QGraphicsView#imageCanvas {
    background: #eef3f9;
    border: none;
    border-radius: 7px;
}

QTableWidget#resultTable {
    background: #ffffff;
    alternate-background-color: #f7faff;
    border: none;
    gridline-color: transparent;
    selection-background-color: #dcecff;
    selection-color: #113d72;
    outline: none;
}
QTableWidget#resultTable::item {
    border: none;
    border-bottom: 1px solid #edf1f6;
    padding: 7px 8px;
}
QWidget#resultContent { background: transparent; }
QFrame#resultLoading {
    background: rgba(247, 251, 255, 242);
    border: none;
    border-radius: 9px;
}
QLabel#loadingTitle {
    color: #15395f;
    font-size: 19px;
    font-weight: 700;
}
QLabel#loadingMessage {
    color: #66809a;
    font-size: 13px;
    min-width: 280px;
    max-width: 390px;
}
QHeaderView::section {
    color: #58708b;
    background: #f3f7fb;
    border: none;
    border-bottom: 1px solid #dfe7f2;
    padding: 9px 8px;
    font-size: 12px;
    font-weight: 650;
}

QSplitter::handle { background: transparent; width: 12px; }
QStatusBar {
    color: #526b84;
    background: #ffffff;
    border-top: 1px solid #dfe7f2;
    min-height: 28px;
}
QProgressBar {
    color: transparent;
    background: #e4edf7;
    border: none;
    border-radius: 3px;
    max-height: 6px;
}
QProgressBar::chunk { background: #1671d9; border-radius: 3px; }

QMessageBox { background: #ffffff; }
QMessageBox QPushButton {
    color: #174b84;
    background: #edf5ff;
    border: 1px solid #b9d4f3;
    border-radius: 6px;
    min-height: 30px;
    padding: 0 12px;
}
QMessageBox QPushButton:hover { background: #dcecff; }
"""
