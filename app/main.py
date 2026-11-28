

from fastapi import FastAPI
from app.api.v1.router import api_router

app = FastAPI(title="YouTube RAG Chatbot",
               version="1.0.0",
                 description="YouTube video transcript processing and retrieval-augmented generation chatbot.")



@app.get("/")
async def root():
    return {"message": "Welcome to the YouTube RAG Chatbot API!"}


app.include_router(api_router)
