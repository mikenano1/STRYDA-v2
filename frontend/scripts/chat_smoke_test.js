#!/usr/bin/env node
/**
 * Chat Smoke Tests - End-to-End Validation
 * Tests real chat functionality with timing and citation validation
 */

const fetch = require('node-fetch');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const API_BASE = process.env.EXPO_PUBLIC_API_BASE || 'http://localhost:8001';
const OUTPUT_DIR = path.join(__dirname, '..', 'reports');

class ChatSmokeTest {
  constructor() {
    this.results = {
      test_timestamp: new Date().toISOString(),
      api_base: API_BASE,
      sessions_tested: 0,
      total_requests: 0,
      successful_requests: 0,
      failed_requests: 0,
      latencies_ms: [],
      citations_per_response: [],
      error_details: [],
      session_results: []
    };
  }

  async makeRequest(sessionId, message) {
    const startTime = Date.now();
    
    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: message
        }),
        timeout: 30000
      });

      const endTime = Date.now();
      const latency = endTime - startTime;
      
      this.results.total_requests++;

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Validate response structure
      this.validateResponse(data, sessionId, message);
      
      this.results.successful_requests++;
      this.results.latencies_ms.push(latency);
      
      const citationCount = (data.citations || []).length;
      this.results.citations_per_response.push(citationCount);

      return {
        success: true,
        latency,
        data,
        citationCount
      };

    } catch (error) {
      const endTime = Date.now();
      const latency = endTime - startTime;
      
      this.results.failed_requests++;
      this.results.error_details.push({
        session_id: sessionId,
        message: message.substring(0, 50) + '...',
        error: error.message,
        latency
      });

      return {
        success: false,
        latency,
        error: error.message
      };
    }
  }

  validateResponse(data, sessionId, message) {
    // Check required fields
    if (!data.message) {
      throw new Error('Response missing message field');
    }
    
    if (!Array.isArray(data.citations)) {
      throw new Error('Citations field missing or not array');
    }
    
    if (data.session_id !== sessionId) {
      throw new Error(`Session ID mismatch: expected ${sessionId}, got ${data.session_id}`);
    }

    // Validate citations
    for (let i = 0; i < data.citations.length; i++) {
      const citation = data.citations[i];
      
      if (!citation.source || typeof citation.page !== 'number') {
        throw new Error(`Citation ${i} missing source or page`);
      }
      
      if (citation.snippet && citation.snippet.length > 200) {
        throw new Error(`Citation ${i} snippet too long: ${citation.snippet.length} chars`);
      }
      
      if (typeof citation.score !== 'number' || citation.score < 0 || citation.score > 1) {
        throw new Error(`Citation ${i} invalid score: ${citation.score}`);
      }
    }
  }

  async runSessionTest(sessionNumber) {
    const sessionId = `smoke_test_${sessionNumber}_${Date.now()}`;
    
    const messages = [
      "What are the apron flashing cover requirements?",
      "What about very high wind zones?",
      "Are there specific fastener requirements?"
    ];

    console.log(`\n🧪 Session ${sessionNumber}: ${sessionId}`);
    
    const sessionResult = {
      session_id: sessionId,
      session_number: sessionNumber,
      turns: []
    };

    for (let turnNum = 1; turnNum <= messages.length; turnNum++) {
      const message = messages[turnNum - 1];
      
      console.log(`  Turn ${turnNum}: "${message.substring(0, 40)}..."`);
      
      const result = await this.makeRequest(sessionId, message);
      
      const turnResult = {
        turn: turnNum,
        message: message.substring(0, 50) + '...',
        success: result.success,
        latency_ms: result.latency,
        citation_count: result.citationCount || 0,
        error: result.error || null
      };

      sessionResult.turns.push(turnResult);
      
      if (result.success) {
        console.log(`    ✅ ${result.latency}ms | ${result.citationCount} citations`);
      } else {
        console.log(`    ❌ ${result.latency}ms | ${result.error}`);
      }
      
      // Small delay between turns
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    this.results.session_results.push(sessionResult);
    this.results.sessions_tested++;
  }

  calculateMetrics() {
    const latencies = this.results.latencies_ms;
    
    if (latencies.length === 0) {
      return {};
    }

    // Calculate percentiles
    const sortedLatencies = [...latencies].sort((a, b) => a - b);
    const p50Index = Math.floor(sortedLatencies.length * 0.5);
    const p95Index = Math.floor(sortedLatencies.length * 0.95);

    return {
      total_requests: this.results.total_requests,
      successful_requests: this.results.successful_requests,
      error_rate_pct: (this.results.failed_requests / this.results.total_requests) * 100,
      p50_latency_ms: sortedLatencies[p50Index],
      p95_latency_ms: sortedLatencies[p95Index],
      avg_latency_ms: Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length),
      avg_citations_per_response: this.results.citations_per_response.length > 0 
        ? Math.round(this.results.citations_per_response.reduce((a, b) => a + b, 0) / this.results.citations_per_response.length * 10) / 10
        : 0
    };
  }

  async generateReports() {
    try {
      await fs.mkdir(OUTPUT_DIR, { recursive: true });
    } catch (error) {
      // Directory might already exist
    }

    const metrics = this.calculateMetrics();
    
    // JSON Report
    const jsonReport = {
      ...this.results,
      metrics
    };

    await fs.writeFile(
      path.join(OUTPUT_DIR, 'chat_smoke_summary.json'),
      JSON.stringify(jsonReport, null, 2)
    );

    // Markdown Report
    const mdContent = `# Chat Smoke Test Results

## 📊 Performance Metrics
- **P50 Latency**: ${metrics.p50_latency_ms || 0}ms
- **P95 Latency**: ${metrics.p95_latency_ms || 0}ms  
- **Average Latency**: ${metrics.avg_latency_ms || 0}ms
- **Error Rate**: ${metrics.error_rate_pct || 0}%

## 📋 Test Coverage
- **Sessions Tested**: ${this.results.sessions_tested}
- **Total Requests**: ${this.results.total_requests}
- **Successful**: ${this.results.successful_requests}
- **Failed**: ${this.results.failed_requests}
- **Average Citations**: ${metrics.avg_citations_per_response || 0} per response

## 🎯 Acceptance Criteria
- P50 ≤ 2800ms: ${metrics.p50_latency_ms <= 2800 ? '✅ PASS' : '❌ FAIL'}
- P95 ≤ 4500ms: ${metrics.p95_latency_ms <= 4500 ? '✅ PASS' : '❌ FAIL'}
- Error rate < 1%: ${metrics.error_rate_pct < 1.0 ? '✅ PASS' : '❌ FAIL'}

## 📝 Sample Sessions
${this.results.session_results.slice(0, 2).map((session, i) => `
### Session ${i + 1}: ${session.session_id}
${session.turns.map(turn => `
**Turn ${turn.turn}**: ${turn.message}
- Status: ${turn.success ? '✅ Success' : '❌ Failed'}
- Latency: ${turn.latency_ms}ms
- Citations: ${turn.citation_count}
${turn.error ? `- Error: ${turn.error}` : ''}
`).join('')}
`).join('')}

${this.results.error_details.length > 0 ? `
## ❌ Error Details
${this.results.error_details.map(error => `
- **Session**: ${error.session_id}
- **Message**: ${error.message}
- **Error**: ${error.error}
- **Latency**: ${error.latency}ms
`).join('')}
` : ''}
`;

    await fs.writeFile(
      path.join(OUTPUT_DIR, 'chat_smoke_summary.md'),
      mdContent
    );

    console.log('\n📋 Reports generated:');
    console.log(`  • ${path.join(OUTPUT_DIR, 'chat_smoke_summary.json')}`);
    console.log(`  • ${path.join(OUTPUT_DIR, 'chat_smoke_summary.md')}`);
  }

  async runSmokeTests() {
    console.log('🏗️ STRYDA CHAT SMOKE TESTS');
    console.log('=' .repeat(60));
    console.log(`API Base: ${API_BASE}`);
    console.log('Target: 3 sessions × 3 turns each = 9 requests');

    // Health check first
    try {
      const healthResponse = await fetch(`${API_BASE}/health`, { timeout: 10000 });
      if (!healthResponse.ok) {
        throw new Error(`Health check failed: ${healthResponse.status}`);
      }
      console.log('✅ Backend health check passed');
    } catch (error) {
      console.error('❌ Backend health check failed:', error.message);
      return;
    }

    // Run 3 test sessions
    for (let sessionNum = 1; sessionNum <= 3; sessionNum++) {
      await this.runSessionTest(sessionNum);
    }

    // Calculate and display metrics
    const metrics = this.calculateMetrics();
    
    console.log('\n📊 SMOKE TEST SUMMARY');
    console.log('=' .repeat(40));
    console.log(`• Sessions tested: ${this.results.sessions_tested}`);
    console.log(`• Total requests: ${this.results.total_requests}`);
    console.log(`• Success rate: ${this.results.successful_requests}/${this.results.total_requests} (${((this.results.successful_requests/this.results.total_requests)*100).toFixed(1)}%)`);
    console.log(`• P50 latency: ${metrics.p50_latency_ms}ms`);
    console.log(`• P95 latency: ${metrics.p95_latency_ms}ms`);
    console.log(`• Avg citations: ${metrics.avg_citations_per_response}`);

    // Acceptance criteria check
    const p50_pass = metrics.p50_latency_ms <= 2800;
    const p95_pass = metrics.p95_latency_ms <= 4500;
    const error_pass = metrics.error_rate_pct < 1.0;

    console.log('\n🎯 ACCEPTANCE CRITERIA:');
    console.log(`• P50 ≤ 2800ms: ${p50_pass ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`• P95 ≤ 4500ms: ${p95_pass ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`• Error rate < 1%: ${error_pass ? '✅ PASS' : '❌ FAIL'}`);

    if (p50_pass && p95_pass && error_pass) {
      console.log('\n🎉 SMOKE TESTS PASSED!');
    } else {
      console.log('\n⚠️ Some criteria need attention');
    }

    // Generate reports
    await this.generateReports();
  }
}

async function main() {
  const smokeTest = new ChatSmokeTest();
  await smokeTest.runSmokeTests();
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = ChatSmokeTest;