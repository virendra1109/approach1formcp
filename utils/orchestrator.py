# """Orchestrator Agent for Planning and Execution with Dynamic Server Updates"""
# from typing import Dict, List, Any, Optional
# from openai import AsyncAzureOpenAI
# from agent_framework import ChatAgent, AgentThread
# from agent_framework.openai import OpenAIChatClient
# from utils.prompts import executing_instruction
# from config.config import config
# from config.mcp_config import MCP_SERVERS
# import json


# class OrchestratorAgent:
#     """Plans server/tool selection AND executes tasks using ChatAgent with dynamic server awareness"""
    
#     def __init__(self):
#         azure_client = AsyncAzureOpenAI(
#             api_key=config.AZURE_OPENAI_KEY,
#             api_version=config.AZURE_OPENAI_VERSION,
#             azure_endpoint=config.AZURE_OPENAI_ENDPOINT
#         )
#         self.openai_client = OpenAIChatClient(
#             model_id=config.Model,
#             async_client=azure_client
#         )
#         self.planning_agent: Optional[ChatAgent] = None
#         self.execution_agent: Optional[ChatAgent] = None
#         self._current_servers: Dict[str, dict] = {}
        
#     def _build_planning_instruction(self, servers: Dict[str, dict]) -> str:
#         """Build planning instruction with current server list"""
#         server_info = "\n".join([
#             f"  - {srv}: {servers[srv].get('description', 'No description')}"
#             for srv in servers.keys()
#         ])
        
#         return f'''You are a task planning assistant. Analyze queries and determine which servers and tools are needed.

# Available Servers:
# {server_info}

# Your task:
# 1. Identify ALL servers needed to complete the task (can select multiple)
# 2. For each server, write a specific tool search query describing what tools are needed
# 3. Consider the full workflow - if task requires multiple steps, select all relevant servers
# 4. Be inclusive - select all servers that could help to complete the task

# IMPORTANT PLANNING RULES:
# - If query mentions "post X to Slack", you need TWO servers:
#   1. The server that can FETCH X (e.g., HubSpot, Azure, GitHub, Microsoft)
#   2. The Slack server to POST the data
  
# - If query mentions "get X and send to Y":
#   1. Server that provides X
#   2. Server that connects to Y
  
# - Break down complex queries into required data sources and destinations

# Examples:
# - "Post HubSpot contacts in Slack" → servers: ["hubspot", "slack"]
# - "Get Azure Function details and share in Slack" → servers: ["micorosoft mcp", "slack"]
# - "Fetch deals over $10k and notify team" → servers: ["hubspot", "slack"]
# - "Get Microsoft documentation about X" → servers: ["micorosoft mcp"]

# IMPORTANT: You must respond ONLY with valid JSON in this exact format:
# {{
#     "servers": ["server1", "server2"],
#     "tool_queries": {{
#         "server1": "specific tool search query for server1",
#         "server2": "specific tool search query for server2"
#     }}
# }}

# Do not include any other text, explanations, or markdown formatting. Only return the JSON object.'''
    
#     async def initialize(self):
#         """Initialize agents with current server configuration"""
#         # Store initial server configuration
#         self._current_servers = MCP_SERVERS.copy()
        
#         self.planning_agent = ChatAgent(
#             chat_client=self.openai_client,
#             name="Planning_Agent",
#             instructions=self._build_planning_instruction(self._current_servers)
#         )
        
#         self.execution_agent = ChatAgent(
#             chat_client=self.openai_client,
#             name="Execution_Agent",
#             instructions=executing_instruction
#         )
        
#         await self.planning_agent.__aenter__()
#         await self.execution_agent.__aenter__()
    
#     async def update_servers(self, current_servers: Dict[str, dict]):
#         """
#         Update planning agent with new server configuration.
#         Call this whenever servers are added/removed dynamically.
#         """
#         if current_servers != self._current_servers:
#             print(f"Updating orchestrator with new server list: {list(current_servers.keys())}")
#             self._current_servers = current_servers.copy()
            
#             # Recreate planning agent with updated server list
#             if self.planning_agent:
#                 await self.planning_agent.__aexit__(None, None, None)
            
#             self.planning_agent = ChatAgent(
#                 chat_client=self.openai_client,
#                 name="Planning_Agent",
#                 instructions=self._build_planning_instruction(self._current_servers)
#             )
            
#             await self.planning_agent.__aenter__()
#             print("✓ Orchestrator updated with new server configuration")
    
#     async def shutdown(self):
#         """Shutdown agents"""
#         if self.planning_agent:
#             await self.planning_agent.__aexit__(None, None, None)
#         if self.execution_agent:
#             await self.execution_agent.__aexit__(None, None, None)
    
