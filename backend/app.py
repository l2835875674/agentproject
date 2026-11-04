"""启动入口。只负责把领域挂上去 + 托管静态页面。"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.config import FRONTEND_DIR
from backend.core import registry
from backend.domains.read import module as read_module
from backend.domains.physics import module as physics_module

app = FastAPI(title="教育智能体")

for module in (read_module, physics_module):
    registry.register(module)
    app.include_router(module.router)


@app.get("/api/domains")
def list_domains():
    return [{"name": m.NAME, "title": getattr(m, "TITLE", m.NAME)}
            for m in registry.all_domains().values()]


# 静态页面挂在最后，保证 /api/* 优先匹配
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
