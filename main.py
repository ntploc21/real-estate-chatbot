# flake8: noqa: E402
from app.config import DATA_DIR, STATIC_DIR
from dotenv import load_dotenv

load_dotenv()

import logging
import os

import uvicorn
from app.api.routers import api_router
from app.middlewares.frontend import FrontendProxyMiddleware
from app.observability import init_observability
from app.settings import init_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

# from elasticapm.contrib.starlette import make_apm_client, ElasticAPM
# import urllib3
#
# apm_config = {
#     'SERVICE_NAME': os.getenv('ELASTIC_APM_SERVICE_NAME'),
#     'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL'),
#     'SECRET_TOKEN': os.getenv('ELASTIC_APM_SECRET_TOKEN'),
#     'ENVIRONMENT': os.getenv('ELASTIC_APM_ENVIRONMENT'),
#     'VERIFY_SERVER_CERT': os.getenv('ELASTIC_APM_VERIFY_SERVER_CERT', 'true').lower() == 'true',
# }

# Global variable to hold the APM client instance
# apm_client = None
#
# def get_apm_client(config):
#     global apm_client
#     if apm_client is None:
#         apm_client = make_apm_client(config)
#     return apm_client
#
# apm = get_apm_client(apm_config)
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


servers = []
app_name = os.getenv("FLY_APP_NAME")
if app_name:
    servers = [{"url": f"https://{app_name}.fly.dev"}]
app = FastAPI(servers=servers)
# app.add_middleware(ElasticAPM, client=apm)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


init_settings()
init_observability()

environment = os.getenv("ENVIRONMENT", "dev")  # Default to 'development' if not set
logger = logging.getLogger("uvicorn")


def mount_static_files(directory, path, html=False):
    if os.path.exists(directory):
        logger.info(f"Mounting static files '{directory}' at '{path}'")
        app.mount(
            path,
            StaticFiles(directory=directory, check_dir=False, html=html),
            name=f"{directory}-static",
        )


app.include_router(api_router, prefix="/api")

# Mount the data files to serve the file viewer
mount_static_files(DATA_DIR, "/api/files/data")
# Mount the output files from tools
mount_static_files("output", "/api/files/output")

if environment == "dev":
    frontend_endpoint = os.getenv("FRONTEND_ENDPOINT")
    if frontend_endpoint:
        app.add_middleware(
            FrontendProxyMiddleware,
            frontend_endpoint=frontend_endpoint,
            excluded_paths=set(
                route.path for route in app.routes if hasattr(route, "path")
            ),
        )
    else:
        logger.warning("No frontend endpoint - starting API server only")

        @app.get("/")
        async def redirect_to_docs():
            return RedirectResponse(url="/docs")
else:
    # Mount the frontend static files (production)
    mount_static_files(STATIC_DIR, "/", html=True)

if __name__ == "__main__":
    app_host = os.getenv("APP_HOST", "0.0.0.0")
    app_port = int(os.getenv("APP_PORT", "8000"))
    reload = True if environment == "dev" else False

    uvicorn.run(app="main:app", host=app_host, port=app_port, reload=reload)
