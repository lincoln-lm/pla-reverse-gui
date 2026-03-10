"""Preferences dialog for default research levels and other search preferences"""

import numpy as np

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox,
    QTableWidget, QTableWidgetItem, QComboBox, QHeaderView,
    QPushButton, QAbstractItemView, QWidget, QLabel,
    QRadioButton, QButtonGroup
)
from qtpy.QtCore import QSettings, Qt
from .util import get_name_en


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 600)  # Increased width a bit

        # Load settings
        self.settings = QSettings("PLAReverseGUI", "Settings")
        self.shiny_charm = self.settings.value("shinyCharm", False, bool)
        self.always_shiny = self.settings.value("alwaysSearchShiny", False, bool)
        self.shiny_type = self.settings.value("shinyType", 2, int)  # 0=Star,1=Square,2=Any
        self.always_alpha = self.settings.value("alwaysSearchAlpha", False, bool)

        # Main layout
        layout = QVBoxLayout(self)

        # Shiny search checkbox
        self.shiny_search_check = QCheckBox("Always search for shiny Pokemon")
        self.shiny_search_check.setChecked(self.always_shiny)
        self.shiny_search_check.toggled.connect(self.on_shiny_search_toggled)
        layout.addWidget(self.shiny_search_check)

        # Shiny type options (indented)
        shiny_type_widget = QWidget()
        shiny_type_layout = QHBoxLayout(shiny_type_widget)
        shiny_type_layout.setContentsMargins(20, 0, 0, 0)  # indent

        self.shiny_star_radio = QRadioButton("Star")
        self.shiny_square_radio = QRadioButton("Square")
        self.shiny_any_radio = QRadioButton("Any")

        self.shiny_type_group = QButtonGroup(self)
        self.shiny_type_group.addButton(self.shiny_star_radio, 0)
        self.shiny_type_group.addButton(self.shiny_square_radio, 1)
        self.shiny_type_group.addButton(self.shiny_any_radio, 2)

        # Set saved type
        if self.shiny_type == 0:
            self.shiny_star_radio.setChecked(True)
        elif self.shiny_type == 1:
            self.shiny_square_radio.setChecked(True)
        else:
            self.shiny_any_radio.setChecked(True)

        # Enable/disable based on always_shiny
        self.shiny_star_radio.setEnabled(self.always_shiny)
        self.shiny_square_radio.setEnabled(self.always_shiny)
        self.shiny_any_radio.setEnabled(self.always_shiny)

        shiny_type_layout.addWidget(self.shiny_star_radio)
        shiny_type_layout.addWidget(self.shiny_square_radio)
        shiny_type_layout.addWidget(self.shiny_any_radio)
        shiny_type_layout.addStretch()
        layout.addWidget(shiny_type_widget)

        # Alpha search checkbox
        self.alpha_search_check = QCheckBox("Always search for alpha Pokemon")
        self.alpha_search_check.setChecked(self.always_alpha)
        layout.addWidget(self.alpha_search_check)
        
        # Bottom row: Shiny charm + "Change all to"
        bottom_row = QHBoxLayout()
        self.charm_check = QCheckBox("Shiny Charm")
        self.charm_check.setChecked(self.shiny_charm)
        self.charm_check.toggled.connect(self.on_charm_toggled)
        bottom_row.addWidget(self.charm_check)

        bottom_row.addStretch()

        bottom_row.addWidget(QLabel("Change all to:"))
        self.change_all_combo = QComboBox()
        self.change_all_combo.addItems(["Base Research", "Research Level 10", "Perfect Research"])
        self.change_all_combo.currentIndexChanged.connect(self.change_all_research_level)
        bottom_row.addWidget(self.change_all_combo)

        layout.addLayout(bottom_row)

        # Table for species research levels
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Species", "Research Level"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 150)  # Fixed width for dropdown column
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        # Populate table with all species
        self.populate_species()

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # Initial update of change_all_combo based on charm state
        self.update_change_all_combo()

    def populate_species(self):
        # All species that appear as wild encounters in Pokémon Legends: Arceus
        # (National Pokédex numbers, excluding forms)
        hisui_species = [
            25, 26, 35, 36, 37, 38, 41, 42, 46, 47, 54, 55, 58, 59, 63, 64, 65, 66,
            67, 68, 72, 73, 74, 75, 76, 77, 78, 81, 82, 92, 93, 94, 95, 100, 101,
            108, 111, 112, 113, 114, 122, 123, 125, 126, 129, 130, 133, 134, 135,
            136, 137, 143, 155, 156, 157, 169, 172, 173, 175, 176, 185, 190, 193,
            196, 197, 198, 200, 201, 207, 208, 211, 212, 214, 215, 216, 217, 220,
            221, 223, 224, 226, 233, 234, 239, 240, 242, 265, 266, 267, 268, 269,
            280, 281, 282, 299, 315, 339, 340, 355, 356, 358, 361, 362, 363, 364,
            365, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399,
            400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413,
            414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427,
            428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441,
            442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455,
            456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467, 468, 469,
            470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483,
            484, 485, 486, 487, 488, 489, 490, 492, 493, 501, 502, 503, 548, 549,
            550, 570, 571, 627, 628, 641, 642, 645, 700, 704, 705, 706, 712, 713,
            722, 723, 724, 899, 900, 901, 902, 903, 904, 905,
        ]
        # Sort by name for readability
        sorted_species = sorted(hisui_species, key=lambda s: get_name_en(s, None))

        self.table.setRowCount(len(sorted_species))
        for row, species in enumerate(sorted_species):
            name_item = QTableWidgetItem(get_name_en(species, None))
            name_item.setData(Qt.UserRole, species)
            self.table.setItem(row, 0, name_item)

            combo = QComboBox()
            combo.addItems(["Base Research", "Research Level 10", "Perfect Research"])
            saved_level = self.settings.value(f"species/{species}/researchLevel", 0, int)
            combo.setCurrentIndex(saved_level)
            self.table.setCellWidget(row, 1, combo)

        # If the charm was saved as True, ensure no species is still at Base Research
        if self.shiny_charm:
            self.apply_charm_rule()

    def apply_charm_rule(self):
        """For each species, if it's Base Research, set to Research Level 10."""
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 1)
            if combo and combo.currentIndex() == 0:
                combo.setCurrentIndex(1)   # Base -> Level 10

    def update_change_all_combo(self):
        """Add or remove 'Base Research' from the change-all dropdown based on charm state."""
        current_index = self.change_all_combo.currentIndex()
        current_text = self.change_all_combo.currentText()
        self.change_all_combo.clear()
        if self.charm_check.isChecked():
            self.change_all_combo.addItems(["Research Level 10", "Perfect Research"])
        else:
            self.change_all_combo.addItems(["Base Research", "Research Level 10", "Perfect Research"])
        # Try to restore the previous selection if possible
        index = self.change_all_combo.findText(current_text)
        if index >= 0:
            self.change_all_combo.setCurrentIndex(index)
        else:
            self.change_all_combo.setCurrentIndex(0)

    def change_all_research_level(self, index):
        """Set all species combos to the selected research level."""
        # Map the dropdown index to the actual research level index
        if self.charm_check.isChecked():
            # Items: "Research Level 10" (index 0), "Perfect Research" (index 1)
            # Map to: 1 = Level 10, 2 = Perfect
            target_level = index + 1
        else:
            # Items: "Base Research" (0), "Research Level 10" (1), "Perfect Research" (2)
            target_level = index
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 1)
            if combo:
                combo.setCurrentIndex(target_level)

    def on_charm_toggled(self, checked):
        """When charm is checked, upgrade any Base Research to Level 10 and update dropdown."""
        if checked:
            self.apply_charm_rule()
        self.update_change_all_combo()

    def on_shiny_search_toggled(self, checked):
        """Enable/disable shiny type radio buttons."""
        self.shiny_star_radio.setEnabled(checked)
        self.shiny_square_radio.setEnabled(checked)
        self.shiny_any_radio.setEnabled(checked)

    def save_settings(self):
        """Write settings to QSettings and accept"""
        self.settings.setValue("shinyCharm", self.charm_check.isChecked())
        self.settings.setValue("alwaysSearchShiny", self.shiny_search_check.isChecked())
        self.settings.setValue("shinyType", self.shiny_type_group.checkedId())
        self.settings.setValue("alwaysSearchAlpha", self.alpha_search_check.isChecked())

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None:
                continue
            species = item.data(Qt.UserRole)
            combo = self.table.cellWidget(row, 1)
            if combo:
                level = combo.currentIndex()
                self.settings.setValue(f"species/{species}/researchLevel", level)
        self.accept()
