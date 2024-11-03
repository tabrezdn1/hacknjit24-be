from fastapi import FastAPI
import uvicorn
from starlette.middleware.cors import CORSMiddleware

from app.exception.exception_handler import ExceptionHandler
from app.router import routers

app = FastAPI()
ExceptionHandler.initiate_exception_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this to match your Next.js app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# add routers
for router_module in routers:
    app.include_router(router_module.router)

if __name__ == '__main__':
    uvicorn.run(port=8080, app=app)
