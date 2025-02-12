from pydantic import BaseModel, conint

           
class EditOrderLock(BaseModel):
    lock: conint(ge=0, le=10000)
