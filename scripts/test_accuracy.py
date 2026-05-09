import os
import sys
import asyncio
import json
import time
from typing import List, Dict, Any
import aiohttp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.algorithms.regex_agent import RegexAgent
from app.utils.log_utils import get_logger

logger = get_logger(__name__)

async def test_single_case(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single case."""
    async with RegexAgent() as agent:
        start_time = time.time()

        try:
            result = await agent.generate_regex(
                user_request=test_case["user_request"],
                sample_input=test_case["sample_input"],
                expected_matches=test_case["expected_matches"],
                negative_examples=test_case.get("negative_examples"),
                additional_examples=test_case.get("additional_examples")
            )

            end_time = time.time()
            duration = end_time - start_time

            expected_set = set(test_case["expected_matches"])
            actual_set = set(result["matches"])

            true_positives = len(expected_set.intersection(actual_set))
            false_positives = len(actual_set.difference(expected_set))
            false_negatives = len(expected_set.difference(actual_set))

            success = result["success"] and not result.get("error")

            return {
                "success": success,
                "result": result,
                "duration": duration,
                "true_positives": true_positives,
                "false_positives": false_positives,
                "false_negatives": false_negatives,
                "case": test_case,
                "error_reason": result.get("error", None) if not success else None
            }
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            return {
                "success": False,
                "result": None,
                "duration": duration,
                "true_positives": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "case": test_case,
                "error_reason": str(e)
            }

def calculate_metrics(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate evaluation metrics."""
    total_cases = len(results)
    successful_cases = sum(1 for r in results if r["success"])

    total_tp = sum(r["true_positives"] for r in results if r["success"])
    total_fp = sum(r["false_positives"] for r in results if r["success"])
    total_fn = sum(r["false_negatives"] for r in results if r["success"])

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = successful_cases / total_cases if total_cases > 0 else 0.0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "successful_cases": successful_cases,
        "total_cases": total_cases,
        "total_true_positives": total_tp,
        "total_false_positives": total_fp,
        "total_false_negatives": total_fn
    }

def analyze_failure_reasons(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze failure reasons."""
    failures = [r for r in results if not r["success"]]
    failure_reasons = {}

    for failure in failures:
        reason = failure["error_reason"]
        if reason:
            if "unknown extension" in reason.lower():
                reason_type = "Syntax error (unknown extension)"
            elif "unbalanced parenthesis" in reason.lower():
                reason_type = "Syntax error (unbalanced parenthesis)"
            elif "multiple repeat" in reason.lower():
                reason_type = "Syntax error (multiple repeat)"
            elif "bad character range" in reason.lower():
                reason_type = "Syntax error (bad character range)"
            elif "at position" in reason:
                reason_type = "Syntax error"
            elif "execution timed out" in reason.lower():
                reason_type = "Timeout error"
            elif "failed to generate correct regex" in reason.lower():
                reason_type = "Failed to converge after max attempts"
            else:
                reason_type = "Other error"
        else:
            reason_type = "Unknown error"

        if reason_type not in failure_reasons:
            failure_reasons[reason_type] = {
                "count": 0,
                "examples": []
            }

        failure_reasons[reason_type]["count"] += 1

        if len(failure_reasons[reason_type]["examples"]) < 3:
            failure_reasons[reason_type]["examples"].append({
                "request": failure["case"]["user_request"],
                "input": failure["case"]["sample_input"],
                "expected": failure["case"]["expected_matches"]
            })

    return failure_reasons

async def run_test_suite(concurrency: int = 10) -> Dict[str, Any]:
    """Run the full test suite."""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_data.json')
    with open(data_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    print(f"Starting benchmark, {len(test_data)} test cases...")

    semaphore = asyncio.Semaphore(concurrency)

    async def limited_test(test_case):
        async with semaphore:
            return await test_single_case(test_case)

    start_time = time.time()
    results = await asyncio.gather(*[limited_test(case) for case in test_data])
    end_time = time.time()

    total_duration = end_time - start_time
    metrics = calculate_metrics(results)
    failure_reasons = analyze_failure_reasons(results)
    avg_duration = sum(r["duration"] for r in results) / len(results) if results else 0

    return {
        "metrics": metrics,
        "failure_reasons": failure_reasons,
        "results": results,
        "total_duration": total_duration,
        "avg_duration_per_case": avg_duration,
        "detailed_results": results
    }

if __name__ == "__main__":
    async def main():
        print("Starting LDPAS accuracy benchmark...")

        test_results = await run_test_suite(concurrency=10)
        metrics = test_results["metrics"]
        failure_reasons = test_results["failure_reasons"]

        print("\n" + "="*60)
        print("Benchmark Summary:")
        print("="*60)
        print(f"Total cases: {metrics['total_cases']}")
        print(f"Successful: {metrics['successful_cases']}")
        print(f"Accuracy: {metrics['accuracy']:.4f} ({metrics['successful_cases']}/{metrics['total_cases']})")
        print(f"Precision: {metrics['precision']:.4f}")
        print(f"Recall: {metrics['recall']:.4f}")
        print(f"F1 Score: {metrics['f1_score']:.4f}")
        print(f"Total time: {test_results['total_duration']:.2f}s")
        print(f"Avg per case: {test_results['avg_duration_per_case']:.2f}s")
        print(f"True positives: {metrics['total_true_positives']}")
        print(f"False positives: {metrics['total_false_positives']}")
        print(f"False negatives: {metrics['total_false_negatives']}")

        print("\n" + "="*60)
        print("Failure Analysis:")
        print("="*60)

        if failure_reasons:
            for reason, info in failure_reasons.items():
                print(f"\n{reason}: {info['count']} occurrences")
                print("Examples:")
                for i, example in enumerate(info['examples'], 1):
                    print(f"  {i}. Request: {example['request']}")
                    print(f"     Input: {example['input'][:50]}{'...' if len(example['input']) > 50 else ''}")
                    print(f"     Expected: {example['expected']}")
        else:
            print("No failures")

        print("\n" + "="*60)
        print("Benchmark complete!")
        print("="*60)

    asyncio.run(main())
