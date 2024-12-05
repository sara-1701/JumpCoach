from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt


class GUIMetrics(QWidget):
    def __init__(self, color_palette, jumps):
        super().__init__()
        self.color_palette = color_palette
        self.jumps = jumps
        self.key_metrics = [
            "height",
            "airtime",
            "takeoff_avg_vertical_arm_speed",
        ]  # Hardcoded key metrics
        self.initialize_metrics_table()

    def initialize_metrics_table(self):
        # Main layout for the metrics widget
        self.layout = QVBoxLayout(self)

        # Title for the metrics panel
        self.title_label = QLabel("Jump Metrics")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 27px; font-family: 'Roboto';")
        self.layout.addWidget(self.title_label)

        # Table to display metrics
        self.metrics_table = QTableWidget()
        self.layout.addWidget(self.metrics_table)

        self.metrics_table.setColumnCount(3)  # Number of columns
        self.metrics_table.setRowCount(1)  # Temporary row count for testing
        self.metrics_table.setHorizontalHeaderLabels(
            ["Metric", "Selected Jump", "PB/Prev. PB"]
        )
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
                background-color: {self.color_palette['accent_color']};  /* Yellow background for header */
                color: {self.color_palette['black']};  /* White text for header */
                font-size: 24px;  /* Font size for header */
            }}
            """
        )

    def update_metrics_table(self, jump_idx, max_jump_idx, second_max_jump_idx):
        """Update the metrics table to show the selected jump and its relevant comparison."""
        self.curr_jump_idx = jump_idx

        # Determine the comparison jump based on whether the current jump is the PB
        if jump_idx == max_jump_idx:
            comparison_jump_idx = (
                second_max_jump_idx  # Compare PB to the second-highest jump
            )
            comparison_label = f"Prev PB (#{second_max_jump_idx + 1})"
        else:
            comparison_jump_idx = max_jump_idx  # Compare to the highest jump
            comparison_label = f"PB (#{max_jump_idx + 1})"

        # Get metrics for the selected jump and comparison jump
        selected_jump = self.jumps[jump_idx].metrics
        comparison_jump = self.jumps[comparison_jump_idx].metrics

        # Clear the table rows
        self.metrics_table.setRowCount(0)  # Clear existing rows only

        # Separate key metrics (at the top) and other metrics
        key_metrics_data = [key for key in self.key_metrics if key in selected_jump]
        other_metrics_data = [
            key
            for key in sorted(set(selected_jump.keys()).union(comparison_jump.keys()))
            if key not in self.key_metrics
        ]

        # Combine key metrics and other metrics
        all_metrics = key_metrics_data + other_metrics_data

        # Populate the table
        for row_idx, key in enumerate(all_metrics):
            self.metrics_table.insertRow(row_idx)

            # Metric name
            metric_item = QTableWidgetItem(key)
            metric_item.setTextAlignment(Qt.AlignCenter)
            if key in self.key_metrics:  # Bold the key metrics
                metric_item.setFont(self.get_bold_font())
            self.metrics_table.setItem(row_idx, 0, metric_item)

            # Selected jump value
            selected_value = selected_jump.get(key, "N/A")
            selected_item = self.create_table_item(
                selected_value, bold=(key in self.key_metrics)
            )
            self.metrics_table.setItem(row_idx, 1, selected_item)

            # Comparison jump value
            comparison_value = comparison_jump.get(key, "N/A")
            comparison_item = self.create_table_item(
                comparison_value, bold=(key in self.key_metrics)
            )
            self.metrics_table.setItem(row_idx, 2, comparison_item)

        # Adjust header labels based on the comparison
        current_jump_label = f"Jump #{jump_idx + 1}"
        self.metrics_table.setHorizontalHeaderLabels(
            ["Metric", current_jump_label, comparison_label]
        )

        # Adjust column widths
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def create_table_item(self, value, bold=False):
        """Create a table item with optional bold font."""
        item = QTableWidgetItem(
            f"{value:.4f}" if isinstance(value, float) else str(value)
        )
        item.setTextAlignment(Qt.AlignCenter)
        if bold:
            item.setFont(self.get_bold_font())
        return item

    def get_bold_font(self):
        """Return a bold font for key metrics."""
        font = self.font()
        font.setBold(True)
        return font
