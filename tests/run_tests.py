#!/usr/bin/env python
"""
Integration tests for YanaChat V2.

Run with: python tests/run_tests.py
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm_pipeline import LLMPipeline
from src.chat_handler import ChatHandler


def test_llm_pipeline():
    """Test LLMPipeline initialization and basic generation."""
    print("Testing LLMPipeline...")
    
    try:
        pipeline = LLMPipeline()
        print(f"  ✓ LLMPipeline initialized with model: {pipeline.model}")
        
        # Note: This would make a real API call
        # result = pipeline.generate("Hello")
        # print(f"  ✓ Generate works")
        
    except ValueError as e:
        print(f"  ✗ LLMPipeline init failed: {e}")
        return False
    
    return True


def test_chat_handler():
    """Test ChatHandler initialization and logging."""
    print("Testing ChatHandler...")
    
    try:
        handler = ChatHandler()
        print(f"  ✓ ChatHandler initialized")
        
        # Check log file path exists
        assert handler.log_path.parent.exists()
        print(f"  ✓ Log directory created: {handler.log_path.parent}")
        
    except Exception as e:
        print(f"  ✗ ChatHandler test failed: {e}")
        return False
    
    return True


def test_logging_format():
    """Test that logs are written in correct JSONL format."""
    print("Testing JSONL logging format...")
    
    try:
        handler = ChatHandler()
        
        # Create test log entry
        test_query = "Test query"
        test_response = {"response": "Test response", "latency_ms": 100}
        test_session = "test_session"
        
        handler._log_interaction(test_query, test_response, test_session)
        
        # Read back the log
        with open(handler.log_path, "r") as f:
            last_line = f.readlines()[-1]
        
        # Parse as JSON
        log_entry = json.loads(last_line)
        
        # Verify required fields
        required_fields = ["timestamp", "session_id", "model", "query", "response", "latency_ms"]
        for field in required_fields:
            assert field in log_entry, f"Missing field: {field}"
        
        assert log_entry["session_id"] == test_session
        assert log_entry["query"] == test_query
        assert log_entry["model"] == "mistral-large-latest"
        
        print(f"  ✓ JSONL format is correct")
        print(f"    Fields: {', '.join(required_fields)}")
        
    except Exception as e:
        print(f"  ✗ JSONL logging test failed: {e}")
        return False
    
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*50)
    print("YanaChat V2 - Integration Tests")
    print("="*50 + "\n")
    
    tests = [
        test_llm_pipeline,
        test_chat_handler,
        test_logging_format,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            results.append(False)
        print()
    
    # Summary
    print("="*50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("="*50 + "\n")
    
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
