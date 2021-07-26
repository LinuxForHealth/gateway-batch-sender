import uvicorn
from fastapi import Header
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import File, UploadFile, Form
import logging
from logging import DEBUG
import random

logging.getLogger().setLevel(DEBUG)
logging.getLogger("uvicorn.error").setLevel(DEBUG)

app = FastAPI()

async def upload_hl7_batchzip(file: UploadFile = File(...), tenant_id: str = Header(None)):
    roll = random.randint(0,3)
    if roll == 0:
        raise HTTPException(
            status_code=400, detail="Forced 400 error"
        )
    if roll == 1:
        raise HTTPException(
            status_code=500, detail="Forced 500 error"
        )
    con = await file.read()
    print(f'function called with {con}, {tenant_id}')


app.add_api_route('/test', upload_hl7_batchzip, methods=['POST'])

uvicorn.run(app, host='0.0.0.0', port=5000, log_level='debug')
