from pydantic import BaseModel


class MessageSchema(BaseModel):
    message: str


class AiChatSchema(BaseModel):
    role: str
    content: str
