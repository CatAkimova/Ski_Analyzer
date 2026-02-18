from fastapi import FastAPI
from fastapi import File
from fastapi import UploadFile

import tempfile
import os
from dotenv import load_dotenv
load_dotenv()


from pathlib import Path
from ski_analyzer.core.pipeline import SkiAnalysisPipeline
from ski_analyzer.utils.llm_recommendations import LLMRecommendationGenerator

from typing import Any
import numpy as np

def to_builtin(obj: Any) -> Any:
    """
    Рекурсивно переводит numpy/pandas типы в обычные python-типы,
    чтобы FastAPI смог сериализовать ответ в JSON.
    """
    # dict
    if isinstance(obj, dict):
        return {str(k): to_builtin(v) for k, v in obj.items()}

    # list/tuple/set
    if isinstance(obj, (list, tuple, set)):
        return [to_builtin(x) for x in obj]

    # numpy scalar (np.bool_, np.float64, np.int64 и т.п.)
    if isinstance(obj, np.generic):
        return obj.item()

    # numpy array
    if isinstance(obj, np.ndarray):
        return obj.tolist()

    return obj

app = FastAPI()

@app.get("/health")
async def health():
    return{"status": "running"}

@app.post("/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    filename = file.filename
    suffix = Path(filename).suffix.lower()

    if suffix not in [".mp4", ".mov"]:
        return {"error": "Неподдерживаемый формат файла"}

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        temp_path = tmp.name
        tmp.write(await file.read())
    try:
        pipeline = SkiAnalysisPipeline()
        result = pipeline.analyze_user_video(temp_path, save_intermediate = False, use_llm = False, llm_generator = None, user_profile = None)
        report = result.get("analysis", {}) or {}

        files = result.get("files", {}) or {}
        llm_recs = result.get("llm_recommendations", None)

        response = {"analysis": report, "files": files}
        if llm_recs:
            response["llm_recommendations"] = llm_recs

        return to_builtin(response)


    finally:
        os.remove(temp_path)
        print("Файл удален")



