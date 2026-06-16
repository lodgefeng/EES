# -*- coding: utf-8 -*-
"""Backward-compatible exports for older integrations."""

from app.ar_imaging_adjustment import ARImagingAdjustmentWindow
from app.ai_experiment_llm_judgement import AIExperimentLLMJudgementWindow

# Older name pointed at the adjustment page; keep alias for compatibility.
AIExperimentJudgementWidget = ARImagingAdjustmentWindow
AIExperimentJudgementWindow = ARImagingAdjustmentWindow

__all__ = [
    "AIExperimentJudgementWidget",
    "AIExperimentJudgementWindow",
    "ARImagingAdjustmentWindow",
    "AIExperimentLLMJudgementWindow",
]
