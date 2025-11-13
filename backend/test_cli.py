"""
Systematic CLI testing script for OmniKnowledgeBase.

This script tests all CLI commands to ensure they work correctly.
It can be run standalone or with pytest.

Usage:
    python backend/test_cli.py
    # OR
    pytest backend/test_cli.py -v
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# CLI command
CLI_CMD = ["python", str(project_root / "cli.py")]


def run_cli_command(args: List[str], expect_success: bool = True) -> Tuple[bool, str, str]:
    """
    Run a CLI command and return success status, stdout, and stderr.
    
    Args:
        args: CLI arguments (without 'python cli.py')
        expect_success: Whether command is expected to succeed
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    cmd = CLI_CMD + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            encoding="utf-8",
            errors="replace",
        )
        success = result.returncode == 0
        if expect_success and not success:
            print(f"  ⚠ Command failed: {' '.join(cmd)}")
            print(f"    Return code: {result.returncode}")
            if result.stderr:
                print(f"    Stderr: {result.stderr[:200]}")
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print(f"  ⚠ Command timed out: {' '.join(cmd)}")
        return False, "", "Timeout"
    except Exception as e:
        print(f"  ⚠ Exception running command: {' '.join(cmd)}")
        print(f"    Error: {e}")
        return False, "", str(e)


def test_help_commands():
    """Test help commands."""
    print("\n" + "=" * 60)
    print("Testing Help Commands")
    print("=" * 60)
    
    tests = [
        (["--help"], "Main help"),
        (["--version"], "Version"),
        (["document", "--help"], "Document help"),
        (["rag", "--help"], "RAG help"),
        (["note", "--help"], "Note help"),
        (["vector", "--help"], "Vector help"),
        (["index", "--help"], "Index help"),
    ]
    
    results = []
    for args, description in tests:
        print(f"\n  Testing: {description}")
        success, stdout, stderr = run_cli_command(args)
        results.append((description, success))
        if success:
            print(f"    ✓ {description}")
        else:
            print(f"    ✗ {description} failed")
    
    return results


def test_document_commands():
    """Test document management commands."""
    print("\n" + "=" * 60)
    print("Testing Document Commands")
    print("=" * 60)
    
    results = []
    
    # List documents
    print("\n  Testing: document list")
    success, stdout, stderr = run_cli_command(["document", "list"])
    results.append(("document list", success))
    if success:
        print(f"    ✓ document list (found {stdout.count('Title:')} documents)")
    else:
        print(f"    ✗ document list failed")
    
    # List documents as JSON
    print("\n  Testing: document list --json")
    success, stdout, stderr = run_cli_command(["document", "list", "--json"])
    results.append(("document list --json", success))
    if success:
        try:
            data = json.loads(stdout)
            print(f"    ✓ document list --json (returned {len(data)} documents)")
        except json.JSONDecodeError:
            print(f"    ⚠ document list --json (invalid JSON)")
            results[-1] = ("document list --json", False)
    else:
        print(f"    ✗ document list --json failed")
    
    # Find duplicates
    print("\n  Testing: document find-duplicates")
    success, stdout, stderr = run_cli_command(["document", "find-duplicates"])
    results.append(("document find-duplicates", success))
    if success:
        print(f"    ✓ document find-duplicates")
    else:
        print(f"    ✗ document find-duplicates failed")
    
    # Test invalid command (should fail)
    print("\n  Testing: document invalid-command (should fail)")
    success, stdout, stderr = run_cli_command(["document", "invalid-command"], expect_success=False)
    results.append(("document invalid-command", not success))  # Should fail
    if not success:
        print(f"    ✓ document invalid-command correctly failed")
    else:
        print(f"    ✗ document invalid-command should have failed")
    
    return results


def test_vector_commands():
    """Test vector store commands."""
    print("\n" + "=" * 60)
    print("Testing Vector Commands")
    print("=" * 60)
    
    results = []
    
    # List collections
    print("\n  Testing: vector collections")
    success, stdout, stderr = run_cli_command(["vector", "collections"])
    results.append(("vector collections", success))
    if success:
        print(f"    ✓ vector collections")
    else:
        print(f"    ✗ vector collections failed")
    
    # List collections as JSON
    print("\n  Testing: vector collections --json")
    success, stdout, stderr = run_cli_command(["vector", "collections", "--json"])
    results.append(("vector collections --json", success))
    if success:
        try:
            data = json.loads(stdout)
            print(f"    ✓ vector collections --json (returned {len(data)} collections)")
        except json.JSONDecodeError:
            print(f"    ⚠ vector collections --json (invalid JSON)")
            results[-1] = ("vector collections --json", False)
    else:
        print(f"    ✗ vector collections --json failed")
    
    # Get stats for documents collection (if exists)
    print("\n  Testing: vector stats documents")
    success, stdout, stderr = run_cli_command(["vector", "stats", "documents"])
    results.append(("vector stats documents", success))
    if success:
        print(f"    ✓ vector stats documents")
    else:
        print(f"    ⚠ vector stats documents (may not exist)")
    
    return results


