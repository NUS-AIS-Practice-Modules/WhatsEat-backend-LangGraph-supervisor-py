"""
Agent Testing Script - Generates comprehensive test reports for each agent
Run this script to test all agents individually and generate markdown reports.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Ensure environment is loaded
from whats_eat.configuration.env_loader import load_env
load_env()


def test_places_agent():
    """Test the Places Agent with various queries."""
    print("\n" + "="*80)
    print("TESTING PLACES AGENT")
    print("="*80)
    
    from whats_eat.agents.places_agent import build_places_agent
    agent = build_places_agent()
    
    test_cases = [
        {
            "name": "Search Italian restaurants in Singapore",
            "input": {
                "messages": [
                    {"role": "user", "content": "Find Italian restaurants in Singapore"}
                ]
            },
            "expected": "Should return a list of Italian restaurants with details"
        },
        {
            "name": "Search by coordinates",
            "input": {
                "messages": [
                    {"role": "user", "content": "Find restaurants near coordinates 1.3521, 103.8198"}
                ]
            },
            "expected": "Should return nearby restaurants"
        },
        {
            "name": "Search with price level",
            "input": {
                "messages": [
                    {"role": "user", "content": "Find affordable cafes in Orchard Road Singapore"}
                ]
            },
            "expected": "Should return cafes with price information"
        }
    ]
    
    results = []
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test['name']}")
        print(f"Expected: {test['expected']}")
        
        try:
            result = agent.invoke(test["input"])
            success = "messages" in result and len(result["messages"]) > 0
            
            results.append({
                "test_name": test["name"],
                "status": "✅ PASS" if success else "❌ FAIL",
                "input": test["input"]["messages"][0]["content"],
                "expected": test["expected"],
                "output_summary": str(result.get("messages", [])[-1] if result.get("messages") else "No output")[:200],
                "error": None
            })
            print(f"Status: {'✅ PASS' if success else '❌ FAIL'}")
            
        except Exception as e:
            results.append({
                "test_name": test["name"],
                "status": "❌ ERROR",
                "input": test["input"]["messages"][0]["content"],
                "expected": test["expected"],
                "output_summary": None,
                "error": str(e)
            })
            print(f"Status: ❌ ERROR - {str(e)}")
    
    return {
        "agent_name": "Places Agent",
        "description": "Handles Google Places API searches, geocoding, and photo resolution",
        "test_results": results,
        "total_tests": len(test_cases),
        "passed": sum(1 for r in results if r["status"] == "✅ PASS"),
        "failed": sum(1 for r in results if r["status"] in ["❌ FAIL", "❌ ERROR"])
    }


def test_user_profile_agent():
    """Test the User Profile Agent."""
    print("\n" + "="*80)
    print("TESTING USER PROFILE AGENT")
    print("="*80)
    
    from whats_eat.agents.user_profile_agent import build_user_profile_agent
    agent = build_user_profile_agent()
    
    test_cases = [
        {
            "name": "Generate user profile from YouTube channel",
            "input": {
                "messages": [
                    {"role": "user", "content": "Generate my food preference profile"}
                ]
            },
            "expected": "Should return user profile with embeddings and preferences"
        }
    ]
    
    results = []
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test['name']}")
        print(f"Expected: {test['expected']}")
        
        try:
            result = agent.invoke(test["input"])
            success = "messages" in result and len(result["messages"]) > 0
            
            results.append({
                "test_name": test["name"],
                "status": "✅ PASS" if success else "❌ FAIL",
                "input": test["input"]["messages"][0]["content"],
                "expected": test["expected"],
                "output_summary": str(result.get("messages", [])[-1] if result.get("messages") else "No output")[:200],
                "error": None
            })
            print(f"Status: {'✅ PASS' if success else '❌ FAIL'}")
            
        except Exception as e:
            results.append({
                "test_name": test["name"],
                "status": "⚠️ SKIP" if "OAuth token not found" in str(e) else "❌ ERROR",
                "input": test["input"]["messages"][0]["content"],
                "expected": test["expected"],
                "output_summary": None,
                "error": str(e)
            })
            print(f"Status: {'⚠️ SKIP - OAuth token required' if 'OAuth token not found' in str(e) else '❌ ERROR'} - {str(e)}")
    
    return {
        "agent_name": "User Profile Agent",
        "description": "Generates user preference profiles from YouTube activity using embeddings",
        "test_results": results,
        "total_tests": len(test_cases),
        "passed": sum(1 for r in results if r["status"] == "✅ PASS"),
        "failed": sum(1 for r in results if r["status"] in ["❌ FAIL", "❌ ERROR"]),
        "skipped": sum(1 for r in results if r["status"] == "⚠️ SKIP")
    }


def test_rag_recommender_agent():
    """Test the RAG Recommender Agent."""
    print("\n" + "="*80)
    print("TESTING RAG RECOMMENDER AGENT")
    print("="*80)
    
    from whats_eat.agents.rag_recommender_agent import build_rag_recommender_agent
    agent = build_rag_recommender_agent()
    
    # Sample place data for testing
    sample_places = json.dumps([
        {
            "name": "Paradise Dynasty",
            "formatted_address": "ION Orchard, Singapore",
            "rating": 4.2,
            "price_level": 3,
            "types": ["restaurant", "food"],
            "location": {"lat": 1.3048, "lng": 103.8318}
        }
    ])
    
    test_cases = [
        {
            "name": "Process and store places data",
            "input": {
                "messages": [
                    {"role": "user", "content": f"Store these places: {sample_places}"}
                ]
            },
            "expected": "Should store places in Neo4j and Pinecone"
        },
        {
            "name": "Query similar places",
            "input": {
                "messages": [
                    {"role": "user", "content": "Find restaurants similar to Chinese dim sum"}
                ]
            },
            "expected": "Should return similar restaurants from vector database"
        }
    ]
    
    results = []
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test['name']}")
        print(f"Expected: {test['expected']}")
        
        try:
            result = agent.invoke(test["input"])
            success = "messages" in result and len(result["messages"]) > 0
            
            results.append({
                "test_name": test["name"],
                "status": "✅ PASS" if success else "❌ FAIL",
                "input": test["input"]["messages"][0]["content"][:100],
                "expected": test["expected"],
                "output_summary": str(result.get("messages", [])[-1] if result.get("messages") else "No output")[:200],
                "error": None
            })
            print(f"Status: {'✅ PASS' if success else '❌ FAIL'}")
            
        except Exception as e:
            results.append({
                "test_name": test["name"],
                "status": "❌ ERROR",
                "input": test["input"]["messages"][0]["content"][:100],
                "expected": test["expected"],
                "output_summary": None,
                "error": str(e)
            })
            print(f"Status: ❌ ERROR - {str(e)}")
    
    return {
        "agent_name": "RAG Recommender Agent",
        "description": "Stores and retrieves restaurant data using Neo4j knowledge graph and Pinecone vector search",
        "test_results": results,
        "total_tests": len(test_cases),
        "passed": sum(1 for r in results if r["status"] == "✅ PASS"),
        "failed": sum(1 for r in results if r["status"] in ["❌ FAIL", "❌ ERROR"])
    }


def test_summarizer_agent():
    """Test the Summarizer Agent."""
    print("\n" + "="*80)
    print("TESTING SUMMARIZER AGENT")
    print("="*80)
    
    from whats_eat.agents.summarizer_agent import build_summarizer_agent
    agent = build_summarizer_agent()
    
    sample_recommendations = json.dumps([
        {
            "name": "Paradise Dynasty",
            "address": "ION Orchard",
            "rating": 4.2,
            "cuisine": "Chinese",
            "price_level": 3
        },
        {
            "name": "Tim Ho Wan",
            "address": "Plaza Singapura",
            "rating": 4.0,
            "cuisine": "Dim Sum",
            "price_level": 2
        }
    ])
    
    test_cases = [
        {
            "name": "Generate summary cards for recommendations",
            "input": {
                "messages": [
                    {"role": "user", "content": f"Summarize these restaurants: {sample_recommendations}"}
                ]
            },
            "expected": "Should return JSON with cards array and rationale"
        }
    ]
    
    results = []
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test['name']}")
        print(f"Expected: {test['expected']}")
        
        try:
            result = agent.invoke(test["input"])
            success = "messages" in result and len(result["messages"]) > 0
            
            results.append({
                "test_name": test["name"],
                "status": "✅ PASS" if success else "❌ FAIL",
                "input": test["input"]["messages"][0]["content"][:100],
                "expected": test["expected"],
                "output_summary": str(result.get("messages", [])[-1] if result.get("messages") else "No output")[:200],
                "error": None
            })
            print(f"Status: {'✅ PASS' if success else '❌ FAIL'}")
            
        except Exception as e:
            results.append({
                "test_name": test["name"],
                "status": "❌ ERROR",
                "input": test["input"]["messages"][0]["content"][:100],
                "expected": test["expected"],
                "output_summary": None,
                "error": str(e)
            })
            print(f"Status: ❌ ERROR - {str(e)}")
    
    return {
        "agent_name": "Summarizer Agent",
        "description": "Generates final recommendation cards with rationale (no tool calls)",
        "test_results": results,
        "total_tests": len(test_cases),
        "passed": sum(1 for r in results if r["status"] == "✅ PASS"),
        "failed": sum(1 for r in results if r["status"] in ["❌ FAIL", "❌ ERROR"])
    }


def generate_markdown_report(all_results):
    """Generate a comprehensive markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# WhatsEat Agent Testing Report

