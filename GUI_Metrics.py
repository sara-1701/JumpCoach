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
            "total_arm_movement",
        ]
        self.initialize_metrics_table()

    def initialize_metrics_table(self):
        self.layout = QVBoxLayout(self)

        self.title_label = QLabel("Jump Metrics")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 27px; font-family: 'Roboto';")
        self.layout.addWidget(self.title_label)

        self.metrics_table = QTableWidget()
        self.layout.addWidget(self.metrics_table)

        self.metrics_table.setColumnCount(4)
        self.metrics_table.setRowCount(0)
        self.metrics_table.setHorizontalHeaderLabels(
            ["Metric", "Selected Jump", "PB/Prev. PB", "% Change"]
        )
        self.metrics_table.horizontalHeader().setVisible(True)
        self.metrics_table.verticalHeader().setVisible(False)

        self.metrics_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.metrics_table.setSelectionMode(QTableWidget.NoSelection)
        self.metrics_table.setFocusPolicy(Qt.NoFocus)

        self.metrics_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Interactive
        )
        self.metrics_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.metrics_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )
        self.metrics_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Stretch
        )

        self.metrics_table.setColumnWidth(0, 250)

        self.metrics_table.setStyleSheet(
            f"""
            QTableWidget {{
                color: {self.color_palette['black']};
                background-color: {self.color_palette['white']};
                font-size: 16px;
            }}
            QHeaderView::section {{
                background-color: {self.color_palette['accent_color']};
                color: {self.color_palette['black']};
                font-size: 24px;
            }}
            """
        )

    def update_metrics_table(self, jump_idx, *_):
        self.curr_jump_idx = jump_idx
        jump = self.jumps[jump_idx]

        feedback_metrics = getattr(jump, "feedback_metrics", [])
        pb_index = getattr(jump, "pb_index", None)
        second_pb_index = getattr(jump, "second_pb_index", None)

        if pb_index is None:
            comparison_jump_idx = None
            comparison_label = "N/A"
        elif jump_idx == pb_index:
            comparison_jump_idx = second_pb_index
            comparison_label = (
                f"Prev PB (#{second_pb_index + 1})"
                if second_pb_index is not None
                else "N/A"
            )
        else:
            comparison_jump_idx = pb_index
            comparison_label = f"PB (#{pb_index + 1})"

        selected_jump = jump.metrics

        if comparison_jump_idx is None or comparison_jump_idx >= len(self.jumps):
            self.metrics_table.setRowCount(0)
            key_metrics_data = [key for key in self.key_metrics if key in selected_jump]
            other_metrics_data = [
                key
                for key in sorted(selected_jump.keys())
                if key not in self.key_metrics
            ]
            all_metrics = key_metrics_data + other_metrics_data

            for row_idx, key in enumerate(all_metrics):
                self.metrics_table.insertRow(row_idx)

                metric_item = QTableWidgetItem(key)
                metric_item.setTextAlignment(Qt.AlignCenter)
                if key in self.key_metrics or key in feedback_metrics:
                    metric_item.setFont(self.get_bold_font())
                self.metrics_table.setItem(row_idx, 0, metric_item)

                selected_value = selected_jump.get(key, "N/A")
                selected_item = self.create_table_item(
                    selected_value,
                    bold=(key in self.key_metrics or key in feedback_metrics),
                )
                self.metrics_table.setItem(row_idx, 1, selected_item)

                for col_idx in range(2, 4):
                    na_item = QTableWidgetItem("N/A")
                    na_item.setTextAlignment(Qt.AlignCenter)
                    self.metrics_table.setItem(row_idx, col_idx, na_item)

            self.metrics_table.setHorizontalHeaderLabels(
                ["Metric", f"Jump #{jump_idx + 1}", "N/A", "N/A"]
            )
            return

        comparison_jump = self.jumps[comparison_jump_idx].metrics
        self.metrics_table.setRowCount(0)

        key_metrics_data = [key for key in self.key_metrics if key in selected_jump]
        other_metrics_data = [
            key
            for key in sorted(set(selected_jump.keys()).union(comparison_jump.keys()))
            if key not in self.key_metrics
        ]
        all_metrics = key_metrics_data + other_metrics_data

        for row_idx, key in enumerate(all_metrics):
            self.metrics_table.insertRow(row_idx)

            is_feedback_metric = key in feedback_metrics
            is_key_metric = key in self.key_metrics

            metric_item = QTableWidgetItem(key)
            metric_item.setTextAlignment(Qt.AlignCenter)
            if is_key_metric:
                metric_item.setFont(self.get_bold_font())
            if is_feedback_metric:
                metric_item.setBackground(QColor("#ffffe0"))
            self.metrics_table.setItem(row_idx, 0, metric_item)

            selected_value = selected_jump.get(key, "N/A")
            selected_item = self.create_table_item(selected_value, bold=is_key_metric)
            if is_feedback_metric:
                selected_item.setBackground(QColor("#ffffe0"))
            self.metrics_table.setItem(row_idx, 1, selected_item)

            comparison_value = comparison_jump.get(key, "N/A")
            comparison_item = self.create_table_item(
                comparison_value, bold=is_key_metric
            )
            if is_feedback_metric:
                comparison_item.setBackground(QColor("#ffffe0"))
            self.metrics_table.setItem(row_idx, 2, comparison_item)

            if isinstance(selected_value, (int, float)) and isinstance(
                comparison_value, (int, float)
            ):
                if comparison_value != 0:
                    percentage_change = (
                        (selected_value - comparison_value) / comparison_value
                    ) * 100
                    percentage_text = f"{percentage_change:+.2f}%"
                else:
                    percentage_text = "∞"
            else:
                percentage_text = "N/A"

            percentage_item = QTableWidgetItem(percentage_text)
            percentage_item.setTextAlignment(Qt.AlignCenter)
            if is_key_metric:
                percentage_item.setFont(self.get_bold_font())
            if is_feedback_metric:
                percentage_item.setBackground(QColor("#ffffe0"))
            self.metrics_table.setItem(row_idx, 3, percentage_item)

        self.metrics_table.setHorizontalHeaderLabels(
            ["Metric", f"Jump #{jump_idx + 1}", comparison_label, "% Change"]
        )

    def create_table_item(self, value, bold=False):
        item = QTableWidgetItem(
            f"{value:.4f}" if isinstance(value, float) else str(value)
        )
        item.setTextAlignment(Qt.AlignCenter)
        if bold:
            item.setFont(self.get_bold_font())
        return item

    def get_bold_font(self):
        font = self.font()
        font.setBold(True)
        return font
