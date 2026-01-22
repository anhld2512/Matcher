from pydantic import BaseModel
from typing import Optional

class JDBase(BaseModel):
    name: str
    description: Optional[str] = None

class JDCreate(JDBase):
    pass

class JDUpdate(BaseModel):
    description: Optional[str] = None

class CVBase(BaseModel):
    name: str
    description: Optional[str] = None

class CVCreate(CVBase):
    pass

class CVUpdate(BaseModel):
    description: Optional[str] = None
