import os
from fastapi import FastAPI, Response, status
from openai import AsyncOpenAI, APIConnectionError, APITimeoutError, APIStatusError, OpenAIError
from dotenv import load_dotenv
from database_models import MessageSchema

load_dotenv()
app = FastAPI()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.post("/chat", response_model=MessageSchema)
async def root(msg: MessageSchema, response: Response):
    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "you are a helpful assistant"},
                {"role": "user", "content": msg.message}
            ]
        )
        return MessageSchema(message=completion.choices[0].message.content)

    except APITimeoutError:
        response.status_code = status.HTTP_504_GATEWAY_TIMEOUT
        return MessageSchema(message="Error request timeout")

    except APIConnectionError:
        response.status_code = status.HTTP_502_BAD_GATEWAY
        return MessageSchema(message="Connection error")

    except APIStatusError as http_err:
        status_code = http_err.response.status_code
        response.status_code = status_code
        return MessageSchema(message=http_err.message)

    except OpenAIError as req_err:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return MessageSchema(message=f"An error occured: {req_err}")
