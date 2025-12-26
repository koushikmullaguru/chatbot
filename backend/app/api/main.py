from fastapi import APIRouter
from .endpoints import auth, users, academic, generator, assessment, planner, performance, llm

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(academic.router, prefix="/academic", tags=["academic"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(generator.router, prefix="/generator", tags=["generator"])
api_router.include_router(assessment.router, prefix="/assessments", tags=["assessment"])
api_router.include_router(planner.router, prefix="/planner", tags=["planner"])
api_router.include_router(performance.router, prefix="/performance", tags=["performance"])