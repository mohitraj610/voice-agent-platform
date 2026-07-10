tools = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Fetch the temperature and weather of city",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Question asking about weather for a city",
                },
            },
            "required": ["question"],
        },
    }
]


def get_weather(question):
    return "Mumbai temperature is 65°C, cloudy"
