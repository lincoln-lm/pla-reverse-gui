"""QTableWidget for spawner paths"""

# pylint: disable=no-name-in-module
from qtpy.QtWidgets import (
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QSizePolicy,
    QMenu,
    QAction,
)
from qtpy.QtCore import Qt, QSize, QModelIndex
from qtpy.QtGui import QPainter

# pylint: enable=no-name-in-module
from .path_tracker_window import PathTrackerWindow
from ..util import string_to_path

class MultiIconDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, icon_size=28, spacing=2):
        super().__init__(parent)
        self.icon_size = icon_size
        self.spacing = spacing

    def paint(self, painter, option, index):
        values = index.data(Qt.UserRole)
        if not values or not isinstance(values, list):
            super().paint(painter, option, index)
            return

        parent_table = self.parent()
        if not hasattr(parent_table, 'parent_window'):
            super().paint(painter, option, index)
            return
        parent_window = parent_table.parent_window

        col = index.column()
        if col == 2:   # Weather column
            # If NONE (0) is present, show only the NONE icon
            if 0 in values:
                values_for_icons = [0]
            else:
                values_for_icons = values
            icon_getter = parent_window.get_weather_icon
        elif col == 3: # Time column (no special handling for now)
            values_for_icons = values
            icon_getter = lambda v: parent_window.get_time_icon(v, None)
        else:
            super().paint(painter, option, index)
            return

        # Load icons for the values (sorted for consistency)
        icons = []
        for val in sorted(values_for_icons):
            icon = icon_getter(val)
            if icon and not icon.isNull():
                icons.append(icon)
        if not icons:
            super().paint(painter, option, index)
            return

        # Calculate total width of composite
        total_width = self.icon_size * len(icons) + self.spacing * (len(icons)-1)
        # Center the composite within the cell
        x = option.rect.x() + (option.rect.width() - total_width) // 2
        y = option.rect.y() + (option.rect.height() - self.icon_size) // 2

        # Draw each icon
        for icon in icons:
            pixmap = icon.pixmap(self.icon_size, self.icon_size)
            painter.drawPixmap(x, y, pixmap)
            x += self.icon_size + self.spacing


class ResultTableWidget(QTableWidget):
    """QTableWidget for spawner paths"""

    COLUMNS = (
        ("Advances", 100),
        ("Path", 100),
        ("Weather", 100),
        ("Time", 100),
        ("Species", 100),
        ("Shiny", 80),
        ("Alpha", 80),
        ("Nature", 80),
        ("Ability", 100),
        ("HP", 50),
        ("Atk", 50),
        ("Def", 50),
        ("SpA", 50),
        ("SpD", 50),
        ("Spe", 50),
        ("Gender", 70),
        ("Height", 80),
        ("Weight", 80),
        ("ID", 0),
    )

    def __init__(self):
        super().__init__()

        self.setColumnCount(19)
        self.setHorizontalHeaderLabels([column[0] for column in self.COLUMNS])
        for i, (_, width) in enumerate(self.COLUMNS):
            self.setColumnWidth(i, width)
        self.setColumnHidden(18, True)

        #self.setIconSize(QSize(28, 28))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.verticalHeader().setVisible(False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu_handler)

        # Install custom delegate for Weather and Time columns
        delegate = MultiIconDelegate(self)
        self.setItemDelegateForColumn(2, delegate)
        self.setItemDelegateForColumn(3, delegate)

        self.action_open_path = QAction("Open Path Tracker", self)
        self.action_open_path.triggered.connect(self.open_path_tracker)
        self.min_spawn_count = 0
        self.max_spawn_count = 0
        self.encounter_table = None
        self.seed = 0
        self.weather = None
        self.time = None
        self.spawn_counts = None

    def context_menu_handler(self, pos):
        """Handler for QTableView context manager"""
        menu = QMenu(self)
        menu.addAction(self.action_open_path)
        menu.exec_(self.mapToGlobal(pos))

    def open_path_tracker(self):
        """Handler for opening the path tracker"""
        selected_row = self.item(self.selectedIndexes()[0].row(), 1)
        path_text = selected_row.text()
        if path_text == "N/A":
            return
        spawn_counts = (-1,)
        if self.max_spawn_count == 4:
            pre_path = (1, 1)
        elif self.min_spawn_count != self.max_spawn_count:
            pre_path = (2,)
            spawn_counts = self.spawn_counts
        else:
            pre_path = (self.max_spawn_count,)
        path = string_to_path(path_text)
        path_tracker = PathTrackerWindow(
            self,
            self.encounter_table,
            self.second_wave_encounter_table,
            self.seed,
            pre_path,
            path,
            spawn_counts,
            self.max_spawn_count,
            self.weather,
            self.time,
            self.species_info,
        )
        path_tracker.show()
