"""Test script for Agentic Search functionality."""

import json
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.agent_executor import AgentExecutor
from backend.app.services.agentic_search_service import AgenticSearchService
from backend.app.services.agent_tools import AgentTools
from backend.app.services.embedding_service import EmbeddingService
from backend.app.services.llm_service import LLMService
from backend.app.services.note_file_service import NoteFileService
from backend.app.services.note_metadata_service import NoteMetadataService
from backend.app.services.vector_service import VectorService
from backend.app.utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def test_agentic_search():
    """Test Agentic Search functionality."""
    print("=" * 60)
    print("Agentic Search Test")
    print("=" * 60)
    
    try:
        # Initialize services
        print("\n1. Initializing services...")
        vector_service = VectorService()
        embedding_service = EmbeddingService()
        llm_service = LLMService()
        note_metadata_service = NoteMetadataService()
        note_file_service = NoteFileService()
        
        print(f"   ✓ LLM Provider: {llm_service.config.provider.value}")
        print(f"   ✓ LLM Model: {llm_service.config.model}")
        print(f"   ✓ API Base: {llm_service.config.api_base}")
        
        # Initialize tools
        print("\n2. Initializing Agent Tools...")
        tools = AgentTools(
            note_metadata_service=note_metadata_service,
            note_file_service=note_file_service,
            vector_service=vector_service,
            embedding_service=embedding_service,
            collection_name="documents",
        )
        print(f"   ✓ Loaded {len(tools.get_tool_definitions())} tools")
        
        # Initialize agentic search service
        print("\n3. Initializing Agentic Search Service...")
        agentic_search_service = AgenticSearchService(tools=tools)
        print("   ✓ Agentic Search Service ready")
        
        # Initialize agent executor
        print("\n4. Initializing Agent Executor...")
        executor = AgentExecutor(
            llm_service=llm_service,
            agentic_search_service=agentic_search_service,
            max_iterations=5,
        )
        print("   ✓ Agent Executor ready")
        
        # Test queries
        test_queries = [
            "列出所有笔记",
            "搜索关于RAG的笔记",
            "有哪些笔记包含标签？",
        ]
        
        print("\n" + "=" * 60)
        print("Running Test Queries")
        print("=" * 60)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n[Test {i}] Query: {query}")
            print("-" * 60)
            
            try:
                result = executor.execute(query)
                
                print(f"\n✓ Answer:")
                print(result["answer"])
                print(f"\n✓ Iterations: {result['iterations']}")
                print(f"✓ Tool Calls: {len(result['tool_calls'])}")
                
                if result["tool_calls"]:
                    print("\nTool Call Details:")
                    for j, tool_call in enumerate(result["tool_calls"], 1):
                        print(f"  [{j}] {tool_call['tool_name']}")
                        print(f"      Args: {json.dumps(tool_call['tool_args'], ensure_ascii=False)}")
                        result_preview = str(tool_call.get('result', ''))[:100]
                        print(f"      Result: {result_preview}...")
                
                if result.get("max_iterations_reached"):
                    print("\n⚠️  Warning: Maximum iterations reached")
                
            except Exception as e:
                print(f"\n✗ Error: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_agentic_search()
    sys.exit(0 if success else 1)

