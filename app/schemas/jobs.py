from pydantic import BaseModel


class Job(BaseModel):
    type: str
