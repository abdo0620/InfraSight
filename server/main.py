"""InfraSight API.
Run:  uvicorn main:create_app --factory --reload      (from the server/ folder)"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from db.database import init_db, make_engine, make_session_factory
from db.seeds.seed import seed_reference_data
from routes import admin, ai, auth, compliance, reports, tickets


def create_app(engine=None) -> FastAPI:
    engine = engine or make_engine()
    init_db(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as db:
        seed_reference_data(db)

    app = FastAPI(title='InfraSight API', version='0.2.0')
    app.state.session_factory = session_factory
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins(), allow_methods=['*'], allow_headers=['*'])

    for module in (reports, tickets, admin, compliance, ai, auth):
        app.include_router(module.router)

    @app.get('/api/health')
    def health():
        return {'status': 'ok'}

    if settings.CLIENT_DIR.exists():  # serve the front end from the same origin
        app.mount('/', StaticFiles(directory=settings.CLIENT_DIR, html=True), name='client')
    return app


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:create_app', factory=True, reload=True)
