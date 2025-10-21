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

        memory_client.add(message_list, user_id=user_id, output_format="v1.1")
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
        memories = memory_client.search(query, user_id=user_id)
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
        memories = memory_client.get_all(filters={[{"user_id": user_id}]})
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


def add_member_facts(member_data: dict) -> str:
    """
    Store member details as facts in memory for a specific member.

    Args:
        member_data: Dictionary containing member details including:
                    - id: Member ID (used as user_id)
                    - name: Member name
                    - age: Member age
                    - vertical: Member's industry vertical
                    - persona: Member's persona
                    - current_stage: Current journey stage
                    - goal: Member's goal
                    Plus vertical-specific fields

    Returns:
        A JSON string with the result of the operation
    """
    try:
        member_id = member_data.get("id")
        if not member_id:
            return json.dumps({"success": False, "error": "Member ID is required"})

        logger.info(f"Adding member facts for member_id={member_id}")

        # Create fact-based messages about the member
        facts = []

        if member_data.get("name"):
            facts.append(f"Member's name is {member_data['name']}")

        if member_data.get("age"):
            facts.append(f"Member is {member_data['age']} years old")

        if member_data.get("vertical"):
            facts.append(f"Member is in the {member_data['vertical']} vertical")

        if member_data.get("persona"):
            facts.append(f"Member persona: {member_data['persona']}")

        if member_data.get("current_stage"):
            facts.append(f"Current journey stage: {member_data['current_stage']}")

        if member_data.get("goal"):
            facts.append(f"Member's goal: {member_data['goal']}")

        if member_data.get("joined_year"):
            facts.append(f"Member joined in {member_data['joined_year']}")

        # Add vertical-specific facts
        vertical = member_data.get("vertical", "")
        if vertical == "BFSI":
            if member_data.get("credit_score"):
                facts.append(f"Credit score: {member_data['credit_score']}")
            if member_data.get("transaction_volume"):
                facts.append(f"Transaction volume: ${member_data['transaction_volume']:,}")
            if member_data.get("current_products"):
                facts.append(f"Current products: {', '.join(member_data['current_products'])}")
        elif vertical == "Healthcare":
            if member_data.get("visit_frequency"):
                facts.append(f"Visit frequency: {member_data['visit_frequency']}")
            if member_data.get("current_products"):
                facts.append(f"Care programs: {', '.join(member_data['current_products'])}")
        elif vertical == "E-commerce":
            if member_data.get("session_count"):
                facts.append(f"Session count: {member_data['session_count']}")
            if member_data.get("browsing_behavior"):
                facts.append(f"Browsing behavior: {member_data['browsing_behavior']}")

        if member_data.get("risk_level"):
            facts.append(f"Risk level: {member_data['risk_level']}")

        # Combine facts into a structured message
        fact_message = [
            {
                "role": "user",
                "content": f"Member Profile Facts for {member_data.get('name', member_id)}: " + "; ".join(facts),
            }
        ]

        # Store facts in mem0
        memory_client.add(fact_message, user_id=member_id, output_format="v1.1")

        logger.info(f"Member facts stored successfully for member_id={member_id}")
        return json.dumps(
            {
                "success": True,
                "message": f"Member facts stored for {member_data.get('name', member_id)}",
                "facts_count": len(facts),
            }
        )
    except Exception as e:
        logger.error(f"Error adding member facts: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})


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
    "add_member_facts": add_member_facts,
}