#     def decode_json(self, response):
#         response_text = str(response)
#         if "```json" in response_text:
#             json_str = response_text.split("```json")[1].split("```")[0].strip()
#         elif "```" in response_text:
#             json_str = response_text.split("```")[1].split("```")[0].strip()
#         else:
#             json_str = response_text.strip()
#         return json_str

#     async def plan(self, query: str, servers: List[str]) -> Dict:
#         """Generate plan with servers and tool queries"""
#         response = await self.planning_agent.run(query, tools=[])
#         usage = getattr(response, "usage_details", None)


#         input_token1=getattr(usage, "input_token_count", None)
#         output_token1=getattr(usage, "output_token_count", None)
#         total_token1=getattr(usage, "total_token_count", None)

#         json_str = self.decode_json(response)
#         plan = json.loads(json_str)
        
#         print(f"\nPLAN:")
#         print(f"   Servers: {', '.join(plan['servers'])}")
#         for srv, tq in plan['tool_queries'].items():
#             print(f"   • {srv}: '{tq}'")
        
#         return plan,input_token1,output_token1,total_token1
    
#     async def execute(self, query: str, tools: List[Any], thread: Optional[AgentThread] = None) -> Any:
#         """Execute query with filtered tools using thread for context"""
#         print(f"\nEXECUTING with {len(tools)} tools via ChatAgent Orchestrator.\n")
        
#         if thread is None:
#             thread = self.execution_agent.get_new_thread()
        
#         response = await self.execution_agent.run(query, tools=tools, thread=thread)
#         usage = getattr(response, "usage_details", None)


#         input_token=getattr(usage, "input_token_count", None)
#         output_token=getattr(usage, "output_token_count", None)
#         total_token=getattr(usage, "total_token_count", None)

#         return response, thread,input_token,output_token,total_token

"""Orchestrator Agent with Enhanced Debugging and Verification"""
from typing import Dict, List, Any, Optional
from openai import AsyncAzureOpenAI
from agent_framework import ChatAgent, AgentThread
from agent_framework.openai import OpenAIChatClient
from utils.prompts import executing_instruction, planning_instruction
from config.config import config
from config.mcp_config import MCP_SERVERS
import json
import re
from utils.loggers import logger