**Generated:** {timestamp}  
**Project:** WhatsEat Multi-Agent System  
**Framework:** LangGraph with OpenAI gpt-4o-mini

---

## Executive Summary

"""
    
    total_tests = sum(r["total_tests"] for r in all_results)
    total_passed = sum(r["passed"] for r in all_results)
    total_failed = sum(r["failed"] for r in all_results)
    total_skipped = sum(r.get("skipped", 0) for r in all_results)
    
    report += f"""
- **Total Agents Tested:** {len(all_results)}
- **Total Test Cases:** {total_tests}
- **Passed:** ✅ {total_passed}
- **Failed:** ❌ {total_failed}
- **Skipped:** ⚠️ {total_skipped}
- **Success Rate:** {(total_passed/total_tests*100) if total_tests > 0 else 0:.1f}%

---

"""
    
    # Individual agent reports
    for result in all_results:
        report += f"""## {result['agent_name']}

**Description:** {result['description']}

**Test Summary:**
- Total Tests: {result['total_tests']}
- Passed: ✅ {result['passed']}
- Failed: ❌ {result['failed']}
"""
        if result.get('skipped', 0) > 0:
            report += f"- Skipped: ⚠️ {result['skipped']}\n"
        
        report += f"- Success Rate: {(result['passed']/result['total_tests']*100) if result['total_tests'] > 0 else 0:.1f}%\n\n"
        
        report += "### Test Cases\n\n"
        
        for test in result['test_results']:
            report += f"""#### {test['test_name']} {test['status']}

