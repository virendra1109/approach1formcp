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

"""Enhanced Orchestrator with Better Execution Context"""
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
    """Plans server/tool selection AND executes tasks with enhanced context"""
    
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
        patterns = [
            r'#([\w-]+)',  # #channel-name
            r'to\s+#?([\w-]+)\s+(?:channel)?',  # to channel-name
            r'in\s+(?:the\s+)?#?([\w-]+)\s+channel',  # in the channel-name channel
            r'post\s+(?:to|in)\s+#?([\w-]+)',  # post to channel-name
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                channel = match.group(1)
                logger.info(f"Extracted channel from query: '{channel}'")
                return channel
        
        return None
    
    def _build_execution_context(self, query: str, plan: Dict) -> str:
        """Build enhanced execution instructions based on the plan"""
        workflow_type = plan.get("metadata", {}).get("workflow_type", "unknown")
        servers = plan.get("servers", [])
        target_channel = plan.get("metadata", {}).get("target_channel")
        
        context_parts = [query]
        
        # Add workflow guidance
        if workflow_type == "search_and_post" or ("search" in servers and "slack" in servers):
            context_parts.append(
                "\n\n[EXECUTION GUIDANCE: This is a search-and-post workflow. "
                "First use search tools to find actual information, "
                "then format and post the real findings.]"
            )
        elif workflow_type == "retrieve_and_share" or any(s in ["hubspot", "github"] for s in servers):
            context_parts.append(
                "\n\n[EXECUTION GUIDANCE: This is a retrieve-and-share workflow. "
                "First fetch actual data from the service, "
                "then format and share the real results.]"
            )
        
        # Add channel instruction if present
        if target_channel:
            context_parts.append(
                f"\n\n[TARGET CHANNEL: {target_channel}] "
                f"When posting to Slack, use channel=\"{target_channel}\" (no # symbol)."
            )
        
        # Add explicit reminder
        context_parts.append(
            "\n\n[IMPORTANT: You MUST call the actual tools to retrieve real data. "
            "Do NOT post example/template content. Use the tools to get actual information.]"
        )
        
        return "".join(context_parts)
    
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
        logger.info(f"\n{'='*70}")
        logger.info(f"PLANNING PHASE")
        logger.info(f"Query: {query}")
        logger.info(f"{'='*70}")
        
        response = await self.planning_agent.run(query, tools=[])
        usage = getattr(response, "usage_details", None)

        input_token1 = getattr(usage, "input_token_count", 0)
        output_token1 = getattr(usage, "output_token_count", 0)
        total_token1 = getattr(usage, "total_token_count", 0)

        json_str = self.decode_json(response)
        plan = json.loads(json_str)
        
        # Ensure metadata exists
        if "metadata" not in plan:
            plan["metadata"] = {}
        
        # Extract channel if not already in plan
        if "target_channel" not in plan["metadata"]:
            channel = self._extract_channel_from_query(query)
            if channel:
                plan["metadata"]["target_channel"] = channel
        
        logger.info(f"\nPLAN GENERATED:")
        logger.info(f"  Servers: {', '.join(plan['servers'])}")
        logger.info(f"  Workflow: {plan['metadata'].get('workflow_type', 'unknown')}")
        if plan["metadata"].get("target_channel"):
            logger.info(f"  Target Channel: {plan['metadata']['target_channel']}")
        for srv, tq in plan['tool_queries'].items():
            logger.info(f"  • {srv}: '{tq}'")
        logger.info(f"{'='*70}\n")
        
        return plan, input_token1, output_token1, total_token1
    
    async def execute(
        self, 
        query: str, 
        tools: List[Any], 
        thread: Optional[AgentThread] = None,
        plan: Optional[Dict] = None
    ) -> tuple[Any, AgentThread, int, int, int]:
        """Execute query with enhanced context and verification"""
        logger.info(f"\n{'='*70}")
        logger.info(f"EXECUTION PHASE")
        logger.info(f"Tools available: {len(tools)}")
        logger.info(f"{'='*70}")
        
        # Build execution context with plan information
        if plan:
            execution_query = self._build_execution_context(query, plan)
            logger.info(f"\nEnhanced query with context:")
            logger.info(execution_query)
        else:
            execution_query = query
        
        if thread is None:
            thread = self.execution_agent.get_new_thread()
        
        # Log available tools for debugging
        logger.info("\nAvailable tools:")
        for tool in tools:
            tool_name = getattr(tool, 'name', 'unknown')
            logger.info(f"  - {tool_name}")
        
        # Execute
        response = await self.execution_agent.run(
            execution_query, 
            tools=tools, 
            thread=thread
        )
        
        # Detailed logging
        self._log_execution_details(response, plan)
        
        usage = getattr(response, "usage_details", None)
        input_token = getattr(usage, "input_token_count", 0)
        output_token = getattr(usage, "output_token_count", 0)
        total_token = getattr(usage, "total_token_count", 0)

        logger.info(f"\n{'='*70}")
        logger.info(f"EXECUTION COMPLETE")
        logger.info(f"{'='*70}\n")

        return response, thread, input_token, output_token, total_token
    
    def _log_execution_details(self, response, plan: Optional[Dict] = None):
        """Log detailed execution information with plan verification"""
        try:
            expected_channel = plan.get("metadata", {}).get("target_channel") if plan else None
            tool_calls_found = False
            slack_posts = []
            
            if hasattr(response, 'messages'):
                for msg in response.messages:
                    role = getattr(msg, 'role', 'unknown')
                    
                    # Log tool calls
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_calls_found = True
                        logger.info(f"\n{'='*60}")
                        logger.info(f"TOOL CALLS FROM {role.upper()}:")
                        for tc in msg.tool_calls:
                            tool_name = getattr(tc, 'name', 'unknown')
                            tool_args = getattr(tc, 'arguments', {})
                            logger.info(f"\n  Tool: {tool_name}")
                            logger.info(f"  Arguments: {json.dumps(tool_args, indent=4)}")
                            
                            # Track Slack posts
                            if 'slack' in tool_name.lower() and 'post' in tool_name.lower():
                                slack_posts.append(tool_args)
                                logger.warning(f"  ⚠️  SLACK POST DETECTED")
                                channel_used = tool_args.get('channel', 'NOT SPECIFIED')
                                logger.warning(f"  Channel: '{channel_used}'")
                                
                                # Verify channel matches expectation
                                if expected_channel and channel_used != expected_channel:
                                    logger.error(
                                        f"  ❌ CHANNEL MISMATCH! "
                                        f"Expected: '{expected_channel}', Used: '{channel_used}'"
                                    )
                                elif expected_channel:
                                    logger.info(f"  ✓ Channel matches expected: '{expected_channel}'")
                        
                        logger.info(f"{'='*60}\n")
            
            # Verification summary
            if plan:
                workflow = plan.get("metadata", {}).get("workflow_type", "unknown")
                requires_search = "search" in workflow or any("search" in s for s in plan.get("servers", []))
                requires_slack = "slack" in plan.get("servers", [])
                
                logger.info("\n=== EXECUTION VERIFICATION ===")
                logger.info(f"Workflow type: {workflow}")
                logger.info(f"Tool calls made: {tool_calls_found}")
                
                if requires_search and not tool_calls_found:
                    logger.error("❌ PROBLEM: Workflow requires search but no tools were called!")
                
                if requires_slack:
                    if slack_posts:
                        logger.info(f"✓ Slack posts made: {len(slack_posts)}")
                        for i, post in enumerate(slack_posts, 1):
                            logger.info(f"  Post {i}: channel='{post.get('channel')}', "
                                      f"length={len(str(post.get('text', '')))} chars")
                    else:
                        logger.error("❌ PROBLEM: Workflow requires Slack post but none were made!")
                
                logger.info("=" * 30 + "\n")
                
        except Exception as e:
            logger.error(f"Error logging execution details: {e}")