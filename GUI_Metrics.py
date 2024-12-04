from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
)
from PyQt5.QtCore import Qt


class GUIMetrics(QWidget):
    def __init__(self, color_palette, jumps):
        super().__init__()
        self.color_palette = color_palette
        self.jumps = jumps
        self.initialize_metrics_table()

    from PyQt5.QtWidgets import QScrollArea

    def initialize_metrics_table(self):
        # Main layout for the metrics widget
        self.layout = QVBoxLayout(self)

        # Title for the metrics panel
        self.title_label = QLabel("Jump Metrics")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 28px; font-family: 'Roboto';")
        self.layout.addWidget(self.title_label)

        # Table to display metrics
        self.metrics_table = QTableWidget()

        # Wrap the table in a QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.metrics_table)
        self.scroll_area.setWidgetResizable(
            True
        )  # Ensures the table resizes with the scroll area

        self.layout.addWidget(self.scroll_area)

        self.metrics_table.setColumnCount(3)  # Number of columns
        self.metrics_table.setRowCount(1)  # Temporary row count for testing
        self.metrics_table.setHorizontalHeaderLabels(["", "", ""])
        self.metrics_table.horizontalHeader().setVisible(True)
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.metrics_table.verticalHeader().setVisible(False)

        # Ensuring the headers are visible and the table is stretched
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        # Style sheet for the table and header
        self.metrics_table.setStyleSheet(
            f"""
            QTableWidget {{
                color: {self.color_palette['black']};  /* Black text for table entries */
                background-color: {self.color_palette['white']};  /* White background for table entries */
                font-size: 16px;
            }}
            QHeaderView::section {{
                background-color: {self.color_palette['blue']};  /* Green background for header */
                color: {self.color_palette['white']};  /* White text for header */
                font-size: 24px;  /* Font size for header */
                font-weight: bold;
                }}
            """
        )

    def update_metrics_table(self, jump_idx, max_jump_idx):
        """Update the metrics table to show the selected jump and either PB or Previous PB."""
        self.curr_jump_idx = jump_idx

        # Determine Previous PB index if the current jump is the new PB
        prev_pb_idx = None
        if jump_idx == max_jump_idx:
            # Find the highest jump before the current PB
            prev_pb_idx = max(
                (i for i in range(len(self.jumps)) if i != max_jump_idx),
                key=lambda i: self.jumps[i].metrics.get("height", 0),
                default=None,
            )

        # Get metrics for selected jump and PB/Previous PB
        selected_jump = self.jumps[jump_idx].metrics
        pb_jump = (
            self.jumps[prev_pb_idx].metrics
            if jump_idx == max_jump_idx and prev_pb_idx is not None
            else self.jumps[max_jump_idx].metrics
        )

        # Clear the table rows
        self.metrics_table.setRowCount(0)  # Clear existing rows only

        # Populate the table
        for row_idx, key in enumerate(
            sorted(set(selected_jump.keys()).union(pb_jump.keys()))
        ):
            self.metrics_table.insertRow(row_idx)

            # Metric name
            metric_item = QTableWidgetItem(key)
            metric_item.setTextAlignment(Qt.AlignCenter)
            self.metrics_table.setItem(row_idx, 0, metric_item)

            # Selected jump value
            selected_value = selected_jump.get(key, "N/A")
            if isinstance(selected_value, float):
                selected_item = QTableWidgetItem(f"{selected_value:.4f}")
            else:
                selected_item = QTableWidgetItem(str(selected_value))
            selected_item.setTextAlignment(Qt.AlignCenter)
            self.metrics_table.setItem(row_idx, 1, selected_item)

            # PB/Previous PB value
            pb_value = pb_jump.get(key, "N/A")
            if isinstance(pb_value, float):
                pb_item = QTableWidgetItem(f"{pb_value:.4f}")
            else:
                pb_item = QTableWidgetItem(str(pb_value))
            pb_item.setTextAlignment(Qt.AlignCenter)
            self.metrics_table.setItem(row_idx, 2, pb_item)

        # Adjust header labels based on PB status
        current_jump_label = f"Jump #{jump_idx + 1}"
        if jump_idx == max_jump_idx:
            current_jump_label += " (PB)"

        if jump_idx == max_jump_idx and prev_pb_idx is not None:
            pb_label = f"Prev. PB (#{prev_pb_idx + 1})"
        else:
            pb_label = f"Curr. PB (#{max_jump_idx + 1})"

        self.metrics_table.setHorizontalHeaderLabels(
            ["Metric", current_jump_label, pb_label]
        )

        # Adjust column widths
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
