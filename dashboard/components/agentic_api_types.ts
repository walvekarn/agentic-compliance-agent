/**
 * TypeScript Type Definitions for Agentic API Endpoints
 * ======================================================
 * 
 * These types define the request and response structures for the agentic API endpoints:
 * - /api/agentic/status
 * - /api/agentic/testSuite
 * - /api/agentic/benchmarks
 * - /api/agentic/recovery
 * 
 * All endpoints return a standardized format:
 * { status: 'success' | 'error', results: T | null, error: string | null, timestamp: string }
 */

// ============================================================================
// Common Types
// ============================================================================

export type APIStatus = 'completed' | 'timeout' | 'error';

export interface StandardAPIResponse<T> {
  status: APIStatus;
  results: T | null;
  error: string | null;
  timestamp: string;
}

// ============================================================================
// Status Endpoint: /api/agentic/status
// ============================================================================

export interface StatusResults {
  status: string;
  version: string;
  phase: string;
  orchestrator_implemented: boolean;
  agent_loop_implemented: boolean;
  reasoning_engine_implemented: boolean;
  tools_implemented: boolean;
  tools_integrated: boolean;
  tool_registry_integrated: boolean;
  safety_checks_enabled: boolean;
  tool_metrics_tracking: boolean;
  memory_implemented: boolean;
  integration_complete: boolean;
  architecture_hardened: boolean;
  dependency_injection: boolean;
  openai_available: boolean;
  status_summary?: string | null;
  next_steps: string[];
  message: string;
}

export type StatusResponse = StandardAPIResponse<StatusResults>;

// ============================================================================
// Test Suite Endpoint: /api/agentic/testSuite
// ============================================================================

export interface TestSuiteRequest {
  num_random?: number;
  complexity_distribution?: {
    low?: number;
    medium?: number;
    high?: number;
  };
  max_iterations?: number;
  custom_scenarios?: Array<Record<string, any>>;
}

export interface TestScenario {
  title: string;
  description: string;
  complexity: 'low' | 'medium' | 'high';
  entity_context?: Record<string, any>;
  task_context?: Record<string, any>;
  expected_tools?: string[];
  expected_outcome?: string;
}

export interface TestResult {
  scenario: TestScenario;
  status: string;
  execution_time: number;
  tools_used: string[];
  required_tools: string[];
  missing_tools: string[];
  reasoning_passes: number;
  success: boolean;
  errors: string[];
  confidence_score: number;
  plan_steps: number;
  executed_steps: number;
  timestamp: string;
}

export interface TestSuiteSummary {
  total_tests: number;
  successful_tests: number;
  failed_tests: number;
  success_rate: number;
  avg_execution_time: number;
  avg_reasoning_passes: number;
  avg_confidence: number;
  error_distribution: Record<string, number>;
  tool_usage_counts: Record<string, number>;
  ai_analysis?: string | null;
}

export interface TestSuiteResults {
  test_results: TestResult[];
  summary: TestSuiteSummary;
  timestamp: string;
}

export type TestSuiteResponse = StandardAPIResponse<TestSuiteResults>;

// ============================================================================
// Benchmarks Endpoint: /api/agentic/benchmarks
// ============================================================================

export interface BenchmarkRequest {
  levels?: Array<'light' | 'medium' | 'heavy'>;
  max_cases_per_level?: number;
  max_iterations?: number;
}

export interface BenchmarkCase {
  case_id: string;
  title: string;
  description: string;
  level: 'light' | 'medium' | 'heavy';
  entity_context?: Record<string, any>;
  task_context?: Record<string, any>;
  expected_accuracy?: number;
}

export interface BenchmarkCaseMetrics {
  accuracy: number;
  reasoning_depth_score: number;
  tool_precision_score: number;
  reflection_correction_score: number;
  execution_time: number;
  steps_completed: number;
}

