from fastapi import FastAPI
from fastapi.responses import FileResponse
from api.tickets import router as ticket_router

app = FastAPI(title="NetOps AI Sentinel", version='0.1.0')

app.include_router(ticket_router)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")

@app.get("/")
async def root():
    return {"message": "Welcome to NetOps AI Sentinel API. Use /docs for Swagger."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host='0.0.0.0', port=8000, reload=True)
