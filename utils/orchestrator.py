"""Orchestrator Agent for Planning and Execution with Dynamic Server Updates"""
from typing import Dict, List, Any, Optional
from openai import AsyncAzureOpenAI
from agent_framework import ChatAgent, AgentThread
from agent_framework.openai import OpenAIChatClient
from utils.prompts import executing_instruction
from config.config import config
from config.mcp_config import MCP_SERVERS
import json


class OrchestratorAgent:
    """Plans server/tool selection AND executes tasks using ChatAgent with dynamic server awareness"""
    
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
        
        return f'''You are a task planning assistant. Analyze queries and determine which servers and tools are needed.

Available Servers:
{server_info}

Your task:
1. Identify ALL servers needed to complete the task (can select multiple)
2. For each server, write a specific tool search query describing what tools are needed
3. Consider the full workflow - if task requires multiple steps, select all relevant servers
4. Be inclusive - select all servers that could help to complete the task

IMPORTANT PLANNING RULES:
- If query mentions "post X to Slack", you need TWO servers:
  1. The server that can FETCH X (e.g., HubSpot, Azure, GitHub, Microsoft)
  2. The Slack server to POST the data
  
- If query mentions "get X and send to Y":
  1. Server that provides X
  2. Server that connects to Y
  
- Break down complex queries into required data sources and destinations

Examples:
- "Post HubSpot contacts in Slack" → servers: ["hubspot", "slack"]
- "Get Azure Function details and share in Slack" → servers: ["micorosoft mcp", "slack"]
- "Fetch deals over $10k and notify team" → servers: ["hubspot", "slack"]
- "Get Microsoft documentation about X" → servers: ["micorosoft mcp"]

IMPORTANT: You must respond ONLY with valid JSON in this exact format:
{{
    "servers": ["server1", "server2"],
    "tool_queries": {{
        "server1": "specific tool search query for server1",
        "server2": "specific tool search query for server2"
    }}
}}

Do not include any other text, explanations, or markdown formatting. Only return the JSON object.'''
    
    async def initialize(self):
        """Initialize agents with current server configuration"""
        # Store initial server configuration
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
        """
        Update planning agent with new server configuration.
        Call this whenever servers are added/removed dynamically.
        """
        if current_servers != self._current_servers:
            print(f"Updating orchestrator with new server list: {list(current_servers.keys())}")
            self._current_servers = current_servers.copy()
            
            # Recreate planning agent with updated server list
            if self.planning_agent:
                await self.planning_agent.__aexit__(None, None, None)
            
            self.planning_agent = ChatAgent(
                chat_client=self.openai_client,
                name="Planning_Agent",
                instructions=self._build_planning_instruction(self._current_servers)
            )
            
            await self.planning_agent.__aenter__()
            print("✓ Orchestrator updated with new server configuration")
    
    async def shutdown(self):
        """Shutdown agents"""
        if self.planning_agent:
            await self.planning_agent.__aexit__(None, None, None)
        if self.execution_agent:
            await self.execution_agent.__aexit__(None, None, None)
    
    def decode_json(self, response):
        response_text = str(response)
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
        return json_str

    async def plan(self, query: str, servers: List[str]) -> Dict:
        """Generate plan with servers and tool queries"""
        response = await self.planning_agent.run(query, tools=[])
        usage = getattr(response, "usage_details", None)


        input_token1=getattr(usage, "input_token_count", None)
        output_token1=getattr(usage, "output_token_count", None)
        total_token1=getattr(usage, "total_token_count", None)

        json_str = self.decode_json(response)
        plan = json.loads(json_str)
        
        print(f"\nPLAN:")
        print(f"   Servers: {', '.join(plan['servers'])}")
        for srv, tq in plan['tool_queries'].items():
            print(f"   • {srv}: '{tq}'")
        
        return plan,input_token1,output_token1,total_token1
    
    async def execute(self, query: str, tools: List[Any], thread: Optional[AgentThread] = None) -> Any:
        """Execute query with filtered tools using thread for context"""
        print(f"\nEXECUTING with {len(tools)} tools via ChatAgent Orchestrator.\n")
        
        if thread is None:
            thread = self.execution_agent.get_new_thread()
        
        response = await self.execution_agent.run(query, tools=tools, thread=thread)
        usage = getattr(response, "usage_details", None)


        input_token=getattr(usage, "input_token_count", None)
        output_token=getattr(usage, "output_token_count", None)
        total_token=getattr(usage, "total_token_count", None)

        return response, thread,input_token,output_token,total_token