class OrchestratorAgent:
    """Plans server/tool selection AND executes tasks with enhanced debugging"""
    
    def __init__(self):
        azure_client = AsyncAzureOpenAI(
            api_key=config.AZURE_OPENAI_KEY,
            api_version=config.AZURE_OPENAI_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT
        )
        self.openai_client = OpenAIChatClient(
            model_id=config.Model,
            async_client=azure_client
        )
        self.planning_agent: Optional[ChatAgent] = None
        self.execution_agent: Optional[ChatAgent] = None
        self._current_servers: Dict[str, dict] = {}
        
    def _build_planning_instruction(self, servers: Dict[str, dict]) -> str:
        """Build planning instruction with current server list"""
        server_info = "\n".join([
            f"  - {srv}: {servers[srv].get('description', 'No description')}"
            for srv in servers.keys()
        ])
        
        return planning_instruction.format(server_info=server_info)
    
    def _extract_channel_from_query(self, query: str) -> Optional[str]:
        """Extract Slack channel name from query"""
        # Patterns: #channel-name, "to channel-name", "in channel-name"
        patterns = [
            r'#([\w-]+)',  # #research-updates
            r'to\s+#?([\w-]+)\s+(?:channel)?',  # to research-updates
            r'in\s+(?:the\s+)?#?([\w-]+)\s+channel',  # in the dev-team channel
            r'post\s+(?:to|in)\s+#?([\w-]+)',  # post to research-updates
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                channel = match.group(1)
                logger.info(f"Extracted channel from query: '{channel}'")
                return channel
        
        logger.warning("No channel found in query, will use default")
        return None
    
    async def initialize(self):
        """Initialize agents with current server configuration"""
        self._current_servers = MCP_SERVERS.copy()
        
        self.planning_agent = ChatAgent(
            chat_client=self.openai_client,
            name="Planning_Agent",
            instructions=self._build_planning_instruction(self._current_servers)
        )
        
        self.execution_agent = ChatAgent(
            chat_client=self.openai_client,
            name="Execution_Agent",
            instructions=executing_instruction
        )
        
        await self.planning_agent.__aenter__()
        await self.execution_agent.__aenter__()
    
    async def update_servers(self, current_servers: Dict[str, dict]):
        """Update planning agent with new server configuration"""
        if current_servers != self._current_servers:
            logger.info(f"Updating orchestrator with servers: {list(current_servers.keys())}")
            self._current_servers = current_servers.copy()
            
            if self.planning_agent:
                await self.planning_agent.__aexit__(None, None, None)
            
            self.planning_agent = ChatAgent(
                chat_client=self.openai_client,
                name="Planning_Agent",
                instructions=self._build_planning_instruction(self._current_servers)
            )
            
            await self.planning_agent.__aenter__()
            logger.info("✓ Orchestrator updated with new server configuration")
    
    async def shutdown(self):
        """Shutdown agents"""
        if self.planning_agent:
            await self.planning_agent.__aexit__(None, None, None)
        if self.execution_agent:
            await self.execution_agent.__aexit__(None, None, None)
    
    def decode_json(self, response):
        """Extract JSON from response"""
        response_text = str(response)
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
        return json_str

    async def plan(self, query: str, servers: List[str]) -> tuple[Dict, int, int, int]:
        """Generate plan with servers and tool queries"""
        logger.info(f"Planning for query: {query}")
        
        # Extract channel info early to inform planning
        channel = self._extract_channel_from_query(query)
        
        # Enhance query with channel context if found
        enhanced_query = query
        if channel:
            enhanced_query = f"{query}\n[Target channel: {channel}]"
        
        response = await self.planning_agent.run(enhanced_query, tools=[])
        usage = getattr(response, "usage_details", None)

        input_token1 = getattr(usage, "input_token_count", 0)
        output_token1 = getattr(usage, "output_token_count", 0)
        total_token1 = getattr(usage, "total_token_count", 0)

        json_str = self.decode_json(response)
        plan = json.loads(json_str)
        
        # Add channel to plan metadata if extracted
        if channel:
            plan["metadata"] = {"target_channel": channel}
        
        logger.info(f"PLAN GENERATED:")
        logger.info(f"   Servers: {', '.join(plan['servers'])}")
        for srv, tq in plan['tool_queries'].items():
            logger.info(f"   • {srv}: '{tq}'")
        if channel:
            logger.info(f"   Target Channel: {channel}")
        
        return plan, input_token1, output_token1, total_token1
    
    async def execute(
        self, 
        query: str, 
        tools: List[Any], 
        thread: Optional[AgentThread] = None,
        plan: Optional[Dict] = None
    ) -> tuple[Any, AgentThread, int, int, int]:
        """Execute query with filtered tools using thread for context"""
        logger.info(f"EXECUTING with {len(tools)} tools")
        
        # Extract channel from query for execution context
        channel = self._extract_channel_from_query(query)
        
        # Enhance query with explicit channel instruction
        enhanced_query = query
        if channel:
            enhanced_query = f"""{query}

CRITICAL INSTRUCTION: The target Slack channel is "{channel}" (without # symbol).
When posting to Slack, you MUST use channel="{channel}" in the tool call.
DO NOT use any other channel name."""
            logger.info(f"Enhanced query with channel instruction: {channel}")
        
        if thread is None:
            thread = self.execution_agent.get_new_thread()
        
        # Log available tools
        logger.info("Available tools for execution:")
        for tool in tools:
            tool_name = getattr(tool, 'name', 'unknown')
            logger.info(f"  - {tool_name}")
        
        response = await self.execution_agent.run(
            enhanced_query, 
            tools=tools, 
            thread=thread
        )
        
        # Log execution details
        self._log_execution_details(response)
        
        usage = getattr(response, "usage_details", None)
        input_token = getattr(usage, "input_token_count", 0)
        output_token = getattr(usage, "output_token_count", 0)
        total_token = getattr(usage, "total_token_count", 0)

        return response, thread, input_token, output_token, total_token
    
    def _log_execution_details(self, response):
        """Log detailed execution information"""
        try:
            if hasattr(response, 'messages'):
                for msg in response.messages:
                    role = getattr(msg, 'role', 'unknown')
                    
                    # Log tool calls
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        logger.info(f"\n{'='*60}")
                        logger.info(f"TOOL CALLS FROM {role.upper()}:")
                        for tc in msg.tool_calls:
                            tool_name = getattr(tc, 'name', 'unknown')
                            tool_args = getattr(tc, 'arguments', {})
                            logger.info(f"\n  Tool: {tool_name}")
                            logger.info(f"  Arguments: {json.dumps(tool_args, indent=4)}")
                            
                            # Special attention to Slack calls
                            if 'slack' in tool_name.lower() or 'post' in tool_name.lower():
                                logger.warning(f"  ⚠️  SLACK POST DETECTED")
                                if 'channel' in tool_args:
                                    logger.warning(f"  Channel used: '{tool_args['channel']}'")
                                else:
                                    logger.error(f"  ❌ NO CHANNEL SPECIFIED!")
                        logger.info(f"{'='*60}\n")
                    
                    # Log content
                    if hasattr(msg, 'content') and msg.content:
                        content = str(msg.content)
                        if len(content) > 200:
                            logger.info(f"{role}: {content[:200]}...")
                        else:
                            logger.info(f"{role}: {content}")
        except Exception as e:
            logger.error(f"Error logging execution details: {e}")