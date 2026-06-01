"""
Опциональный e2e: полный пайплайн с YOLO на реальном коротком клипе.

Это не набор обучающих видео из главы 4, а произвольный короткий файл для
проверки интеграции. Путь задаётся переменной окружения SKI_ANALYZER_E2E_VIDEO.

Запуск:
  SKI_ANALYZER_E2E_VIDEO=/path/to/short.mp4 python -m pytest -m e2e -q
"""
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.e2e


@pytest.mark.skipif(
    not os.getenv("SKI_ANALYZER_E2E_VIDEO"),
    reason="Set SKI_ANALYZER_E2E_VIDEO to a short .mp4/.mov to run full pipeline e2e",
)
def test_full_pipeline_on_env_video():
    from ski_analyzer.core.pipeline import SkiAnalysisPipeline

    video = Path(os.environ["SKI_ANALYZER_E2E_VIDEO"]).expanduser().resolve()
    assert video.is_file(), video
    assert video.suffix.lower() in {".mp4", ".mov"}

    pipe = SkiAnalysisPipeline()
    result = pipe.analyze_user_video(
        str(video),
        save_intermediate=False,
        use_llm=False,
        llm_generator=None,
        user_profile=None,
    )
    assert "analysis" in result
    assert "files" in result
    assert result["analysis"]
