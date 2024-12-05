from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class GUIMetrics(QWidget):
    def __init__(self, color_palette, jumps):
        super().__init__()
        self.color_palette = color_palette
        self.jumps = jumps
        self.key_metrics = [
            "height",
            "airtime",
            "takeoff_knee_bend",
            "landing_impact_jerk",
            "landing_knee_bend",
            "forward_backward_movement",
            "lateral_movement",
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

        self.metrics_table.setColumnCount(4)  # Number of columns
        self.metrics_table.setRowCount(0)  # No rows initially
        self.metrics_table.setHorizontalHeaderLabels(
            ["Metric", "Selected Jump", "PB/Prev. PB", "% Change"]
        )
        self.metrics_table.horizontalHeader().setVisible(True)
        self.metrics_table.verticalHeader().setVisible(False)

        # Prevent selection or editing
        self.metrics_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.metrics_table.setSelectionMode(QTableWidget.NoSelection)
        self.metrics_table.setFocusPolicy(Qt.NoFocus)

        # Set custom column widths
        self.metrics_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Interactive
        )  # Custom width for the first column
        self.metrics_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )  # Dynamic for second column
        self.metrics_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )  # Dynamic for third column
        self.metrics_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Stretch
        )  # Dynamic for fourth column

        # Set the first column width to be twice the size of the other columns
        self.metrics_table.setColumnWidth(0, 250)

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
                color: {self.color_palette['black']};  /* Black text for header */
                font-size: 24px;  /* Font size for header */
            }}
            """
        )

    def update_metrics_table(
        self, jump_idx, max_jump_idx, second_max_jump_idx, feedback_metrics
    ):
        """Update the metrics table to show the selected jump, its comparison, and percentage change."""
        self.curr_jump_idx = jump_idx

        # Check if there's only one jump
        if len(self.jumps) == 1:
            selected_jump = self.jumps[jump_idx].metrics

            # Clear the table rows and set new column count
            self.metrics_table.setRowCount(0)

            # Separate key metrics (at the top) and other metrics
            key_metrics_data = [key for key in self.key_metrics if key in selected_jump]
            other_metrics_data = [
                key
                for key in sorted(selected_jump.keys())
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
                if (
                    key in self.key_metrics or key in feedback_metrics
                ):  # Bold key or feedback metrics
                    metric_item.setFont(self.get_bold_font())
                self.metrics_table.setItem(row_idx, 0, metric_item)

                # Selected jump value
                selected_value = selected_jump.get(key, "N/A")
                selected_item = self.create_table_item(
                    selected_value,
                    bold=(key in self.key_metrics or key in feedback_metrics),
                )
                self.metrics_table.setItem(row_idx, 1, selected_item)

                # Mark comparison and percentage change as "N/A"
                for col_idx in range(2, 4):
                    na_item = QTableWidgetItem("N/A")
                    na_item.setTextAlignment(Qt.AlignCenter)
                    self.metrics_table.setItem(row_idx, col_idx, na_item)

            # Adjust header labels for single jump case
            current_jump_label = f"Jump #{jump_idx + 1}"
            self.metrics_table.setHorizontalHeaderLabels(
                ["Metric", current_jump_label, "N/A", "N/A"]
            )
            return

        # Regular case: More than one jump
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

        # Clear the table rows and set new column count
        self.metrics_table.setRowCount(0)

        # Separate key metrics (at the top) and other metrics
        key_metrics_data = [key for key in self.key_metrics if key in selected_jump]
        other_metrics_data = [
            key
            for key in sorted(set(selected_jump.keys()).union(comparison_jump.keys()))
            if key not in self.key_metrics
        ]

        # Combine key metrics and other metrics
        all_metrics = key_metrics_data + other_metrics_data

        for row_idx, key in enumerate(all_metrics):
            self.metrics_table.insertRow(row_idx)

            # Determine if the row should have a yellow background
            is_feedback_metric = key in feedback_metrics
            is_key_metric = key in self.key_metrics

            # Metric name
            metric_item = QTableWidgetItem(key)
            metric_item.setTextAlignment(Qt.AlignCenter)
            if is_key_metric:  # Bold key metrics
                metric_item.setFont(self.get_bold_font())
            if is_feedback_metric:  # Yellow background for feedback metrics
                metric_item.setBackground(QColor("#ffffe0"))
            self.metrics_table.setItem(row_idx, 0, metric_item)

            # Selected jump value
            selected_value = selected_jump.get(key, "N/A")
            selected_item = self.create_table_item(
                selected_value, bold=is_key_metric  # Bold if key metric
            )
            if is_feedback_metric:  # Yellow background for feedback metrics
                selected_item.setBackground(QColor("#ffffe0"))
            self.metrics_table.setItem(row_idx, 1, selected_item)

            # Comparison jump value
            comparison_value = comparison_jump.get(key, "N/A")
            comparison_item = self.create_table_item(
                comparison_value, bold=is_key_metric  # Bold if key metric
            )
            if is_feedback_metric:  # Yellow background for feedback metrics
                comparison_item.setBackground(QColor("#ffffe0"))
            self.metrics_table.setItem(row_idx, 2, comparison_item)

            # Percentage change
            if isinstance(selected_value, (int, float)) and isinstance(
                comparison_value, (int, float)
            ):
                if comparison_value != 0:
                    percentage_change = (
                        (selected_value - comparison_value) / comparison_value
                    ) * 100
                    percentage_text = f"{percentage_change:+.2f}%"  # Show +/- sign
                else:
                    percentage_text = "∞"  # Infinite change if comparison value is 0
            else:
                percentage_text = "N/A"

            percentage_item = QTableWidgetItem(percentage_text)
            percentage_item.setTextAlignment(Qt.AlignCenter)
            if is_key_metric:  # Bold if key metric
                percentage_item.setFont(self.get_bold_font())
            if is_feedback_metric:  # Yellow background for feedback metrics
                percentage_item.setBackground(QColor("#ffffe0"))
            self.metrics_table.setItem(row_idx, 3, percentage_item)

        # Adjust header labels based on the comparison
        current_jump_label = f"Jump #{jump_idx + 1}"
        self.metrics_table.setHorizontalHeaderLabels(
            ["Metric", current_jump_label, comparison_label, "% Change"]
        )

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
