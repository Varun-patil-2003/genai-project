from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from api.tickets import router as ticket_router
from api.chat import router as chat_router
from api.anomalies import router as anomaly_router
from api.rca import router as rca_router

app = FastAPI(
    title="NetOps AI Sentinel",
    version='1.0.0',
    description="Enterprise AI for Network Operations Root Cause Analysis"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ticket_router)
app.include_router(chat_router)
app.include_router(anomaly_router)
app.include_router(rca_router)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/")
async def root():
    return {
        "status": "Online",
        "message": "Welcome to NetOps AI Sentinel API. Use /docs for Swagger.",
        "endpoints": ["/tickets", "/chat", "/anomalies", "/rca"]
        }

if __name__ == "__main__":
    import uvicorn, os
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
