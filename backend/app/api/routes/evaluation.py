from app.evaluation.runner import EvaluationRunner
from fastapi import APIRouter

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

# Cached latest evaluation in memory
_latest_results = None


@router.post("/run")
async def run_evaluation_benchmark():
    global _latest_results
    runner = EvaluationRunner()
    _latest_results = runner.run_benchmark()
    return _latest_results


@router.get("/results")
async def get_latest_evaluation_results():
    global _latest_results
    if not _latest_results:
        runner = EvaluationRunner()
        _latest_results = runner.run_benchmark()
    return _latest_results