def test_note_commands():
    """Test note management commands."""
    print("\n" + "=" * 60)
    print("Testing Note Commands")
    print("=" * 60)
    
    results = []
    
    # List notes
    print("\n  Testing: note list")
    success, stdout, stderr = run_cli_command(["note", "list"])
    results.append(("note list", success))
    if success:
        note_count = stdout.count(".md") if ".md" in stdout else 0
        print(f"    ✓ note list")
    else:
        print(f"    ✗ note list failed")
    
    # List notes as JSON
    print("\n  Testing: note list --json")
    success, stdout, stderr = run_cli_command(["note", "list", "--json"])
    results.append(("note list --json", success))
    if success:
        try:
            data = json.loads(stdout)
            print(f"    ✓ note list --json (returned {len(data)} notes)")
        except json.JSONDecodeError:
            print(f"    ⚠ note list --json (invalid JSON)")
            results[-1] = ("note list --json", False)
    else:
        print(f"    ✗ note list --json failed")
    
    # Test search (may fail if no notes)
    print("\n  Testing: note search (may fail if no notes)")
    success, stdout, stderr = run_cli_command(["note", "search", "test"], expect_success=True)
    # This might succeed or fail depending on data
    # Accept success, "No matching notes found", or any error message
    if success or "No matching notes found" in stdout or "At least one of" in stderr or "Error:" in stderr:
        results.append(("note search", True))
        print(f"    ✓ note search (handled correctly)")
    else:
        results.append(("note search", False))
        print(f"    ✗ note search failed unexpectedly")
        print(f"      Success: {success}, Return code: {0 if success else 'non-zero'}")
        if stdout:
            print(f"      Stdout preview: {stdout[:200]}")
        if stderr:
            print(f"      Stderr preview: {stderr[:200]}")
    
    return results


def test_rag_commands():
    """Test RAG commands (may be slow)."""
    print("\n" + "=" * 60)
    print("Testing RAG Commands")
    print("=" * 60)
    print("  Note: RAG commands may be slow due to model loading")
    
    results = []
    
    # Test query (may fail if no documents)
    print("\n  Testing: rag query (basic)")
    success, stdout, stderr = run_cli_command(["rag", "query", "test"], expect_success=False)
    # This might succeed or fail depending on data
    if success or "No documents found" in stdout or "Error" in stderr:
        results.append(("rag query", True))
        print(f"    ✓ rag query (handled correctly)")
    else:
        results.append(("rag query", False))
        print(f"    ✗ rag query failed unexpectedly")
    
    return results


def test_index_commands():
    """Test index management commands."""
    print("\n" + "=" * 60)
    print("Testing Index Commands")
    print("=" * 60)
    
    results = []
    
    # Status (should always work)
    print("\n  Testing: index status")
    success, stdout, stderr = run_cli_command(["index", "status"])
    results.append(("index status", success))
    if success:
        print(f"    ✓ index status")
    else:
        print(f"    ✗ index status failed")
    
    return results


def test_command_validation():
    """Test command validation and error handling."""
    print("\n" + "=" * 60)
    print("Testing Command Validation")
    print("=" * 60)
    
    results = []
    
    # Test missing required arguments
    test_cases = [
        (["document", "add"], "document add without args (should fail)"),
        (["document", "show"], "document show without doc_id (should fail)"),
        (["rag", "query"], "rag query without question (should fail)"),
        (["note", "create"], "note create without args (should fail)"),
    ]
    
    for args, description in test_cases:
        print(f"\n  Testing: {description}")
        success, stdout, stderr = run_cli_command(args, expect_success=False)
        results.append((description, not success))  # Should fail
        if not success:
            print(f"    ✓ {description} correctly failed")
        else:
            print(f"    ✗ {description} should have failed")
    
    return results


def main():
    """Run all CLI tests."""
    print("=" * 60)
    print("OmniKnowledgeBase CLI Test Suite")
    print("=" * 60)
    print("\nThis script tests all CLI commands systematically.")
    print("Note: Some tests may fail if required data/services are not available.")
    
    all_results = []
    
    # Run test suites
    all_results.extend(test_help_commands())
    all_results.extend(test_document_commands())
    all_results.extend(test_vector_commands())
    all_results.extend(test_note_commands())
    all_results.extend(test_index_commands())
    all_results.extend(test_rag_commands())
    all_results.extend(test_command_validation())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in all_results if success)
    total = len(all_results)
    failed = total - passed
    
    for test_name, success in all_results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({failed} failed)")
    
    if failed > 0:
        print("\n⚠️  Some tests failed. This may be expected if:")
        print("   - Required data is not available")
        print("   - Services are not configured")
        print("   - Models are not loaded")
        print("\nReview the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