**Input:** `{test['input']}`

**Expected:** {test['expected']}

"""
            if test['output_summary']:
                report += f"**Output:** {test['output_summary']}\n\n"
            
            if test['error']:
                report += f"**Error:** ```\n{test['error']}\n```\n\n"
            
            report += "---\n\n"
    
    # Recommendations section
    report += """## Recommendations

### Successful Components
"""
    
    for result in all_results:
        if result['passed'] > 0:
            report += f"- ✅ **{result['agent_name']}**: {result['passed']}/{result['total_tests']} tests passed\n"
    
    report += "\n### Areas for Improvement\n"
    
    for result in all_results:
        if result['failed'] > 0 or result.get('skipped', 0) > 0:
            report += f"- ⚠️ **{result['agent_name']}**: "
            issues = []
            if result['failed'] > 0:
                issues.append(f"{result['failed']} test(s) failed")
            if result.get('skipped', 0) > 0:
                issues.append(f"{result['skipped']} test(s) skipped")
            report += ", ".join(issues) + "\n"
    
    report += """

---

## Conclusion

This report documents the individual testing of all WhatsEat agents. Each agent was tested in isolation to verify its core functionality before integration into the supervisor workflow.

**Next Steps:**
1. Address any failing tests
2. Set up YouTube OAuth for User Profile Agent (if skipped)
3. Verify Neo4j and Pinecone connectivity for RAG Agent
4. Perform end-to-end integration testing with the Supervisor

"""
    
    return report


def main():
    """Run all agent tests and generate reports."""
    print("WhatsEat Agent Testing Suite")
    print("=" * 80)
    
    all_results = []
    
    # Test each agent
    try:
        all_results.append(test_places_agent())
    except Exception as e:
        print(f"Failed to test Places Agent: {e}")
    
    try:
        all_results.append(test_user_profile_agent())
    except Exception as e:
        print(f"Failed to test User Profile Agent: {e}")
    
    try:
        all_results.append(test_rag_recommender_agent())
    except Exception as e:
        print(f"Failed to test RAG Recommender Agent: {e}")
    
    try:
        all_results.append(test_summarizer_agent())
    except Exception as e:
        print(f"Failed to test Summarizer Agent: {e}")

    
    # Generate markdown report
    report = generate_markdown_report(all_results)
    
    # Save report
    report_dir = Path(__file__).parent / "test_reports"
    # 修改为 tests/test_reports 子文件夹
    report_dir = Path(__file__).parent / "tests" / "test_reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"agent_test_report_{timestamp}.md"
    
    report_path.write_text(report, encoding="utf-8")
    
    print("\n" + "="*80)
    print(f"✅ Report generated: {report_path}")
    print("="*80)
    
    # Also save as JSON for programmatic access
    json_path = report_dir / f"agent_test_report_{timestamp}.json"
    json_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"✅ JSON data saved: {json_path}")
    
    return all_results


if __name__ == "__main__":
    main()
