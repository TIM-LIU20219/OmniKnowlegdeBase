"""Test script for Note Generation functionality."""

import json
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.note_generation_service import NoteGenerationService
from backend.app.services.workflow_orchestrator import WorkflowOrchestrator
from backend.app.utils.logging_config import setup_logging

# Setup logging
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)


def test_workflow_orchestrator():
    """Test WorkflowOrchestrator mode detection."""
    print("=" * 60)
    print("WorkflowOrchestrator Test")
    print("=" * 60)

    try:
        orchestrator = WorkflowOrchestrator()
        print("   ✓ WorkflowOrchestrator initialized")

        # Test mode detection
        test_cases = [
            ("/new Python编程基础", ("/new", "Python编程基础")),
            ("/ask 什么是RAG？", ("/ask", "什么是RAG？")),
            ("/enhance 现有内容", ("/enhance", "现有内容")),
            ("普通查询", ("default", "普通查询")),
        ]

        print("\n1. Testing mode detection...")
        for query, expected in test_cases:
            mode, actual_query = orchestrator.detect_mode(query)
            if mode == expected[0] and actual_query == expected[1]:
                print(f"   ✓ '{query}' -> mode={mode}, query='{actual_query}'")
            else:
                print(f"   ✗ '{query}' -> Expected {expected}, got ({mode}, '{actual_query}')")
                return False

        print("\n   ✓ Mode detection test passed")
        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_note_generation_service():
    """Test NoteGenerationService."""
    print("\n" + "=" * 60)
    print("NoteGenerationService Test")
    print("=" * 60)

    try:
        print("\n1. Initializing NoteGenerationService...")
        service = NoteGenerationService()
        print("   ✓ NoteGenerationService initialized")

        # Test /new mode (LLM knowledge)
        print("\n2. Testing /new mode (LLM knowledge)...")
        try:
            result = service.generate_with_llm_knowledge(
                topic="Python基础语法",
            )

            print(f"   ✓ Title: {result.get('title', 'N/A')}")
            print(f"   ✓ Content length: {len(result.get('content', ''))} chars")
            print(f"   ✓ Similar notes found: {len(result.get('similar_notes', []))}")
            print(f"   ✓ Links added: {len(result.get('added_links', []))}")
            print(f"   ✓ Suggestions: {len(result.get('suggestions', ''))} chars")

            # Show content preview
            content_preview = result.get('content', '')[:200]
            print(f"\n   Content preview:\n   {content_preview}...")

        except Exception as e:
            print(f"   ✗ Error in /new mode: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Test /ask mode (RAG)
        print("\n3. Testing /ask mode (RAG)...")
        try:
            result = service.generate_with_rag(
                question="什么是RAG？",
                strategy="hybrid",
            )

            print(f"   ✓ Title: {result.get('title', 'N/A')}")
            print(f"   ✓ Content length: {len(result.get('content', ''))} chars")
            print(f"   ✓ Sources found: {len(result.get('sources', []))}")
            print(f"   ✓ Similar notes found: {len(result.get('similar_notes', []))}")
            print(f"   ✓ Links added: {len(result.get('added_links', []))}")

            # Show content preview
            content_preview = result.get('content', '')[:200]
            print(f"\n   Content preview:\n   {content_preview}...")

            # Show sources if available
            if result.get('sources'):
                print(f"\n   Sources:")
                for i, source in enumerate(result['sources'][:3], 1):
                    print(f"     [{i}] {source.get('title', 'Unknown')} ({source.get('type', 'unknown')})")

        except Exception as e:
            print(f"   ✗ Error in /ask mode: {e}")
            import traceback
            traceback.print_exc()
            return False

        print("\n   ✓ NoteGenerationService test passed")
        return True

    except Exception as e:
        print(f"\n✗ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_integration():
    """Test full workflow integration."""
    print("\n" + "=" * 60)
    print("Workflow Integration Test")
    print("=" * 60)

    try:
        print("\n1. Initializing WorkflowOrchestrator...")
        orchestrator = WorkflowOrchestrator()
        print("   ✓ WorkflowOrchestrator initialized")

        # Test /new workflow
        print("\n2. Testing /new workflow...")
        try:
            result = orchestrator.execute("/new Python列表和字典的使用")
            print(f"   ✓ Mode: {result.get('mode')}")
            print(f"   ✓ Title: {result.get('title', 'N/A')}")
            print(f"   ✓ Content length: {len(result.get('content', ''))} chars")
            print(f"   ✓ Has suggestions: {bool(result.get('suggestions'))}")
            print(f"   ✓ Links added: {len(result.get('added_links', []))}")

        except Exception as e:
            print(f"   ✗ Error in /new workflow: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Test /ask workflow
        print("\n3. Testing /ask workflow...")
        try:
            result = orchestrator.execute("/ask 如何实现向量检索？")
            print(f"   ✓ Mode: {result.get('mode')}")
            print(f"   ✓ Title: {result.get('title', 'N/A')}")
            print(f"   ✓ Content length: {len(result.get('content', ''))} chars")
            print(f"   ✓ Has sources: {bool(result.get('sources'))}")
            print(f"   ✓ Has suggestions: {bool(result.get('suggestions'))}")

        except Exception as e:
            print(f"   ✗ Error in /ask workflow: {e}")
            import traceback
            traceback.print_exc()
            return False

        print("\n   ✓ Workflow integration test passed")
        return True

    except Exception as e:
        print(f"\n✗ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Note Generation Test Suite")
    print("=" * 60)

    results = []

    # Test 1: WorkflowOrchestrator
    results.append(("WorkflowOrchestrator", test_workflow_orchestrator()))

    # Test 2: NoteGenerationService
    results.append(("NoteGenerationService", test_note_generation_service()))

    # Test 3: Workflow Integration
    results.append(("Workflow Integration", test_workflow_integration()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


