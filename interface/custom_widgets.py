# interface/custom_widgets.py

from PyQt5.QtWidgets import QComboBox, QSpinBox, QDoubleSpinBox, QSlider
from PyQt5.QtCore import Qt

class NoScrollComboBox(QComboBox):
    """
    Uma subclasse de QComboBox que ignora o evento de rolagem do mouse.
    """
    def wheelEvent(self, event):
        event.ignore()

class NoScrollSpinBox(QSpinBox):
    """
    Uma subclasse de QSpinBox que ignora o evento de rolagem do mouse.
    """
    def wheelEvent(self, event):
        event.ignore()

class NoScrollDoubleSpinBox(QDoubleSpinBox):
    """
    Uma subclasse de QDoubleSpinBox que ignora o evento de rolagem do mouse.
    """
    def wheelEvent(self, event):
        event.ignore()

class NoScrollSlider(QSlider):
    """
    Uma subclasse de QSlider que ignora o evento de rolagem do mouse.
    """
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, event):
        event.ignore()