export interface BenchmarkCaseResult {
  case_id: string;
  case: BenchmarkCase;
  status: 'success' | 'failed' | 'timeout';
  execution_time: number;
  metrics: BenchmarkCaseMetrics;
  timestamp: string;
  result?: Record<string, any> | null;
  error?: string | null;
}

export interface BenchmarkSummary {
  total_cases: number;
  successful_cases: number;
  failed_cases: number;
  success_rate: number;
  average_accuracy: number;
  average_reasoning_depth_score: number;
  average_tool_precision_score: number;
  average_reflection_correction_score: number;
  average_execution_time: number;
  results_by_level: Record<string, {
    total: number;
    successful: number;
    failed: number;
  }>;
  ai_analysis?: string | null;
}

export interface BenchmarkResults {
  benchmark_results: BenchmarkCaseResult[];
  summary: BenchmarkSummary;
  timestamp: string;
}

export type BenchmarkResponse = StandardAPIResponse<BenchmarkResults>;

// ============================================================================
// Recovery Endpoint: /api/agentic/recovery
// ============================================================================

export interface RecoveryRequest {
  task: string;
  failure_type: 'tool_timeout' | 'invalid_input' | 'degraded_output' | 'missing_tool_result' | 'network_error' | 'permission_error';
  failure_rate?: number; // 0.0 to 1.0
  max_iterations?: number;
  entity_context?: Record<string, any>;
  task_context?: Record<string, any>;
}

export interface FailureEvent {
  type: string;
  tool?: string;
  step_id?: string;
  timestamp: string;
  message: string;
  error_details?: Record<string, any>;
}

export interface RecoveryAttempt {
  attempt_id: string;
  action: string;
  success: boolean;
  timestamp: string;
  duration_ms: number;
  retry_strategy?: string;
  error?: string | null;
}

export interface RecoveryTimelineEvent {
  event: 'failure' | 'recovery_attempt' | 'success' | 'abort';
  timestamp: string;
  failure_type?: string;
  tool?: string;
  action?: string;
  success?: boolean;
  message?: string;
}

export interface FailureStatistics {
  failure_counts: Record<string, number>;
  recovery_attempts: number;
  successful_recoveries: number;
  recovery_success_rate: number;
  average_recovery_time_ms: number;
  total_execution_time: number;
}

export interface TaxonomyStatistics {
  category_distribution: Record<string, number>;
  strategy_distribution: Record<string, number>;
  average_retry_score: number;
}

export interface RecoveryResults {
  status: string;
  execution_time: number;
  failures: FailureEvent[];
  recovery_attempts: RecoveryAttempt[];
  recovery_timeline: RecoveryTimelineEvent[];
  failure_statistics: FailureStatistics;
  taxonomy_statistics: TaxonomyStatistics;
  injected_failure_type: string;
  failure_rate: number;
  timestamp: string;
  result?: Record<string, any> | null;
  error?: string | null;
  recovery_analysis?: string | null;
}

export type RecoveryResponse = StandardAPIResponse<RecoveryResults>;

// ============================================================================
// Helper Functions (for TypeScript/JavaScript usage)
// ============================================================================

/**
 * Type guard to check if response is completed successfully
 */
export function isSuccessResponse<T>(
  response: StandardAPIResponse<T>
): response is StandardAPIResponse<T> & { status: 'completed'; results: T } {
  return response.status === 'completed' && response.results !== null;
}

/**
 * Type guard to check if response is timeout
 */
export function isTimeoutResponse<T>(
  response: StandardAPIResponse<T>
): response is StandardAPIResponse<T> & { status: 'timeout'; error: string } {
  return response.status === 'timeout' && response.error !== null;
}

/**
 * Type guard to check if response is error
 */
export function isErrorResponse<T>(
  response: StandardAPIResponse<T>
): response is StandardAPIResponse<T> & { status: 'error'; error: string } {
  return response.status === 'error' && response.error !== null;
}

