import os
from fastapi import FastAPI, Response, status
from openai import AsyncOpenAI, APIConnectionError, APITimeoutError, APIStatusError, OpenAIError
from dotenv import load_dotenv
from database_models import MessageSchema, AiChatSchema
from tools_functions import tools, get_weather
import json

load_dotenv()
app = FastAPI()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.post("/chat")
async def root(msg: MessageSchema, response: Response):
    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "you are a helpful assistant"},
                {"role": "user", "content": msg.message}
            ]
        )
        return completion.choices[0].message.content

    except APITimeoutError:
        response.status_code = status.HTTP_504_GATEWAY_TIMEOUT
        return "Error request timeout"

    except APIConnectionError:
        response.status_code = status.HTTP_502_BAD_GATEWAY
        return "Connection error"

    except APIStatusError as http_err:
        status_code = http_err.response.status_code
        response.status_code = status_code
        return http_err.message

    except OpenAIError as req_err:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return f"An error occured: {req_err}"


@app.post("/tool-call")
async def tool_call(chat: AiChatSchema, response: Response):
    input_list = [dict(chat)]
    try:
        completion = await client.responses.create(
            model="gpt-5.4-nano",
            tools=tools,
            input=input_list,
        )
        input_list += completion.output
        for item in completion.output:
            if item.type == "function_call" and item.name == "get_weather":
                try:
                    parsed_args = json.loads(item.arguments)
                    tool_input = parsed_args["question"]
                except (json.JSONDecodeError, KeyError) as e:
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    input_list.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": f" Failed, error with arguments - {e}"
                    })
                else:
                    result = get_weather(tool_input)
                    input_list.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": result
                    })
        completion = await client.responses.create(
            model="gpt-5.4-nano",
            instructions="Respond with absolute value",
            tools=tools,
            input=input_list,
        )
        return completion.output_text

    except APITimeoutError:
        response.status_code = status.HTTP_504_GATEWAY_TIMEOUT
        return "Error request timeout"

    except APIConnectionError:
        response.status_code = status.HTTP_502_BAD_GATEWAY
        return "Connection error"

    except APIStatusError as http_err:
        status_code = http_err.response.status_code
        response.status_code = status_code
        return http_err.message

    except OpenAIError as req_err:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return f"An error occured: {req_err}"
