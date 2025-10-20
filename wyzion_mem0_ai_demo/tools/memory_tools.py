"""
Memory tools for OpenAI Agent using Mem0
These functions are used as OpenAI agent tools
"""

import json

from mem0 import MemoryClient

from wyzion_mem0_ai_demo.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Global memory client to be initialized
memory_client: MemoryClient = None


def initialize_memory_client(api_key: str):
    """Initialize the global memory client"""
    global memory_client
    logger.info("Initializing Mem0 memory client")
    try:
        memory_client = MemoryClient(api_key=api_key)
        logger.info("Mem0 memory client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Mem0 memory client: {e}", exc_info=True)
        raise


def add_memory(messages: str, user_id: str) -> str:
    """
    Store a conversation or information in memory for a specific user.

    Args:
        messages: The conversation messages to store in memory. Should be a JSON string
                 of message objects with 'role' and 'content' keys, or a simple text string.
        user_id: The unique identifier for the user

    Returns:
        A JSON string with the result of the operation
    """
    try:
        logger.info(f"Adding memory for user_id={user_id}")
        # Try to parse as JSON first
        try:
            message_list = json.loads(messages)
            logger.debug(f"Parsed messages as JSON: {len(message_list)} messages")
        except json.JSONDecodeError:
            # If not JSON, treat as a simple text message
            message_list = [{"role": "user", "content": messages}]
            logger.debug("Treating messages as plain text")

        memory_client.add(message_list, user_id=user_id, agent_id="sales-agent", output_format="v1.1")
        logger.info(f"Memory stored successfully for user_id={user_id}")
        return json.dumps({"success": True, "message": "Memory stored successfully"})
    except Exception as e:
        logger.error(f"Error adding memory for user_id={user_id}: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


def search_memories(query: str, user_id: str) -> str:
    """
    Search through stored memories for a specific user based on a query.

    Args:
        query: The search query to find relevant memories
        user_id: The unique identifier for the user

    Returns:
        A JSON string containing the list of relevant memories
    """
    try:
        logger.info(f"Searching memories for user_id={user_id}, query='{query}'")
        memories = memory_client.search(query, user_id=user_id, agent_id="sales-agent")
        memory_texts = [m["memory"] for m in memories]
        logger.info(f"Found {len(memory_texts)} memories for query='{query}'")
        return json.dumps({"success": True, "memories": memory_texts, "count": len(memory_texts)})
    except Exception as e:
        logger.error(f"Error searching memories for user_id={user_id}, query='{query}': {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e), "memories": [], "count": 0})


def get_all_memories(user_id: str) -> str:
    """
    Retrieve all stored memories for a specific user.

    Args:
        user_id: The unique identifier for the user

    Returns:
        A JSON string containing all memories for the user
    """
    try:
        logger.info(f"Fetching all memories for user_id={user_id}")
        memories = memory_client.get_all(filters={"OR": [{"user_id": user_id}, {"agent_id": "sales-agent"}]})
        logger.debug(f"Raw memories response type: {type(memories)}")
        logger.debug(f"Raw memories response: {memories}")

        # Handle different response formats from Mem0 API
        if isinstance(memories, str):
            logger.warning(f"Memories response is a string, attempting to parse: {memories}")
            try:
                memories = json.loads(memories)
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse memories string as JSON: {je}")
                return json.dumps(
                    {
                        "success": False,
                        "error": "Invalid response format from memory service",
                        "memories": [],
                        "count": 0,
                    }
                )

        # Extract memory texts safely
        if isinstance(memories, list):
            memory_texts = [m.get("memory", "") for m in memories if isinstance(m, dict)]
            logger.info(f"Successfully retrieved {len(memory_texts)} memories for user_id={user_id}")
            return json.dumps({"success": True, "memories": memory_texts, "count": len(memory_texts)})
        elif isinstance(memories, dict):
            # Handle case where response is a dict with results key
            results = memories.get("results", memories.get("memories", []))
            if isinstance(results, list):
                memory_texts = [m.get("memory", "") for m in results if isinstance(m, dict)]
                logger.info(f"Successfully retrieved {len(memory_texts)} memories for user_id={user_id}")
                return json.dumps({"success": True, "memories": memory_texts, "count": len(memory_texts)})

        logger.warning(f"Unexpected memory response format: {type(memories)}")
        return json.dumps({"success": False, "error": "Unexpected response format", "memories": [], "count": 0})

    except Exception as e:
        logger.error(f"Error fetching memories for user_id={user_id}: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e), "memories": [], "count": 0})


# Tool definitions for OpenAI function calling
MEMORY_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_memories",
            "description": "Search through stored memories for a specific user based on a query to find relevant past conversations and context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant memories",
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The unique identifier for the user",
                    },
                },
                "required": ["query", "user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_memories",
            "description": "Retrieve all stored memories for a specific user to get complete conversation history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The unique identifier for the user",
                    },
                },
                "required": ["user_id"],
            },
        },
    },
]

# Map function names to callable functions
MEMORY_TOOL_FUNCTIONS = {
    "search_memories": search_memories,
    "get_all_memories": get_all_memories,
    "add_memory": add_memory,
}
