"""LEAP Sequential Orchestrator.

The core innovation: Sequential orchestration that enables 4GB VRAM deployment.

Traditional approach:
- Load all tool schemas (15,000 tokens) with agent
- Single model processes everything
- OOM or extreme slowdown on 4GB

LEAP approach:
- Phase 1: Main agent with minimal catalogue → Generate tool request
- Phase 2: Subagent executes tool → Filter response  
- Phase 3: Main agent with filtered response → Generate answer
- Only one model in VRAM at a time → Works on 4GB!
"""
import json
import time
import re
from typing import Optional
from dataclasses import dataclass, field

from .config import LEAPConfig
from .catalogue import get_catalogue_prompt, TOOL_SPECS
from .inference import OllamaInference


@dataclass
class OrchestrationMetrics:
    """Track orchestration performance."""
    phase1_time: float = 0.0  # Main agent planning
    phase2_time: float = 0.0  # Subagent execution
    phase3_time: float = 0.0  # Main agent response
    total_time: float = 0.0
    tool_name: str = ""
    raw_response_tokens: int = 0
    filtered_response_tokens: int = 0
    token_reduction: float = 0.0


class LEAPOrchestrator:
    """LEAP Agent with sequential orchestration for 4GB VRAM."""
    
    def __init__(self, config: Optional[LEAPConfig] = None):
        self.config = config or LEAPConfig()
        self.inference = OllamaInference(self.config)
        self.metrics = OrchestrationMetrics()
        self.history: list = []
        
        # Import tools
        self.tools = self._load_tools()
        
        if self.config.warmup_models:
            self.inference.warmup()
    
    def _load_tools(self) -> dict:
        """Load tool functions."""
        from .tools import file_tools, shell_tools, web_tools, code_tools, utility_tools
        
        return {
            "read_file": file_tools.read_file,
            "write_file": file_tools.write_file,
            "replace_in_file": file_tools.replace_in_file,
            "insert_in_file": file_tools.insert_in_file,
            "list_directory": file_tools.list_directory,
            "search_files": file_tools.search_files,
            "file_info": file_tools.file_info,
            "run_shell_command": shell_tools.run_command,
            "get_shell_env": shell_tools.get_environment,
            "web_search": web_tools.web_search,
            "news_search": web_tools.news_search,
            "fetch_url": web_tools.fetch_url,
            "crawl_webpage": web_tools.crawl_webpage,
            "analyze_code": code_tools.analyze_code,
            "grep_code": code_tools.grep_code,
            "find_definition": code_tools.find_definition,
            "read_definition": code_tools.read_definition,
            "replace_definition": code_tools.replace_definition,
            "calculate": utility_tools.calculate,
            "get_current_time": utility_tools.get_datetime,
            "parse_json": utility_tools.json_parse,
        }
    
    def run(self, query: str, max_turns: int = 15) -> str:
        """Process a user query through the LEAP pipeline (Rolling O(1) State)."""
        self.state_summary = "No actions taken yet."
        total_start = time.time()
        
        if self.config.verbose:
            print(f"\n{'='*60}")
            print(f"LEAP Processing (Limit {max_turns} turns): {query[:50]}...")
            print(f"{'='*60}")
        
        current_turn = 1
        
        while current_turn <= max_turns:
            if self.config.verbose:
                print(f"\n🔄 Turn {current_turn}/{max_turns}")
                print(f"📝 Current State: {self.state_summary[:100]}...")
            
            # Phase 1: Planning (Main agent)
            phase1_start = time.time()
            tool_request = self._phase1_planning(query)
            self.metrics.phase1_time += time.time() - phase1_start
            
            # If no tool selected in Phase 1...
            if tool_request is None:
                if current_turn == 1:
                    return self._direct_response(query)
                else:
                    if self.config.verbose:
                        print("✅ Agent decided to finish")
                    break

            if self.config.verbose:
                print(f"✅ Phase 1: Tool request - {tool_request.get('tool', 'unknown')}")
            
            # Phase 2: Execution (Subagent)
            phase2_start = time.time()
            filtered_response = self._phase2_execution(tool_request)
            self.metrics.phase2_time += time.time() - phase2_start
            
            if self.config.verbose:
                print(f"✅ Phase 2: Tool executed")
            
            # Phase 3: Update State (Main Agent - Rolling Summary)
            # Input: Query + Old State + New Tool Result
            # Output: New State Summary
            phase3_start = time.time()
            self._phase3_update_state(query, tool_request, filtered_response)
            self.metrics.phase3_time += time.time() - phase3_start
            
            current_turn += 1
        
        # Final Response Generation
        final_answer = self._generate_final_answer(query)
        
        if self.config.verbose:
            print(f"✅ Final answer generated")
            self._print_metrics()
            
        return final_answer

    def _generate_final_answer(self, query: str) -> str:
        """Generate final answer from rolling state summary."""
        prompt = f"""User query: {query}

Summary of actions taken:
{self.state_summary}

Based on this summary, provide the final answer to the user request.
If you created files or verified code, report what was done."""

        return self.inference.generate(
            model=self.config.main_model,
            prompt=prompt,
            temperature=self.config.main_temperature,
            max_tokens=1024
        )
    
    def _phase1_planning(self, query: str) -> Optional[dict]:
        """Phase 1: Main agent decides NEXT tool using Rolling State."""
        catalogue = get_catalogue_prompt()
        
        prompt = f"""You are an autonomous engineer. Your job is to SOLVE the task, not just explain it.

{catalogue}

User request: {query}

Current Progress:
{self.state_summary}

RULES:
1. Do NOT explain code in chat. Use tools (`fs_write`, `fs_replace`) to APPLY changes.
2. If the user asks for time/date, you MUST use `get_current_time`.
3. If the user asks about files, ALWAYS check with `fs_list` or `fs_read` first.
4. Only reply with "null" if the task is FULLY COMPLETE (e.g., answer is final).
5. Prefer using tools over guessing.

Which tool should be used NEXT? Reply with JSON only:
{{"tool": "tool_name", "params": {{"key": "value"}}, "filter": ["field1"]}}

If the task is complete, return:
{{"tool": null}}

Examples:
- List files → {{"tool": "fs_list", "params": {{"path": "directory_name"}} }}
- Replace text → {{"tool": "fs_replace", "params": {{"path": "file.py", "old_text": "foo", "new_text": "bar"}} }}

Your JSON answer:"""
        
        response = self.inference.generate(
            model=self.config.main_model,
            prompt=prompt,
            temperature=0.5,
            max_tokens=300
        )
        
        if self.config.verbose:
            print(f"📝 Model response: {response[:150]}...")
        
        return self._parse_tool_request(response)

    def _phase3_update_state(self, query: str, tool_request: dict, tool_result: str):
        """Phase 3: Update the rolling state summary."""
        prompt = f"""Update the progress summary for this task.
        
User Request: {query}

Old Summary:
{self.state_summary}

New Action: Used {tool_request.get("tool")}
Result: {tool_result[:1000]}

Write a concise, updated summary of what has been done so far. 
Do not lose important details from the Old Summary.
Merge the New Action into the summary.
Keep it under 300 words.

Updated Summary:"""

        response = self.inference.generate(
            model=self.config.main_model,
            prompt=prompt,
            temperature=0.5,
            max_tokens=512
        )
        # Clean thinking tags
        self.state_summary = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
    
    def _parse_tool_request(self, response: str) -> Optional[dict]:
        """Extract JSON tool request from model response."""
        # Remove thinking tags if present
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        response = response.strip()
        
        # Try direct JSON parse first (most reliable)
        try:
            parsed = json.loads(response)
            if isinstance(parsed, dict) and 'tool' in parsed:
                if parsed.get('tool') is None or parsed.get('tool') == 'null':
                    return None
                return parsed
        except json.JSONDecodeError:
            pass
        
        # Find JSON with balanced braces
        def extract_json_object(text: str) -> Optional[str]:
            start = text.find('{')
            if start == -1:
                return None
            depth = 0
            for i, c in enumerate(text[start:], start):
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        return text[start:i+1]
            return None
        
        json_str = extract_json_object(response)
        if json_str:
            try:
                parsed = json.loads(json_str)
                if isinstance(parsed, dict) and 'tool' in parsed:
                    if parsed.get('tool') is None or parsed.get('tool') == 'null':
                        return None
                    return parsed
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _phase2_execution(self, tool_request: dict) -> str:
        """Phase 2: Execute tool and filter response.
        
        The subagent:
        1. Executes the actual tool
        2. Filters response to only requested fields
        3. Returns minimal data to main agent
        """
        tool_name = tool_request.get('tool')
        params = tool_request.get('params', {})
        filter_fields = tool_request.get('filter', [])
        
        self.metrics.tool_name = tool_name
        
        if self.config.verbose:
            print(f"🔧 Executing: {tool_name}")
            if params:
                print(f"   Params: {json.dumps(params, indent=2)}")

        # Execute tool
        if tool_name not in self.tools:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        
        try:
            tool_func = self.tools[tool_name]
            raw_result = tool_func(**params) if params else tool_func()
        except Exception as e:
            return json.dumps({"error": str(e)})
        
        # Track raw response size
        raw_json = json.dumps(raw_result) if isinstance(raw_result, dict) else str(raw_result)
        
        if self.config.verbose:
            preview = raw_json[:200] + "..." if len(raw_json) > 200 else raw_json
            print(f"✅ Result: {preview}")
            
        self.metrics.raw_response_tokens = len(raw_json) // 4
        
        # Filter response using subagent
        if self.config.enable_filtering and filter_fields:
            filtered = self._filter_response(raw_result, filter_fields)
        else:
            filtered = raw_result
        
        # Track filtered response size
        filtered_json = json.dumps(filtered) if isinstance(filtered, dict) else str(filtered)
        self.metrics.filtered_response_tokens = len(filtered_json) // 4
        
        if self.metrics.raw_response_tokens > 0:
            self.metrics.token_reduction = (
                1 - self.metrics.filtered_response_tokens / self.metrics.raw_response_tokens
            ) * 100
        
        return filtered_json
    
    def _filter_response(self, raw_result: any, filter_fields: list) -> dict:
        """Use subagent to filter response to only needed fields."""
        if isinstance(raw_result, str):
            # If already string, try to extract key info
            return {"content": raw_result[:1000]}
        
        if not isinstance(raw_result, dict):
            return {"result": str(raw_result)[:1000]}
        
        # For dict responses, use subagent to filter intelligently
        raw_json = json.dumps(raw_result, indent=2)
        
        # If raw response is small, don't bother filtering
        if len(raw_json) < 500:
            return raw_result
        
        prompt = f"""Extract only these fields from the data: {filter_fields}

Data:
{raw_json[:3000]}

Return ONLY a compact JSON with the requested fields. No explanation."""
        
        response = self.inference.generate(
            model=self.config.sub_model,
            prompt=prompt,
            temperature=self.config.sub_temperature,
            max_tokens=512
        )
        
        # Parse filtered result
        try:
            # Remove thinking tags
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
            json_match = re.search(r'[\{\[].*[\}\]]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Fallback: simple field extraction
        filtered = {}
        for field in filter_fields:
            if field in raw_result:
                filtered[field] = raw_result[field]
        return filtered if filtered else raw_result
    
    def _phase3_response(self, query: str, tool_result: str) -> str:
        """Phase 3: Generate final answer from filtered response."""
        prompt = f"""User query: {query}

Tool result:
{tool_result}

Provide a clear, helpful answer based on this data."""
        
        response = self.inference.generate(
            model=self.config.main_model,
            prompt=prompt,
            temperature=self.config.main_temperature,
            max_tokens=1024
        )
        
        # Clean up response (remove thinking tags)
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        
        return response
    
    def _direct_response(self, query: str) -> str:
        """Handle queries that don't need tools (including code writing)."""
        # Better prompt for coding and general queries
        prompt = f"""You are a helpful AI assistant. Respond to the user's request directly.

User request: {query}

If the request is for code, provide complete working code with explanations.
If the request is a question, provide a clear and helpful answer.

Your response:"""
        
        response = self.inference.generate(
            model=self.config.main_model,
            prompt=prompt,
            temperature=self.config.main_temperature,
            max_tokens=2048  # More tokens for code generation
        )
        
        # Clean up response (remove thinking tags)
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        
        # Fallback if response is empty
        if not response or len(response) < 10:
            if self.config.verbose:
                print("⚠️ Empty response, retrying with higher temperature...")
            response = self.inference.generate(
                model=self.config.main_model,
                prompt=prompt,
                temperature=0.8,
                max_tokens=2048
            )
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        
        return response
    
    def _print_metrics(self):
        """Print orchestration metrics."""
        print(f"\n📊 LEAP Metrics:")
        print(f"   Phase 1 (Planning):  {self.metrics.phase1_time:.1f}s")
        print(f"   Phase 2 (Execution): {self.metrics.phase2_time:.1f}s")
        print(f"   Phase 3 (Response):  {self.metrics.phase3_time:.1f}s")
        print(f"   Total:               {self.metrics.total_time:.1f}s")
        print(f"   Tool: {self.metrics.tool_name}")
        print(f"   Token reduction: {self.metrics.token_reduction:.0f}%")
    
    def get_metrics(self) -> dict:
        """Get orchestration metrics."""
        return {
            "phase1_time": self.metrics.phase1_time,
            "phase2_time": self.metrics.phase2_time,
            "phase3_time": self.metrics.phase3_time,
            "total_time": self.metrics.total_time,
            "tool": self.metrics.tool_name,
            "raw_tokens": self.metrics.raw_response_tokens,
            "filtered_tokens": self.metrics.filtered_response_tokens,
            "token_reduction": f"{self.metrics.token_reduction:.0f}%",
        }
    
    def get_available_tools(self) -> list[str]:
        """List available tool names."""
        return list(self.tools.keys())
