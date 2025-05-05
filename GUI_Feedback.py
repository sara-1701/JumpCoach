from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
import numpy as np
import random


class GUIFeedbackBox(QWidget):
    """Generate concise, actionable feedback after each jump.

    Logic
    -----
    * Compare the current jump with the PB **up to that jump**.
    * If it *is* the PB → single congratulation line; no coaching cue.
    * Otherwise select ONE metric with the largest absolute % deviation from the PB.
        – Take‑off knee bend  (higher is better)
        – Arm swing          (higher is better)
        – Landing impact     (lower is better)
    * Give a cue telling the athlete to move **toward** the PB value.
    * Cues are suppressed when |deviation| < 5 % ("keep consistent").
    """

    # ----------------------------- CONFIG --------------------------------
    _METRICS = {
        "takeoff_knee_bend": {
            "name": "knee bend",
            "pref": "higher",  # more is better
            "more": {
                "mild": "Bend your knees a little more during take‑off for extra power.",
                "med": "Bend your knees more on take‑off to generate force.",
                "large": "Drop deeper into your knees pre‑take‑off for max explosiveness.",
            },
            "less": {
                "mild": "Bend your knees slightly less to avoid over‑squatting.",
                "med": "Don’t over‑bend – come up a bit higher before take‑off.",
                "large": "Way too deep – bend much less to stay explosive.",
            },
        },
        "total_arm_movement": {
            "name": "arm swing",
            "pref": "higher",  # more is better
            "more": {
                "mild": "Add a bit more arm swing to boost lift.",
                "med": "Drive your arms faster to gain extra height.",
                "large": "Really whip your arms upward for maximum propulsion.",
            },
            "less": {
                "mild": "Tame the arm swing slightly for better coordination.",
                "med": "Reduce arm swing to stay controlled.",
                "large": "Your arms are excessive – swing much less for efficiency.",
            },
        },
        "landing_impact_jerk": {
            "name": "landing impact",
            "pref": "lower",  # less is better
            "more": {
                "mild": "Soften your landing a bit by bending knees and ankles.",
                "med": "Focus on cushioning the landing to reduce impact.",
                "large": "Land MUCH softer – absorb with deeper knee flexion.",
            },
            "less": {
                "mild": "Good – landing impact is lower. Keep it soft!",
                "med": "Nice! Landing impact has reduced.",
                "large": "Great! Landing impact is MUCH softer.",
            },
        },
    }

    _COMPLIMENTS = ["Good jump!", "Great!", "Awesome!", "Strong effort!"]

    # ---------------------------------------------------------------------
    def __init__(self, palette, jumps):
        super().__init__()
        self.palette = palette
        self.jumps = jumps
        self._init_ui()

    # ---------------------- UI SETUP -------------------------------------
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        header = QLabel("Feedback for Next Jump")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(
            f"font-size:27px;font-family:'Roboto';color:{self.palette['plot_fg']};"
        )
        layout.addWidget(header)

        self.label = QLabel("Perform a jump to receive feedback!")
        self.label.setAlignment(Qt.AlignLeft)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(
            f"font-size:24px;font-family:'Roboto';background:{self.palette['white']};"
            f"color:{self.palette['black']};border:5px solid {self.palette['accent_color']};"
            f"border-radius:5px;padding:15px;line-height:1.4;"
        )
        layout.addWidget(self.label)

    # ---------------------- FEEDBACK -------------------------------------
    def update_feedback(self, cur_idx: int, pb_idx: int, _second_idx: int):
        jump = self.jumps[cur_idx]

        # Baseline (first jump ever)
        if pb_idx is None or pb_idx < 0 or len(self.jumps) == 1 or cur_idx == 0:
            return self._finalize(
                jump, "Baseline recorded. No previous jump to compare.", []
            )

        cur_m = jump.metrics
        pb_m = self.jumps[pb_idx].metrics

        # NEW PB – no coaching cue
        if cur_idx == pb_idx:
            msg = "NEW PB! Fantastic jump – see if you can beat it next time!"
            return self._finalize(jump, msg, ["height"])

        # ---------------- HEIGHT RANK LINE ----------------
        rank_line = self._height_rank_line(cur_m.get("height", 0), cur_idx)
        lines = [rank_line]

        # ---------------- TECH CUE ----------------
        chosen, abs_dev, cue = None, 0, None
        for metric, cfg in self._METRICS.items():
            cur_val, pb_val = cur_m.get(metric, np.nan), pb_m.get(metric, np.nan)
            if np.isnan(cur_val) or np.isnan(pb_val) or pb_val == 0:
                continue
            pct = (cur_val - pb_val) / abs(pb_val) * 100  # signed
            if abs(pct) > abs_dev:
                abs_dev, chosen = abs(pct), metric
                better_direction = (
                    "more"
                    if (cfg["pref"] == "higher" and cur_val < pb_val)
                    or (cfg["pref"] == "lower" and cur_val > pb_val)
                    else "less"
                )
                if abs_dev < 5:
                    cue = f"Keep your {cfg['name']} consistent – looking good!"
                else:
                    level = (
                        "large" if abs_dev > 50 else "med" if abs_dev > 20 else "mild"
                    )
                    cue = cfg[better_direction][level]

        if cue:
            lines.append(cue)
            used = ["height", chosen]
        else:
            lines.append(
                "Drive your arms explosively and extend through your hips for more height."
            )
            used = ["height"]

            # Build multi‑line bullet list, guarantee newline separation
        text = "\n".join(f"•{l}" for l in lines)
        return self._finalize(jump, text, used)

    # ---------------------- helpers --------------------------------------
    def _height_rank_line(self, cur_height, idx):
        heights = [j.metrics.get("height", 0) for j in self.jumps[: idx + 1]]
        rank = sorted(heights, reverse=True).index(cur_height) + 1
        if rank == len(heights):
            return "This is your lowest jump yet – push higher next time!"
        return f"This is your #{rank} highest jump – aim to beat the PB!"

    def _finalize(self, jump, text, metrics):
        jump.feedback = text
        jump.feedback_metrics = metrics
        self.label.setText(text)
        return metrics
