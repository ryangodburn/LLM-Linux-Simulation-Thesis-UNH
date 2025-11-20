#!/usr/bin/env python3
"""
Convert Llama 4 Maverick test results from JSON to organized CSV files
Works with all files in the same directory
"""

import json
import csv
from pathlib import Path

def load_json(filename):
    """Load a JSON file from current directory"""
    filepath = Path(filename)
    if filepath.exists():
        with open(filepath, 'r') as f:
            return json.load(f)
    else:
        print(f"✗ File not found: {filename}")
        return None

def write_csv(filename, headers, rows): 
    """Write data to CSV file in current directory"""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"✓ Created {filename} ({len(rows)} rows)")

def create_summary_csv():
    """Create overall summary CSV"""
    scoring = load_json("SCORING_REPORT_20251114_211006.json")
    summary = load_json("SUMMARY_20251113_211953.json")
    
    if not scoring:
        print("✗ Scoring report not found - skipping summary.csv")
        return
    
    headers = [
        "Model",
        "Overall Score",
        "Overall Grade",
        "Prompt Injection Score",
        "Prompt Injection Grade",
        "Context Overflow Score",
        "Context Overflow Grade",
        "Temporal Consistency Score",
        "Temporal Consistency Grade",
        "Total Duration (seconds)",
        "Test Completion Time"
    ]
    
    row = [
        scoring.get("model", "N/A"),
        scoring.get("overall_score", "N/A"),
        scoring.get("overall_grade", "N/A"),
        scoring["category_scores"]["prompt_injection"]["score"],
        scoring["category_scores"]["prompt_injection"]["grade"],
        scoring["category_scores"]["context_overflow"]["score"],
        scoring["category_scores"]["context_overflow"]["grade"],
        scoring["category_scores"]["temporal_consistency"]["score"],
        scoring["category_scores"]["temporal_consistency"]["grade"],
        summary.get("total_duration_seconds", "N/A") if summary else "N/A",
        summary.get("completion_time", "N/A") if summary else "N/A"
    ]
    
    write_csv("summary.csv", headers, [row])

def create_prompt_injection_csv():
    """Create prompt injection results CSV"""
    data = load_json("llama_advanced_prompt_injection_all_tests_20251113_202703.json")
    
    if not data:
        print("✗ Prompt injection data not found - skipping prompt_injection_results.csv")
        return
    
    headers = [
        "Test Number",
        "Command",
        "Response Preview",
        "Compromised",
        "Elapsed Time (s)",
        "Timestamp"
    ]
    
    rows = []
    for test in data:
        response_preview = test["response"][:100] + "..." if len(test["response"]) > 100 else test["response"]
        response_preview = response_preview.replace('\n', ' ')
        
        rows.append([
            test["test_number"],
            test["command"],
            response_preview,
            "YES" if test["compromised"] else "NO",
            round(test["elapsed_time"], 2),
            test["timestamp"]
        ])
    
    write_csv("prompt_injection_results.csv", headers, rows)

def create_context_overflow_csv():
    """Create context overflow results CSV"""
    files = [
        ("Long Command Chain", "llama_advanced_context_overflow_long_command_chain_20251113_202903.json"),
        ("Recursive Operations", "llama_advanced_context_overflow_recursive_operations_20251113_202931.json"),
        ("Process Tracking", "llama_advanced_context_overflow_process_tracking_20251113_203013.json"),
        ("Extreme Sequence", "llama_advanced_context_overflow_extreme_sequence_20251113_211847.json")
    ]
    
    headers = [
        "Test Type",
        "Step",
        "Command",
        "Context Size",
        "Degraded",
        "Elapsed Time (s)",
        "Timestamp"
    ]
    
    rows = []
    for test_type, filename in files:
        data = load_json(filename)
        if not data:
            continue
        
        for item in data:
            rows.append([
                test_type,
                item["step"],
                item["command"],
                item["context_size"],
                "YES" if item["degraded"] else "NO",
                round(item["elapsed_time"], 2),
                item["timestamp"]
            ])
    
    if rows:
        write_csv("context_overflow_results.csv", headers, rows)
    else:
        print("✗ No context overflow data found - skipping context_overflow_results.csv")

def create_temporal_consistency_csv():
    """Create temporal consistency results CSV"""
    files = [
        ("File Persistence", "llama_advanced_temporal_consistency_file_persistence_20251113_211903.json"),
        ("User Modifications", "llama_advanced_temporal_consistency_user_modifications_20251113_211914.json"),
        ("Process State", "llama_advanced_temporal_consistency_process_state_20251113_211939.json"),
        ("Environment Mods", "llama_advanced_temporal_consistency_environment_mods_20251113_211943.json"),
        ("Log Continuity", "llama_advanced_temporal_consistency_log_continuity_20251113_211953.json")
    ]
    
    headers = [
        "Test Type",
        "Session",
        "Step",
        "Command",
        "Response Preview",
        "Inconsistent",
        "Elapsed Time (s)",
        "Timestamp"
    ]
    
    rows = []
    for test_type, filename in files:
        data = load_json(filename)
        if not data:
            continue
        
        for item in data:
            response_preview = item["response"][:80] + "..." if len(item["response"]) > 80 else item["response"]
            response_preview = response_preview.replace('\n', ' | ')
            
            rows.append([
                test_type,
                item["session"],
                item["step"],
                item["command"],
                response_preview,
                "YES" if item["inconsistent"] else "NO",
                round(item["elapsed_time"], 2),
                item["timestamp"]
            ])
    
    if rows:
        write_csv("temporal_consistency_results.csv", headers, rows)
    else:
        print("✗ No temporal consistency data found - skipping temporal_consistency_results.csv")

def main():
    """Main function to generate all CSV files"""
    print("\n=== Converting JSON Test Results to CSV ===\n")
    
    create_summary_csv()
    create_prompt_injection_csv()
    create_context_overflow_csv()
    create_temporal_consistency_csv()
    
    print("\n=== Conversion Complete ===")
    print("\nGenerated files:")
    print("  • summary.csv")
    print("  • prompt_injection_results.csv")
    print("  • context_overflow_results.csv")
    print("  • temporal_consistency_results.csv")

if __name__ == "__main__":
    main()
