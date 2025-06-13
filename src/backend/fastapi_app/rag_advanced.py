import json
from collections.abc import AsyncGenerator
from typing import Optional, Union

from agents import (
    Agent,
    ItemHelpers,
    ModelSettings,
    OpenAIChatCompletionsModel,
    Runner,
    ToolCallOutputItem,
    function_tool,
    set_tracing_disabled,
)
from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.types.responses import EasyInputMessageParam, ResponseInputItemParam, ResponseTextDeltaEvent

from fastapi_app.api_models import (
    AIChatRoles,
    ChatRequestOverrides,
    Filter,
    ItemPublic,
    Message,
    RAGContext,
    RetrievalResponse,
    RetrievalResponseDelta,
    SearchResults,
    ThoughtStep,
)
from fastapi_app.postgres_searcher import PostgresSearcher
from fastapi_app.rag_base import RAGChatBase

set_tracing_disabled(disabled=True)


class AdvancedRAGChat(RAGChatBase):
    query_prompt_template = open(RAGChatBase.prompts_dir / "query.txt").read()
    query_fewshots = open(RAGChatBase.prompts_dir / "query_fewshots.json").read()

    def __init__(
        self,
        *,
        messages: list[ResponseInputItemParam],
        overrides: ChatRequestOverrides,
        searcher: PostgresSearcher,
        openai_chat_client: Union[AsyncOpenAI, AsyncAzureOpenAI],
        chat_model: str,
        chat_deployment: Optional[str],  # Not needed for non-Azure OpenAI
    ):
        super().__init__()
        self.searcher = searcher
        self.chat_params = self.get_chat_params(messages, overrides)
        self.model_for_thoughts = (
            {"model": chat_model, "deployment": chat_deployment} if chat_deployment else {"model": chat_model}
        )
        openai_agents_model = OpenAIChatCompletionsModel(
            model=chat_model if chat_deployment is None else chat_deployment, openai_client=openai_chat_client
        )
        self.search_agent = Agent(
            name="Searcher",
            instructions=self.query_prompt_template,
            tools=[function_tool(self.search_database)],
            tool_use_behavior="stop_on_first_tool",
            model=openai_agents_model,
        )
        self.answer_agent = Agent(
            name="Answerer",
            instructions=self.answer_prompt_template,
            model=openai_agents_model,
            model_settings=ModelSettings(
                temperature=self.chat_params.temperature,
                max_tokens=self.chat_params.response_token_limit,
                extra_body={"seed": self.chat_params.seed} if self.chat_params.seed is not None else {},
            ),
        )

    

    
    async def search_database(
        self,
        search_query: str,
    ) -> SearchResults:
        """Search PostgreSQL database with error handling"""
        print(f"DEBUG - Searching with query: {search_query}")
        
        filters: list[Filter] = []
        try:
            results = await self.searcher.search_and_embed(
                query_text=search_query,
                top=self.chat_params.top,
                enable_vector_search=self.chat_params.enable_vector_search,
                enable_text_search=self.chat_params.enable_text_search,
                filters=filters,
            )
            print(f"DEBUG - Found {len(results)} results")
            return SearchResults(
                query=search_query,
                items=[ItemPublic.model_validate(item.to_dict()) for item in results],
                filters=filters
            )
        except Exception as e:
            print(f"Search failed: {e}")
            # Fall back to text-only search if vector search fails
            if "dimensions" in str(e):
                print("Attempting text-only search...")
                results = await self.searcher.search_and_embed(
                    query_text=search_query,
                    top=self.chat_params.top,
                    enable_vector_search=False,  # Disable vector search
                    enable_text_search=True,
                    filters=filters,
                )
                return SearchResults(
                    query=search_query,
                    items=[ItemPublic.model_validate(item.to_dict()) for item in results],
                    filters=filters
                )
            return SearchResults(query=search_query, items=[], filters=filters)

    async def prepare_context(self) -> tuple[list[ItemPublic], list[ThoughtStep]]:
        few_shots: list[ResponseInputItemParam] = json.loads(self.query_fewshots)
        user_query = f"Find search results for user query: {self.chat_params.original_user_query}"
        new_user_message = EasyInputMessageParam(role="user", content=user_query)
        all_messages = few_shots + self.chat_params.past_messages + [new_user_message]

        try:
            run_results = await Runner.run(self.search_agent, input=all_messages)
            most_recent_response = run_results.new_items[-1]
            
            if not isinstance(most_recent_response, ToolCallOutputItem):
                raise ValueError("Model did not call search tool properly")

            search_results = None
            if isinstance(most_recent_response.output, SearchResults):
                search_results = most_recent_response.output
            else:
                try:
                    search_results = SearchResults.model_validate_json(most_recent_response.output)
                except Exception as e:
                    print(f"Failed to parse search results: {e}")
                    search_results = SearchResults(
                        query=self.chat_params.original_user_query,
                        items=[],
                        filters=[]
                    )

            # If we got empty results, try a direct search as fallback
            if not search_results.items:
                print("Falling back to direct search...")
                search_results = await self.search_database(self.chat_params.original_user_query)

        except Exception as e:
            print(f"Search failed: {e}")
            search_results = SearchResults(
                query=self.chat_params.original_user_query,
                items=[],
                filters=[]
            )

        thoughts = [
            ThoughtStep(
                title="Prompt to generate search arguments",
                description=[{"content": self.query_prompt_template}]
                + ItemHelpers.input_to_new_input_list(run_results.input),
                props=self.model_for_thoughts,
            ),
            ThoughtStep(
                title="Search using generated search arguments",
                description=search_results.query,
                props={
                    "top": self.chat_params.top,
                    "vector_search": self.chat_params.enable_vector_search,
                    "text_search": self.chat_params.enable_text_search,
                    "filters": search_results.filters,
                },
            ),
            ThoughtStep(
                title="Search results",
                description=search_results.items,
            ),
        ]
        return search_results.items, thoughts

 

    async def answer(
        self,
        items: list[ItemPublic],
        earlier_thoughts: list[ThoughtStep],
    ) -> RetrievalResponse:
        run_results = await Runner.run(
            self.answer_agent,
            input=self.chat_params.past_messages
            + [{"content": self.prepare_rag_request(self.chat_params.original_user_query, items), "role": "user"}],
        )

        return RetrievalResponse(
            message=Message(content=str(run_results.final_output), role=AIChatRoles.ASSISTANT),
            context=RAGContext(
                data_points={item.id: item for item in items},
                thoughts=earlier_thoughts
                + [
                    ThoughtStep(
                        title="Prompt to generate answer",
                        description=[{"content": self.answer_prompt_template}]
                        + ItemHelpers.input_to_new_input_list(run_results.input),
                        props=self.model_for_thoughts,
                    ),
                ],
            ),
        )

    async def answer_stream(
        self,
        items: list[ItemPublic],
        earlier_thoughts: list[ThoughtStep],
    ) -> AsyncGenerator[RetrievalResponseDelta, None]:
        run_results = Runner.run_streamed(
            self.answer_agent,
            input=self.chat_params.past_messages
            + [{"content": self.prepare_rag_request(self.chat_params.original_user_query, items), "role": "user"}],
        )

        yield RetrievalResponseDelta(
            context=RAGContext(
                data_points={item.id: item for item in items},
                thoughts=earlier_thoughts
                + [
                    ThoughtStep(
                        title="Prompt to generate answer",
                        description=[{"content": self.answer_prompt_template}]
                        + ItemHelpers.input_to_new_input_list(run_results.input),
                        props=self.model_for_thoughts,
                    ),
                ],
            ),
        )

        async for event in run_results.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                yield RetrievalResponseDelta(delta=Message(content=str(event.data.delta), role=AIChatRoles.ASSISTANT))
        return