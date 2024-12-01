from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt5.QtCore import Qt


class GUIMetrics(QWidget):
    def __init__(self, color_palette, jumps):
        super().__init__()
        self.color_palette = color_palette
        self.jumps = jumps
        self.curr_jump_idx = 0  # Index of the currently selected jump

        # Apply styling
        self.setStyleSheet(
            f"""
            background-color: {color_palette['block_bg']};
            padding: 20px;
            border: 1px solid {color_palette['grey']};
            border-radius: 10px;
            """
        )

        # Main layout for the metrics widget
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Title for the metrics panel
        self.title_label = QLabel("Metrics")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 28px; font-family: 'Roboto';")
        self.layout.addWidget(self.title_label)

        # Table to display metrics
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.metrics_table.verticalHeader().setVisible(False)
        self.metrics_table.setStyleSheet(
            f"""
            QTableWidget {{
                font-size: 18px;
                font-family: 'Roboto', sans-serif;
                color: {color_palette['black']};
                border: 1px solid {color_palette['grey']};
                gridline-color: {color_palette['grey']};
                background-color: {color_palette['white']};
            }}
            QHeaderView::section {{
                background-color: {color_palette['block_bg']};
                color: {color_palette['black']};
                font-size: 18px;
                font-weight: bold;
                border: none;
            }}
            QTableWidget::item {{
                border: none;
                border-bottom: 1px solid {color_palette['grey']};
            }}
            """
        )
        self.metrics_table.setAlternatingRowColors(True)
        self.metrics_table.setShowGrid(True)
        self.layout.addWidget(self.metrics_table)

        # Initialize the table with the first jump's metrics
        self.update_metrics_table(0, 0)

    def update_metrics_table(self, jump_idx, max_jump_idx):
        print(f"Jump idx in metrics table: {jump_idx}")
        """Update the metrics table to show the metrics of the selected jump."""
        self.curr_jump_idx = jump_idx
        if 0 <= jump_idx < len(self.jumps):
            jump = self.jumps[jump_idx]
            metrics = jump.metrics  # Assuming this is a dictionary

            # Clear existing table content
            self.metrics_table.setRowCount(0)

            # Populate the table with the metrics
            for row_idx, (key, value) in enumerate(metrics.items()):
                self.metrics_table.insertRow(row_idx)
                metric_item = QTableWidgetItem(key)
                value_item = QTableWidgetItem(str(value))

                # Align text to center
                metric_item.setTextAlignment(Qt.AlignCenter)
                value_item.setTextAlignment(Qt.AlignCenter)

                self.metrics_table.setItem(row_idx, 0, metric_item)
                self.metrics_table.setItem(row_idx, 1, value_item)
