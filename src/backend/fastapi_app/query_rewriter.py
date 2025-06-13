import json

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionToolParam,
)


def build_search_function() -> list[ChatCompletionToolParam]:
    return [
        {
            "type": "function",
            "function": {
                "name": "search_database",
                "description": "Search PostgreSQL database for relevant policies based on user query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_query": {
                            "type": "string",
                            "description": "Query string to use for full text search, e.g. 'entitlements for parental leave'",
                        },

                    },
                    "required": ["search_query"],
                },
            },
        }
    ]


def extract_search_arguments(original_user_query: str, chat_completion: ChatCompletion):
    response_message = chat_completion.choices[0].message
    search_query = original_user_query  # fallback to original query
    search_query = None
    filters = []
    if response_message.tool_calls:
        for tool in response_message.tool_calls:
            if tool.type != "function":
                continue
            function = tool.function
            if function.name == "search_database":
                arg = json.loads(function.arguments)
                search_query = arg.get("search_query", original_user_query)
                # If you have filters in the future, extract them here
                # filters = args.get("filters", [])
                break  # we found our search query, no need to check other tools

    elif query_text := response_message.content:
        search_query = query_text.strip()
    return search_query, filters
