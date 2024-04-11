from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
import os
import asyncio
app = FastAPI()

UPLOAD_FOLDER = "uploads"
FILE_LIFETIME = timedelta(hours=24)

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Dictionary to store uploaded files and their expiration time
uploaded_files = {}

def cleanup_expired_files():
    now = datetime.now()
    expired_files = [filename for filename, expiration_time in uploaded_files.items() if expiration_time <= now]
    for filename in expired_files:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        os.remove(file_path)
        del uploaded_files[filename]

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    cleanup_expired_files()
    # Generate unique filename based on current timestamp
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}-{file.filename}"
    # Save the file locally
    with open(os.path.join(UPLOAD_FOLDER, filename), "wb") as f:
        f.write(await file.read())
    
    # Store the expiration time of the file
    expiration_time = datetime.now() + FILE_LIFETIME
    uploaded_files[filename] = expiration_time
    
    return {"filename": filename}

@app.get("/retrieve/{filename}")
async def retrieve_file(filename: str):
    cleanup_expired_files()
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    # Check if file exists and is not expired
    if filename in uploaded_files and datetime.now() < uploaded_files[filename]:
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found or expired")

@app.delete("/delete/{filename}")
async def delete_file(filename: str):
    cleanup_expired_files()
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        if filename in uploaded_files:
            del uploaded_files[filename]
        return {"message": f"File '{filename}' deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
