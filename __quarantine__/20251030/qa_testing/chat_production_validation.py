#!/usr/bin/env python3
"""
Production-Readiness Validation for Multi-Turn Chat
Comprehensive testing of latency, memory, citations, and load handling
"""

import requests
import time
import json
import statistics
import threading
import concurrent.futures
from datetime import datetime

# Test Configuration
BASE_URL = "http://localhost:8001"
TIMEOUT = 30

class ChatValidator:
    def __init__(self):
        self.results = {
            "validation_timestamp": datetime.now().isoformat(),
            "latency": {"single_turn": [], "multi_turn": []},
            "citations": {"valid": 0, "invalid": 0, "snippet_violations": 0},
            "errors": [],
            "test_results": {},
            "example_transcripts": []
        }
    
    def make_chat_request(self, session_id: str, message: str) -> dict:
        """Make chat request and measure timing"""
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat",
                json={"session_id": session_id, "message": message},
                timeout=TIMEOUT
            )
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                data["_test_latency_ms"] = latency_ms
                return data
            else:
                self.results["errors"].append({
                    "type": "http_error",
                    "status": response.status_code,
                    "message": response.text[:200]
                })
                return {"error": True, "_test_latency_ms": latency_ms}
                
        except Exception as e:
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            self.results["errors"].append({
                "type": "request_error",
                "message": str(e)
            })
            return {"error": True, "_test_latency_ms": latency_ms}
    
    def validate_citations(self, citations: list) -> dict:
        """Validate citation integrity"""
        validation = {"valid": 0, "issues": []}
        
        for cite in citations:
            is_valid = True
            
            # Check required fields
            if not cite.get("source") or not isinstance(cite.get("page"), int):
                validation["issues"].append("Missing source or invalid page")
                is_valid = False
            
            # Check snippet length
            snippet = cite.get("snippet", "")
            if len(snippet) > 200:
                validation["issues"].append(f"Snippet too long: {len(snippet)} chars")
                self.results["citations"]["snippet_violations"] += 1
                is_valid = False
            
            # Check score validity
            score = cite.get("score", 0)
            if not isinstance(score, (int, float)) or score < 0 or score > 1:
                validation["issues"].append(f"Invalid score: {score}")
                is_valid = False
            
            if is_valid:
                validation["valid"] += 1
                self.results["citations"]["valid"] += 1
            else:
                self.results["citations"]["invalid"] += 1
        
        return validation
    
    def test_single_turn_queries(self):
        """Test 10 sample queries with single turns"""
        print("🧪 Testing single-turn queries...")
        
        queries = [
            "What are apron flashing cover requirements?",
            "Building code requirements for metal roofing",
            "Fire safety clearances for solid fuel appliances",
            "Weatherproofing standards for external walls",
            "Fastener requirements for steel cladding",
            "Minimum insulation R-values for Auckland",
            "Wind load requirements for roof structures", 
            "Corrosion resistance for coastal areas",
            "Ventilation requirements for roof cavities",
            "Installation standards for membrane roofing"
        ]
        
        single_turn_results = []
        
        for i, query in enumerate(queries, 1):
            session_id = f"single_test_{i}"
            response = self.make_chat_request(session_id, query)
            
            if not response.get("error"):
                latency = response.get("_test_latency_ms", 0)
                self.results["latency"]["single_turn"].append(latency)
                
                citations = response.get("citations", [])
                citation_validation = self.validate_citations(citations)
                
                single_turn_results.append({
                    "query": query,
                    "latency_ms": latency,
                    "citations_count": len(citations),
                    "citations_valid": citation_validation["valid"],
                    "response_length": len(response.get("message", ""))
                })
                
                print(f"  {i:2d}. {latency:4.0f}ms | {len(citations)} citations | {query[:40]}...")
            else:
                print(f"  {i:2d}. ERROR | {query[:40]}...")
        
        self.results["test_results"]["single_turn"] = single_turn_results
    
    def test_multi_turn_conversation(self):
        """Test multi-turn conversation with memory"""
        print("\n🧪 Testing multi-turn conversations...")
        
        # 3 conversation flows
        conversations = [
            {
                "session": "multi_test_1",
                "turns": [
                    "What are the apron flashing requirements?",
                    "What about in high wind zones?", 
                    "Are there specific fastener requirements?"
                ]
            },
            {
                "session": "multi_test_2", 
                "turns": [
                    "Tell me about metal roofing installation",
                    "What are the corrosion resistance requirements?",
                    "How does this apply to coastal environments?"
                ]
            },
            {
                "session": "multi_test_3",
                "turns": [
                    "Building code requirements for fire safety",
                    "What clearances are needed for fireplaces?",
                    "Any specific requirements for timber floors?"
                ]
            }
        ]
        
        multi_turn_results = []
        
        for conv in conversations:
            session_id = conv["session"]
            conversation_transcript = {"session_id": session_id, "turns": []}
            
            for turn_num, message in enumerate(conv["turns"], 1):
                response = self.make_chat_request(session_id, message)
                
                if not response.get("error"):
                    latency = response.get("_test_latency_ms", 0)
                    self.results["latency"]["multi_turn"].append(latency)
                    
                    citations = response.get("citations", [])
                    self.validate_citations(citations)
                    
                    turn_result = {
                        "turn": turn_num,
                        "user_message": message,
                        "assistant_response": response.get("message", ""),
                        "citations": citations,
                        "latency_ms": latency
                    }
                    
                    conversation_transcript["turns"].append(turn_result)
                    
                    print(f"    {session_id} Turn {turn_num}: {latency:4.0f}ms | {len(citations)} citations")
                else:
                    print(f"    {session_id} Turn {turn_num}: ERROR")
            
            multi_turn_results.append(conversation_transcript)
            # Store first 3 as examples
            if len(self.results["example_transcripts"]) < 3:
                self.results["example_transcripts"].append(conversation_transcript)
        
        self.results["test_results"]["multi_turn"] = multi_turn_results
    
    def test_concurrent_load(self):
        """Test concurrent sessions for load testing"""
        print("\n🧪 Testing concurrent load (20 sessions × 3 turns)...")
        
        def run_concurrent_session(session_num):
            """Run one concurrent session"""
            session_id = f"load_test_{session_num}"
            session_errors = 0
            session_latencies = []
            
            messages = [
                "What are building requirements?",
                "Tell me about metal roofing",
                "Any specific standards?"
            ]
            
            for turn, message in enumerate(messages, 1):
                response = self.make_chat_request(session_id, message)
                
                if response.get("error"):
                    session_errors += 1
                else:
                    session_latencies.append(response.get("_test_latency_ms", 0))
            
            return session_errors, session_latencies
        
        # Run concurrent sessions
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_concurrent_session, i) for i in range(1, 21)]
            
            total_errors = 0
            all_latencies = []
            
            for future in concurrent.futures.as_completed(futures):
                session_errors, session_latencies = future.result()
                total_errors += session_errors
                all_latencies.extend(session_latencies)
        
        self.results["test_results"]["concurrent_load"] = {
            "total_requests": 60,  # 20 sessions × 3 turns
            "total_errors": total_errors,
            "error_rate_pct": (total_errors / 60) * 100,
            "latencies_ms": all_latencies
        }
        
        print(f"    Concurrent load: {total_errors} errors / 60 requests ({(total_errors/60)*100:.1f}% error rate)")
    
    def test_negative_cases(self):
        """Test edge cases and error handling"""
        print("\n🧪 Testing negative cases...")
        
        negative_tests = [
            ("empty_retrieval", "What is the quantum flux capacitor rating?"),  # Out of scope
            ("very_short", "hi"),  # Minimal input
            ("very_long", "What are the " + "detailed " * 50 + "requirements?")  # Long input
        ]
        
        negative_results = []
        
        for test_name, message in negative_tests:
            session_id = f"negative_{test_name}"
            response = self.make_chat_request(session_id, message)
            
            if not response.get("error"):
                citations = response.get("citations", [])
                has_uncertainty_language = any(word in response.get("message", "").lower() 
                                              for word in ["don't have", "unsure", "uncertain", "not specific"])
                
                negative_results.append({
                    "test": test_name,
                    "message": message[:50] + "..." if len(message) > 50 else message,
                    "citations_count": len(citations),
                    "has_uncertainty": has_uncertainty_language,
                    "response_appropriate": len(citations) == 0 or has_uncertainty_language
                })
                
                print(f"    {test_name}: {len(citations)} citations, uncertainty: {has_uncertainty_language}")
            else:
                print(f"    {test_name}: ERROR")
        
        self.results["test_results"]["negative_cases"] = negative_results
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        all_latencies = (self.results["latency"]["single_turn"] + 
                        self.results["latency"]["multi_turn"] +
                        self.results["test_results"].get("concurrent_load", {}).get("latencies_ms", []))
        
        if all_latencies:
            self.results["metrics"] = {
                "p50_latency_ms": statistics.median(all_latencies),
                "p95_latency_ms": statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) > 20 else max(all_latencies),
                "avg_latency_ms": statistics.mean(all_latencies),
                "total_requests": len(all_latencies)
            }
        
        # Calculate citation metrics
        total_citations = self.results["citations"]["valid"] + self.results["citations"]["invalid"]
        if total_citations > 0:
            self.results["citation_metrics"] = {
                "total_citations": total_citations,
                "valid_citations": self.results["citations"]["valid"],
                "citation_success_rate": (self.results["citations"]["valid"] / total_citations) * 100,
                "avg_citations_per_turn": total_citations / len(all_latencies) if all_latencies else 0
            }
    
    def generate_reports(self):
        """Generate validation reports"""
        # JSON Report
        with open('/app/reports/chat_validation.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Markdown Report
        metrics = self.results.get("metrics", {})
        citation_metrics = self.results.get("citation_metrics", {})
        
        md_content = f"""# Multi-Turn Chat Validation Report

## 📊 Performance Metrics
- **P50 Latency**: {metrics.get('p50_latency_ms', 0):.0f}ms
- **P95 Latency**: {metrics.get('p95_latency_ms', 0):.0f}ms
- **Average Latency**: {metrics.get('avg_latency_ms', 0):.0f}ms
- **Total Requests**: {metrics.get('total_requests', 0)}

## 📋 Citation Quality
- **Total Citations**: {citation_metrics.get('total_citations', 0)}
- **Valid Citations**: {citation_metrics.get('valid_citations', 0)}
- **Success Rate**: {citation_metrics.get('citation_success_rate', 0):.1f}%
- **Snippet Violations**: {self.results['citations']['snippet_violations']}

## 🧪 Test Results
- **Single-turn tests**: {len(self.results['latency']['single_turn'])} completed
- **Multi-turn tests**: {len(self.results['example_transcripts'])} conversations
- **Load test error rate**: {self.results['test_results'].get('concurrent_load', {}).get('error_rate_pct', 0):.1f}%

## ✅ Acceptance Criteria Check
- P50 ≤ 2500ms: {'✅ PASS' if metrics.get('p50_latency_ms', 0) <= 2500 else '❌ FAIL'}
- P95 ≤ 4500ms: {'✅ PASS' if metrics.get('p95_latency_ms', 0) <= 4500 else '❌ FAIL'}
- Error rate < 1%: {'✅ PASS' if self.results['test_results'].get('concurrent_load', {}).get('error_rate_pct', 0) < 1.0 else '❌ FAIL'}
- Snippet violations = 0: {'✅ PASS' if self.results['citations']['snippet_violations'] == 0 else '❌ FAIL'}

## 📝 Example Transcripts
{self._format_transcripts()}
"""
        
        with open('/app/reports/chat_validation.md', 'w') as f:
            f.write(md_content)
        
        print("✅ Reports generated:")
        print("  • /app/reports/chat_validation.json")
        print("  • /app/reports/chat_validation.md")
    
    def _format_transcripts(self):
        """Format example transcripts for markdown"""
        transcript_text = ""
        
        for i, transcript in enumerate(self.results["example_transcripts"], 1):
            transcript_text += f"\n### Example {i}: {transcript['session_id']}\n"
            
            for turn in transcript["turns"]:
                transcript_text += f"\n**User**: {turn['user_message']}\n"
                transcript_text += f"**Assistant**: {turn['assistant_response'][:200]}...\n"
                
                if turn["citations"]:
                    transcript_text += "**Citations**:\n"
                    for cite in turn["citations"][:2]:  # Top 2
                        transcript_text += f"- {cite['source']} p.{cite['page']} (score: {cite['score']})\n"
                
                transcript_text += f"*Latency: {turn['latency_ms']:.0f}ms*\n\n"
        
        return transcript_text

def main():
    """Main validation pipeline"""
    print("🏗️ MULTI-TURN CHAT PRODUCTION VALIDATION")
    print("=" * 60)
    print("Target: Production-ready chat with memory & citations")
    
    validator = ChatValidator()
    
    try:
        # Health check first
        health_response = requests.get(f"{BASE_URL}/health", timeout=10)
        if health_response.status_code != 200:
            print("❌ Backend health check failed")
            return
        
        print("✅ Backend health check passed")
        
        # Run test suite
        validator.test_single_turn_queries()
        validator.test_multi_turn_conversation()
        validator.test_concurrent_load()
        validator.test_negative_cases()
        
        # Calculate metrics
        validator.calculate_metrics()
        
        # Print summary
        metrics = validator.results.get("metrics", {})
        citation_metrics = validator.results.get("citation_metrics", {})
        
        print(f"\n📊 VALIDATION SUMMARY")
        print("=" * 40)
        print(f"• P50 latency: {metrics.get('p50_latency_ms', 0):.0f}ms (target: ≤2500ms)")
        print(f"• P95 latency: {metrics.get('p95_latency_ms', 0):.0f}ms (target: ≤4500ms)")
        print(f"• Error rate: {validator.results['test_results'].get('concurrent_load', {}).get('error_rate_pct', 0):.1f}% (target: <1%)")
        print(f"• Citation success rate: {citation_metrics.get('citation_success_rate', 0):.1f}%")
        print(f"• Snippet violations: {validator.results['citations']['snippet_violations']} (target: 0)")
        print(f"• Total errors: {len(validator.results['errors'])}")
        
        # Acceptance check
        p50_pass = metrics.get('p50_latency_ms', 0) <= 2500
        p95_pass = metrics.get('p95_latency_ms', 0) <= 4500
        error_rate_pass = validator.results['test_results'].get('concurrent_load', {}).get('error_rate_pct', 0) < 1.0
        snippet_pass = validator.results['citations']['snippet_violations'] == 0
        
        all_passed = p50_pass and p95_pass and error_rate_pass and snippet_pass
        
        print(f"\n🎯 ACCEPTANCE CRITERIA:")
        print(f"• P50 latency: {'✅ PASS' if p50_pass else '❌ FAIL'}")
        print(f"• P95 latency: {'✅ PASS' if p95_pass else '❌ FAIL'}")
        print(f"• Error rate: {'✅ PASS' if error_rate_pass else '❌ FAIL'}")
        print(f"• Snippet quality: {'✅ PASS' if snippet_pass else '❌ FAIL'}")
        
        if all_passed:
            print(f"\n🎉 PRODUCTION VALIDATION PASSED!")
        else:
            print(f"\n⚠️ Some criteria need attention")
        
        # Generate reports
        validator.generate_reports()
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")

if __name__ == "__main__":
    main()