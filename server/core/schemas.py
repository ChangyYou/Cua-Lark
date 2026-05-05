from pydantic import BaseModel

class ExecuteRequest(BaseModel):
    command: str

class ExecuteResponse(BaseModel):
    status: str
    message: str