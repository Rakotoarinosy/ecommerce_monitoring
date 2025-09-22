from datetime import datetime
import json
import os
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()

@router.get("/process_payment")
def get_process_payment():
    return {"message": "Process Payment Endpoint is working!"}