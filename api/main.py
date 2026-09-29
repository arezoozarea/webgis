from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.spatial import router as spatial_router
from routers.spatial_profile import router as spatial_profile_router
from routers.route_router import router as  route_router
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://172.30.240.40:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(spatial_router)
app.include_router(spatial_profile_router)
app.include_router(route_router)
