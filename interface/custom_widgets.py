# interface/custom_widgets.py

from PyQt5.QtWidgets import QComboBox, QSpinBox, QDoubleSpinBox

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