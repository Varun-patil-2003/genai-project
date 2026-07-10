import gradio as gr
import uvicorn
from app.main import app as fastapi_app  # adjust import to match your actual FastAPI app location

def health_check():
    return "NetOps AI Sentinel API is running. Visit /docs for the API reference."

demo = gr.Interface(
    fn=health_check,
    inputs=None,
    outputs="text",
    title="NetOps AI Sentinel — Backend API"
)

app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)