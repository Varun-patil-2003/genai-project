FROM python:3.11-slim

# working directory
WORKDIR /app

# copy requirements first
COPY requirements.txt .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# cpoy entire project
COPY . .

# expose FastAPI port
EXPOSE 8000

# running FastAPI app
CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" ]
