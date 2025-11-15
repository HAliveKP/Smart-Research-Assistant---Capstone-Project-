"""
Smart Research Assistant - Multi-Agent System Capstone Project

This project demonstrates:
1. Multi-agent system (Orchestrator, Researcher, Analyzer, Writer)
2. Tools (MCP, custom tools, web search)
3. Sessions & Memory (state management, long-term memory)
4. Context engineering (compaction)
5. Observability (logging, tracing, metrics)
6. Agent evaluation

Architecture:
- Orchestrator Agent: Manages workflow and coordinates other agents
- Researcher Agent: Gathers information using web search
- Analyzer Agent: Processes and analyzes gathered data
- Writer Agent: Creates comprehensive reports
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib


# ============================================================================
# 1. OBSERVABILITY: Logging, Tracing, Metrics
# ============================================================================

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class TraceSpan:
    """Represents a trace span for observability"""
    span_id: str
    parent_id: Optional[str]
    agent_name: str
    operation: str
    start_time: float
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def duration(self) -> Optional[float]:
        if self.end_time:
            return self.end_time - self.start_time
        return None


class ObservabilitySystem:
    """Centralized logging, tracing, and metrics"""
    
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        self.traces: List[TraceSpan] = []
        self.metrics: Dict[str, List[float]] = {
            'agent_execution_time': [],
            'token_usage': [],
            'api_calls': [],
            'errors': []
        }
        self.active_spans: Dict[str, TraceSpan] = {}
    
    def log(self, level: LogLevel, agent: str, message: str, metadata: Dict = None):
        """Log a message with metadata"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'agent': agent,
            'message': message,
            'metadata': metadata or {}
        }
        self.logs.append(log_entry)
        print(f"[{level.value}] {agent}: {message}")
    
    def start_span(self, agent_name: str, operation: str, 
                   parent_id: Optional[str] = None) -> str:
        """Start a new trace span"""
        span_id = hashlib.md5(
            f"{agent_name}{operation}{time.time()}".encode()
        ).hexdigest()[:8]
        
        span = TraceSpan(
            span_id=span_id,
            parent_id=parent_id,
            agent_name=agent_name,
            operation=operation,
            start_time=time.time()
        )
        self.active_spans[span_id] = span
        self.log(LogLevel.DEBUG, agent_name, f"Started {operation}", 
                {'span_id': span_id})
        return span_id
    
    def end_span(self, span_id: str, metadata: Dict = None):
        """End a trace span"""
        if span_id in self.active_spans:
            span = self.active_spans[span_id]
            span.end_time = time.time()
            span.metadata = metadata or {}
            self.traces.append(span)
            del self.active_spans[span_id]
            
            self.metrics['agent_execution_time'].append(span.duration())
            self.log(LogLevel.DEBUG, span.agent_name, 
                    f"Completed {span.operation} in {span.duration():.2f}s",
                    {'span_id': span_id})
    
    def record_metric(self, metric_name: str, value: float):
        """Record a metric value"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {}
        for metric_name, values in self.metrics.items():
            if values:
                summary[metric_name] = {
                    'count': len(values),
                    'sum': sum(values),
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values)
                }
        return summary


# ============================================================================
# 2. SESSIONS & MEMORY: State Management & Long-term Memory
# ============================================================================

@dataclass
class ResearchSession:
    """Represents a research session"""
    session_id: str
    topic: str
    created_at: float
    state: Dict[str, Any]
    conversation_history: List[Dict[str, str]]


class InMemorySessionService:
    """Manages research sessions and state"""
    
    def __init__(self):
        self.sessions: Dict[str, ResearchSession] = {}
    
    def create_session(self, topic: str) -> str:
        """Create a new research session"""
        session_id = hashlib.md5(f"{topic}{time.time()}".encode()).hexdigest()[:12]
        session = ResearchSession(
            session_id=session_id,
            topic=topic,
            created_at=time.time(),
            state={'stage': 'initialized', 'results': {}},
            conversation_history=[]
        )
        self.sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        """Retrieve a session"""
        return self.sessions.get(session_id)
    
    def update_session_state(self, session_id: str, updates: Dict[str, Any]):
        """Update session state"""
        if session_id in self.sessions:
            self.sessions[session_id].state.update(updates)
    
    def add_to_history(self, session_id: str, role: str, content: str):
        """Add message to conversation history"""
        if session_id in self.sessions:
            self.sessions[session_id].conversation_history.append({
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat()
            })


class MemoryBank:
    """Long-term memory storage for learned patterns and insights"""
    
    def __init__(self):
        self.research_patterns: Dict[str, List[str]] = {}
        self.topic_insights: Dict[str, Dict[str, Any]] = {}
        self.successful_queries: List[Dict[str, Any]] = []
    
    def store_research_pattern(self, topic_category: str, pattern: str):
        """Store a successful research pattern"""
        if topic_category not in self.research_patterns:
            self.research_patterns[topic_category] = []
        self.research_patterns[topic_category].append(pattern)
    
    def store_topic_insight(self, topic: str, insights: Dict[str, Any]):
        """Store insights about a topic"""
        self.topic_insights[topic] = {
            'insights': insights,
            'timestamp': time.time()
        }
    
    def get_relevant_patterns(self, topic_category: str) -> List[str]:
        """Retrieve relevant research patterns"""
        return self.research_patterns.get(topic_category, [])
    
    def store_successful_query(self, query: str, results_quality: float):
        """Store information about successful queries"""
        self.successful_queries.append({
            'query': query,
            'quality': results_quality,
            'timestamp': time.time()
        })


# ============================================================================
# 3. CONTEXT ENGINEERING: Context Compaction
# ============================================================================

class ContextCompactor:
    """Compacts context to fit within token limits"""
    
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count"""
        return len(text.split()) * 1.3
    
    def compact_search_results(self, results: List[Dict[str, str]]) -> str:
        """Compact search results to essential information"""
        compacted = []
        total_tokens = 0
        
        for i, result in enumerate(results):
            # Extract key information
            summary = f"Source {i+1}: {result.get('title', 'N/A')}\n"
            summary += f"Key points: {result.get('snippet', '')[:200]}...\n"
            
            tokens = self.estimate_tokens(summary)
            if total_tokens + tokens > self.max_tokens:
                break
            
            compacted.append(summary)
            total_tokens += tokens
        
        return "\n".join(compacted)
    
    def compact_conversation_history(self, 
                                     history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Keep only the most recent and relevant messages"""
        # Keep last 5 messages and summarize older ones
        if len(history) <= 5:
            return history
        
        recent = history[-5:]
        older_summary = {
            'role': 'system',
            'content': f"Previous conversation covered {len(history) - 5} messages about the research topic."
        }
        return [older_summary] + recent


# ============================================================================
# 4. TOOLS: Custom Tools & MCP Integration
# ============================================================================

class WebSearchTool:
    """Simulated web search tool (in production, would use real API)"""
    
    def __init__(self, observability: ObservabilitySystem):
        self.obs = observability
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Perform web search"""
        span_id = self.obs.start_span("WebSearchTool", "search")
        
        # Simulate API call
        await asyncio.sleep(0.5)
        
        # Simulated results
        results = [
            {
                'title': f'Result {i+1} for: {query}',
                'snippet': f'This is relevant information about {query}. It contains important details and insights that are useful for research.',
                'url': f'https://example.com/result{i+1}'
            }
            for i in range(num_results)
        ]
        
        self.obs.record_metric('api_calls', 1)
        self.obs.end_span(span_id, {'results_count': len(results)})
        
        return results


class DataAnalysisTool:
    """Custom tool for analyzing research data"""
    
    def __init__(self, observability: ObservabilitySystem):
        self.obs = observability
    
    async def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text"""
        span_id = self.obs.start_span("DataAnalysisTool", "sentiment_analysis")
        
        # Simulated analysis
        await asyncio.sleep(0.3)
        result = {
            'positive': 0.6,
            'neutral': 0.3,
            'negative': 0.1
        }
        
        self.obs.end_span(span_id, result)
        return result
    
    async def extract_key_topics(self, text: str) -> List[str]:
        """Extract key topics from text"""
        span_id = self.obs.start_span("DataAnalysisTool", "topic_extraction")
        
        await asyncio.sleep(0.2)
        # Simple word frequency-based extraction (simulated)
        topics = ['AI', 'machine learning', 'neural networks', 'data science']
        
        self.obs.end_span(span_id, {'topics_found': len(topics)})
        return topics


class MCPServerConnection:
    """Model Context Protocol server connection (simulated)"""
    
    def __init__(self, server_name: str, observability: ObservabilitySystem):
        self.server_name = server_name
        self.obs = observability
        self.connected = False
    
    async def connect(self):
        """Connect to MCP server"""
        span_id = self.obs.start_span("MCPServer", "connect")
        await asyncio.sleep(0.1)
        self.connected = True
        self.obs.end_span(span_id, {'server': self.server_name})
    
    async def invoke_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Invoke a tool via MCP"""
        if not self.connected:
            await self.connect()
        
        span_id = self.obs.start_span("MCPServer", f"invoke_{tool_name}")
        await asyncio.sleep(0.2)
        
        result = {'status': 'success', 'data': f'Result from {tool_name}'}
        self.obs.end_span(span_id, {'tool': tool_name})
        return result


# ============================================================================
# 5. MULTI-AGENT SYSTEM: Sequential & Parallel Agents
# ============================================================================

class Agent:
    """Base agent class"""
    
    def __init__(self, name: str, role: str, observability: ObservabilitySystem):
        self.name = name
        self.role = role
        self.obs = observability
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent task - to be implemented by subclasses"""
        raise NotImplementedError


class ResearcherAgent(Agent):
    """Agent responsible for gathering information"""
    
    def __init__(self, observability: ObservabilitySystem):
        super().__init__("Researcher", "Information Gathering", observability)
        self.search_tool = WebSearchTool(observability)
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather research information"""
        span_id = self.obs.start_span(self.name, "research")
        
        topic = task.get('topic', '')
        self.obs.log(LogLevel.INFO, self.name, f"Researching topic: {topic}")
        
        # Generate search queries
        queries = [
            f"{topic} overview",
            f"{topic} recent developments",
            f"{topic} key concepts",
            f"{topic} applications"
        ]
        
        # Perform searches (parallel execution)
        search_tasks = [self.search_tool.search(q, num_results=3) for q in queries]
        results = await asyncio.gather(*search_tasks)
        
        # Flatten results
        all_results = [item for sublist in results for item in sublist]
        
        self.obs.end_span(span_id, {'sources_found': len(all_results)})
        
        return {
            'status': 'completed',
            'sources': all_results,
            'queries_used': queries
        }


class AnalyzerAgent(Agent):
    """Agent responsible for analyzing gathered data"""
    
    def __init__(self, observability: ObservabilitySystem):
        super().__init__("Analyzer", "Data Analysis", observability)
        self.analysis_tool = DataAnalysisTool(observability)
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze research data"""
        span_id = self.obs.start_span(self.name, "analysis")
        
        sources = task.get('sources', [])
        self.obs.log(LogLevel.INFO, self.name, f"Analyzing {len(sources)} sources")
        
        # Combine all text
        combined_text = " ".join([s.get('snippet', '') for s in sources])
        
        # Parallel analysis
        sentiment_task = self.analysis_tool.analyze_sentiment(combined_text)
        topics_task = self.analysis_tool.extract_key_topics(combined_text)
        
        sentiment, topics = await asyncio.gather(sentiment_task, topics_task)
        
        analysis = {
            'sentiment': sentiment,
            'key_topics': topics,
            'source_quality': len(sources) / 10.0,  # Simple quality metric
            'coverage': 'comprehensive' if len(sources) > 10 else 'basic'
        }
        
        self.obs.end_span(span_id, {'topics_found': len(topics)})
        
        return {
            'status': 'completed',
            'analysis': analysis
        }


class WriterAgent(Agent):
    """Agent responsible for creating reports"""
    
    def __init__(self, observability: ObservabilitySystem):
        super().__init__("Writer", "Report Generation", observability)
        self.context_compactor = ContextCompactor()
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate research report"""
        span_id = self.obs.start_span(self.name, "write_report")
        
        topic = task.get('topic', '')
        sources = task.get('sources', [])
        analysis = task.get('analysis', {})
        
        self.obs.log(LogLevel.INFO, self.name, f"Writing report on: {topic}")
        
        # Compact sources for report
        compacted_sources = self.context_compactor.compact_search_results(sources)
        
        # Generate report structure
        report = {
            'title': f"Research Report: {topic}",
            'summary': f"Comprehensive analysis of {topic} based on {len(sources)} sources.",
            'key_findings': analysis.get('key_topics', []),
            'sentiment_analysis': analysis.get('sentiment', {}),
            'quality_score': analysis.get('source_quality', 0),
            'sources_summary': compacted_sources,
            'generated_at': datetime.now().isoformat()
        }
        
        await asyncio.sleep(0.5)  # Simulate report generation
        
        self.obs.end_span(span_id, {'report_sections': len(report)})
        
        return {
            'status': 'completed',
            'report': report
        }


class OrchestratorAgent(Agent):
    """Main orchestrator that coordinates other agents"""
    
    def __init__(self, observability: ObservabilitySystem, 
                 session_service: InMemorySessionService,
                 memory_bank: MemoryBank):
        super().__init__("Orchestrator", "Workflow Coordination", observability)
        self.session_service = session_service
        self.memory_bank = memory_bank
        
        # Initialize sub-agents
        self.researcher = ResearcherAgent(observability)
        self.analyzer = AnalyzerAgent(observability)
        self.writer = WriterAgent(observability)
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate the research workflow"""
        span_id = self.obs.start_span(self.name, "orchestrate_research")
        
        topic = task.get('topic', '')
        session_id = task.get('session_id')
        
        self.obs.log(LogLevel.INFO, self.name, 
                    f"Starting research workflow for: {topic}")
        
        try:
            # SEQUENTIAL EXECUTION: Research → Analyze → Write
            
            # Step 1: Research
            self.obs.log(LogLevel.INFO, self.name, "Step 1: Gathering information")
            research_result = await self.researcher.execute(
                {'topic': topic}, context
            )
            
            if session_id:
                self.session_service.update_session_state(
                    session_id, {'stage': 'research_complete'}
                )
            
            # Step 2: Analyze
            self.obs.log(LogLevel.INFO, self.name, "Step 2: Analyzing data")
            analysis_result = await self.analyzer.execute(
                {'sources': research_result['sources']}, context
            )
            
            if session_id:
                self.session_service.update_session_state(
                    session_id, {'stage': 'analysis_complete'}
                )
            
            # Step 3: Write Report
            self.obs.log(LogLevel.INFO, self.name, "Step 3: Generating report")
            report_result = await self.writer.execute(
                {
                    'topic': topic,
                    'sources': research_result['sources'],
                    'analysis': analysis_result['analysis']
                }, 
                context
            )
            
            if session_id:
                self.session_service.update_session_state(
                    session_id, {
                        'stage': 'completed',
                        'results': report_result['report']
                    }
                )
            
            # Store insights in long-term memory
            self.memory_bank.store_topic_insight(topic, {
                'quality': analysis_result['analysis'].get('source_quality', 0),
                'topics': analysis_result['analysis'].get('key_topics', [])
            })
            
            self.obs.end_span(span_id, {'workflow': 'completed'})
            
            return {
                'status': 'success',
                'report': report_result['report'],
                'metadata': {
                    'sources_analyzed': len(research_result['sources']),
                    'topics_identified': len(analysis_result['analysis'].get('key_topics', []))
                }
            }
            
        except Exception as e:
            self.obs.log(LogLevel.ERROR, self.name, f"Workflow failed: {str(e)}")
            self.obs.record_metric('errors', 1)
            self.obs.end_span(span_id, {'error': str(e)})
            
            return {
                'status': 'error',
                'error': str(e)
            }


# ============================================================================
# 6. AGENT EVALUATION
# ============================================================================

class AgentEvaluator:
    """Evaluates agent performance"""
    
    def __init__(self, observability: ObservabilitySystem):
        self.obs = observability
    
    def evaluate_research_quality(self, result: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate the quality of research results"""
        evaluation = {
            'completeness': 0.0,
            'accuracy': 0.0,
            'relevance': 0.0,
            'timeliness': 0.0,
            'overall': 0.0
        }
        
        metadata = result.get('metadata', {})
        
        # Completeness: based on number of sources
        sources_count = metadata.get('sources_analyzed', 0)
        evaluation['completeness'] = min(sources_count / 15.0, 1.0)
        
        # Relevance: based on topics identified
        topics_count = metadata.get('topics_identified', 0)
        evaluation['relevance'] = min(topics_count / 5.0, 1.0)
        
        # Accuracy & Timeliness (simulated - would use real metrics)
        evaluation['accuracy'] = 0.85
        evaluation['timeliness'] = 0.90
        
        # Overall score
        evaluation['overall'] = sum(evaluation.values()) / 5.0
        
        self.obs.log(LogLevel.INFO, "Evaluator", 
                    f"Research quality score: {evaluation['overall']:.2f}")
        
        return evaluation
    
    def evaluate_agent_performance(self) -> Dict[str, Any]:
        """Evaluate overall agent system performance"""
        metrics = self.obs.get_metrics_summary()
        
        performance = {
            'avg_execution_time': metrics.get('agent_execution_time', {}).get('avg', 0),
            'total_api_calls': metrics.get('api_calls', {}).get('sum', 0),
            'error_rate': len(self.obs.metrics.get('errors', [])) / max(len(self.obs.logs), 1),
            'trace_count': len(self.obs.traces)
        }
        
        return performance


# ============================================================================
# 7. MAIN APPLICATION
# ============================================================================

class ResearchAssistantSystem:
    """Main multi-agent research assistant system"""
    
    def __init__(self):
        self.observability = ObservabilitySystem()
        self.session_service = InMemorySessionService()
        self.memory_bank = MemoryBank()
        self.orchestrator = OrchestratorAgent(
            self.observability, 
            self.session_service,
            self.memory_bank
        )
        self.evaluator = AgentEvaluator(self.observability)
        self.mcp_server = MCPServerConnection("research-tools", self.observability)
    
    async def conduct_research(self, topic: str) -> Dict[str, Any]:
        """Main entry point for conducting research"""
        # Create session
        session_id = self.session_service.create_session(topic)
        self.observability.log(LogLevel.INFO, "System", 
                              f"Created session {session_id} for topic: {topic}")
        
        # Connect to MCP server
        await self.mcp_server.connect()
        
        # Execute research workflow
        result = await self.orchestrator.execute(
            {'topic': topic, 'session_id': session_id},
            {'mcp_server': self.mcp_server}
        )
        
        # Evaluate results
        evaluation = self.evaluator.evaluate_research_quality(result)
        result['evaluation'] = evaluation
        
        # Get performance metrics
        performance = self.evaluator.evaluate_agent_performance()
        result['performance_metrics'] = performance
        
        return result
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session"""
        session = self.session_service.get_session(session_id)
        if session:
            return asdict(session)
        return None
    
    def get_observability_report(self) -> Dict[str, Any]:
        """Get complete observability report"""
        return {
            'logs': self.observability.logs[-20:],  # Last 20 logs
            'traces': [asdict(t) for t in self.observability.traces],
            'metrics': self.observability.get_metrics_summary()
        }


# ============================================================================
# 8. USAGE EXAMPLE
# ============================================================================

async def main():
    """Example usage of the research assistant system"""
    
    print("=" * 80)
    print("SMART RESEARCH ASSISTANT - CAPSTONE PROJECT")
    print("=" * 80)
    print()
    
    # Initialize system
    system = ResearchAssistantSystem()
    
    # Conduct research
    topic = "Artificial Intelligence in Healthcare"
    print(f"Starting research on: {topic}")
    print("-" * 80)
    
    result = await system.conduct_research(topic)
    
    # Display results
    print("\n" + "=" * 80)
    print("RESEARCH RESULTS")
    print("=" * 80)
    
    if result['status'] == 'success':
        report = result['report']
        print(f"\nTitle: {report['title']}")
        print(f"Summary: {report['summary']}")
        print(f"\nKey Findings: {', '.join(report['key_findings'])}")
        print(f"Quality Score: {report['quality_score']:.2f}")
        print(f"Generated: {report['generated_at']}")
        
        print("\n" + "=" * 80)
        print("EVALUATION METRICS")
        print("=" * 80)
        evaluation = result['evaluation']
        print(f"Overall Quality: {evaluation['overall']:.2%}")
        print(f"Completeness: {evaluation['completeness']:.2%}")
        print(f"Relevance: {evaluation['relevance']:.2%}")
        print(f"Accuracy: {evaluation['accuracy']:.2%}")
        
        print("\n" + "=" * 80)
        print("PERFORMANCE METRICS")
        print("=" * 80)
        perf = result['performance_metrics']
        print(f"Avg Execution Time: {perf['avg_execution_time']:.2f}s")
        print(f"Total API Calls: {int(perf['total_api_calls'])}")
        print(f"Error Rate: {perf['error_rate']:.2%}")
        print(f"Trace Count: {perf['trace_count']}")
        
        print("\n" + "=" * 80)
        print("OBSERVABILITY REPORT (Last 10 Logs)")
        print("=" * 80)
        obs_report = system.get_observability_report()
        for log in obs_report['logs'][-10:]:
            print(f"[{log['level']}] {log['agent']}: {log['message']}")
    
    else:
        print(f"Research failed: {result.get('error')}")
    
    print("\n" + "=" * 80)
    print("PROJECT REQUIREMENTS DEMONSTRATED:")
    print("=" * 80)
    print("✓ Multi-agent system (Orchestrator, Researcher, Analyzer, Writer)")
    print("✓ Sequential agent execution (Research → Analyze → Write)")
    print("✓ Parallel execution (Multiple search queries, analysis tasks)")
    print("✓ Tools: Custom tools (DataAnalysisTool, WebSearchTool)")
    print("✓ MCP integration (MCPServerConnection)")
    print("✓ Sessions & State Management (InMemorySessionService)")
    print("✓ Long-term Memory (MemoryBank)")
    print("✓ Context Engineering (ContextCompactor)")
    print("✓ Observability: Logging, Tracing, Metrics (ObservabilitySystem)")
    print("✓ Agent Evaluation (AgentEvaluator)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
