from fastapi import FastAPI

from odoo_osi import __version__
from odoo_osi.api.routes import health, indexing, modules, repositories, search, solutions


def create_app() -> FastAPI:
    app = FastAPI(
        title="Odoo Open Source Intelligence",
        version=__version__,
        description=(
            "Enterprise-grade search and recommendation platform for open-source Odoo modules."
        ),
    )
    app.include_router(health.router)
    app.include_router(indexing.router)
    app.include_router(repositories.router)
    app.include_router(modules.router)
    app.include_router(search.router)
    app.include_router(solutions.router)
    return app
