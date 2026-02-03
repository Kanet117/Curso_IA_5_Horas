from pydantic import BaseModel

class Mensaje(BaseModel):
    phone: str
    message: str