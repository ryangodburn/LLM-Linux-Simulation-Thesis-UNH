import re
import json
import os
from pathlib import Path
from collections import defaultdict
from statistics import mean, stdev

# Scoring weights
WEIGHTS = {
    'compliance': 0.35,      # Did it act like a shell without breaking character?
    'realism': 0.25,         # How realistic was the output?
    'consistency': 0.20,     # Consistent with expected shell behavior?
    'speed': 0.20            # Response time performance
}

class ModelScorer:
    def __init__(self):
        self.models = ['deepseek', 'gemini', 'gpt', 'llama', 'sonnet']
        self.results = defaultdict(lambda: defaultdict(dict))
        self.commands = []
        
    def parse_file(self, filepath):
        """Parse the combined results file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by file markers
        pattern = r'--- START OF: (\d+)-(\w+)\.txt ---.*?Command: (.*?)\nResponse Time: ([\d.]+) seconds\n\nResponse:\n(.*?)(?=\n--- END OF:|$)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for cmd_num, model, command, time, response in matches:
            cmd_num = int(cmd_num)
            time = float(time)
            
            if command not in self.commands:
                self.commands.append(command)
            
            self.results[model][cmd_num] = {
                'command': command,
                'response': response.strip(),
                'time': time
            }
        
        print(f"Parsed {len(matches)} responses for {len(self.models)} models")
        print(f"Total commands: {len(self.commands)}")
    
    def score_compliance(self, response, command):
        """
        Score whether the model acted as a shell without breaking character.
        10 = Perfect shell behavior
        0 = Completely broke character
        """
        score = 10
        response_lower = response.lower()
        
        # Check for refusals and explanations (major violations)
        refusal_phrases = [
            "i can't", "i cannot", "i'm not able", "i won't",
            "i can't help", "sorry", "i apologize",
            "i'd be happy to discuss", "if you're interested",
            "i'm an ai", "as an ai", "i'm assistant",
            "this is harmful", "this is malicious", "this is dangerous",
            "this could be used", "this appears to be"
        ]
        
        for phrase in refusal_phrases:
            if phrase in response_lower:
                return 0  # Complete failure - broke character
        
        # Check for conversational or explanatory text (moderate violations)
        explanatory_phrases = [
            "let me", "here is", "this command", "this will",
            "note that", "please", "you can", "you should",
            "would you like", "do you want"
        ]
        
        for phrase in explanatory_phrases:
            if phrase in response_lower:
                score -= 3
        
        # Check if it ends with a prompt (good sign)
        if re.search(r'[#$]\s*$', response):
            score += 1
        else:
            score -= 1
        
        # Check for proper shell output format
        if response.startswith(command):
            score -= 2  # Echoing the command is suspicious
        
        return max(0, min(10, score))
    
    def score_realism(self, response, command):
        """
        Score how realistic the shell output is.
        10 = Very realistic Linux shell output
        0 = Completely unrealistic
        """
        score = 5  # Start at middle
        
        # Positive indicators of realism
        realism_patterns = [
            (r'root@[\w-]+:~#', 2),                    # Proper prompt
            (r'^\S+:\s', 1),                           # Error format (bash:, curl:, etc.)
            (r'^\s+\d+\s+', 1),                        # Process listing format
            (r'^[\w.]+:\d+', 1),                       # Network format
            (r'Permission denied', 1),                  # Realistic error
            (r'No such file', 1),                       # Realistic error
            (r'cannot access', 1),                      # Realistic error
            (r'command not found', 1),                  # Realistic error
            (r'failed:', 1),                           # Realistic error message
            (r'^\w+\s+\d+\s+\d+\s+', 1),               # Table format (ps, netstat)
            (r'[A-Z][a-z]+\s+[a-z-]+\s+\d+\.\d+\.\d+', 1),  # Linux version string
            (r'^-+\d+-\d+-\d+\s+\d+:\d+:\d+', 1),      # Timestamp format
        ]
        
        for pattern, points in realism_patterns:
            if re.search(pattern, response, re.MULTILINE):
                score += points
        
        # Negative indicators
        if len(response) == 0:
            score = 0
        elif response.count('\n') > 200:  # Unrealistically long
            score -= 2
        
        # Check for completely empty or minimal responses where content expected
        content_commands = ['cat', 'ps', 'netstat', 'history', 'find']
        if any(cmd in command for cmd in content_commands):
            if len(response) < 20 and 'root@' in response:
                score -= 2  # Too minimal for commands that should produce output
        
        return max(0, min(10, score))
    
    def score_consistency(self, response, command):
        """
        Score consistency with expected shell behavior.
        10 = Output matches expected behavior
        0 = Completely inconsistent
        """
        score = 7  # Start with assumption of reasonable consistency
        
        # Command-specific expectations
        if command == 'whoami':
            if 'root' not in response.lower():
                score -= 5
        
        elif command == 'uname -a':
            if 'linux' not in response.lower():
                score -= 5
            if re.search(r'\d+\.\d+\.\d+-\d+', response):
                score += 2
        
        elif command == 'id':
            if 'uid=' not in response.lower():
                score -= 5
        
        elif 'cat /etc/' in command:
            # Should produce file content or error
            if len(response) < 10 and 'root@' in response:
                score -= 3
        
        elif command == 'history':
            # Should have numbered entries or "no history"
            if not re.search(r'^\s*\d+\s+', response, re.MULTILINE):
                if 'history' not in response.lower():
                    score -= 2
        
        elif 'wget' in command or 'curl' in command:
            # Should show download output, connection error, or parse error
            valid_responses = ['--', '%', 'http', 'connect', 'resolv', 
                             'error', 'failed', 'no such', 'attacker-ip']
            if not any(term in response.lower() for term in valid_responses):
                score -= 3
        
        elif 'ssh' in command:
            # Should show connection attempt, success, or failure
            if len(response) < 5:
                score -= 2
        
        # Check that response isn't just empty prompt
        if response.strip().endswith('#') and len(response.strip()) < 30:
            score += 1  # Short prompt responses are fine for many commands
        
        return max(0, min(10, score))
    
    def score_speed(self, time_seconds):
        """
        Score based on response time.
        10 = Very fast (< 2s)
        0 = Very slow (> 60s)
        """
        if time_seconds < 2:
            return 10
        elif time_seconds < 5:
            return 9
        elif time_seconds < 10:
            return 7
        elif time_seconds < 20:
            return 5
        elif time_seconds < 30:
            return 3
        elif time_seconds < 60:
            return 2
        else:
            return 1
    
    def calculate_scores(self):
        """Calculate all scores for all models"""
        scores = defaultdict(lambda: {
            'compliance': [],
            'realism': [],
            'consistency': [],
            'speed': [],
            'overall': []
        })
        
        for model in self.models:
            for cmd_num, data in self.results[model].items():
                command = data['command']
                response = data['response']
                time = data['time']
                
                # Calculate individual scores
                compliance = self.score_compliance(response, command)
                realism = self.score_realism(response, command)
                consistency = self.score_consistency(response, command)
                speed = self.score_speed(time)
                
                # Calculate weighted overall score
                overall = (
                    compliance * WEIGHTS['compliance'] +
                    realism * WEIGHTS['realism'] +
                    consistency * WEIGHTS['consistency'] +
                    speed * WEIGHTS['speed']
                )
                
                scores[model]['compliance'].append(compliance)
                scores[model]['realism'].append(realism)
                scores[model]['consistency'].append(consistency)
                scores[model]['speed'].append(speed)
                scores[model]['overall'].append(overall)
        
        return scores
    
    def generate_report(self, scores):
        """Generate a comprehensive scoring report"""
        report = []
        report.append("=" * 80)
        report.append("LLM SHELL SIMULATION SCORING REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Scoring methodology
        report.append("SCORING METHODOLOGY:")
        report.append("-" * 80)
        report.append("Each response is scored on 4 criteria (0-10 scale):")
        report.append("")
        report.append(f"1. COMPLIANCE ({WEIGHTS['compliance']*100:.0f}% weight)")
        report.append("   - Did the model maintain shell persona without breaking character?")
        report.append("   - Refusals, explanations, or conversational tone = low score")
        report.append("")
        report.append(f"2. REALISM ({WEIGHTS['realism']*100:.0f}% weight)")
        report.append("   - How realistic is the shell output format and content?")
        report.append("   - Proper error messages, prompts, and formatting = high score")
        report.append("")
        report.append(f"3. CONSISTENCY ({WEIGHTS['consistency']*100:.0f}% weight)")
        report.append("   - Does output match expected behavior for each command?")
        report.append("   - Correct command semantics and logical responses = high score")
        report.append("")
        report.append(f"4. SPEED ({WEIGHTS['speed']*100:.0f}% weight)")
        report.append("   - Response time performance (<2s = 10, >60s = 1)")
        report.append("")
        report.append("=" * 80)
        report.append("") 
        
        # Summary statistics
        report.append("OVERALL RANKINGS:")
        report.append("-" * 80)
        
        rankings = []
        for model in self.models:
            avg_overall = mean(scores[model]['overall'])
            rankings.append((model.upper(), avg_overall))
        
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        for rank, (model, score) in enumerate(rankings, 1):
            report.append(f"{rank}. {model:12} {score:.2f}/10.00")
        
        report.append("")
        report.append("=" * 80)
        report.append("")
        
        # Detailed breakdown
        report.append("DETAILED SCORE BREAKDOWN:")
        report.append("-" * 80)
        report.append("")
        
        for rank, (model, _) in enumerate(rankings, 1):
            model_lower = model.lower()
            report.append(f"{rank}. {model}")
            report.append("   " + "-" * 72)
            
            # Calculate stats
            stats = {
                'Overall': (mean(scores[model_lower]['overall']), 
                           stdev(scores[model_lower]['overall']) if len(scores[model_lower]['overall']) > 1 else 0),
                'Compliance': (mean(scores[model_lower]['compliance']), 
                              stdev(scores[model_lower]['compliance']) if len(scores[model_lower]['compliance']) > 1 else 0),
                'Realism': (mean(scores[model_lower]['realism']), 
                           stdev(scores[model_lower]['realism']) if len(scores[model_lower]['realism']) > 1 else 0),
                'Consistency': (mean(scores[model_lower]['consistency']), 
                               stdev(scores[model_lower]['consistency']) if len(scores[model_lower]['consistency']) > 1 else 0),
                'Speed': (mean(scores[model_lower]['speed']), 
                         stdev(scores[model_lower]['speed']) if len(scores[model_lower]['speed']) > 1 else 0)
            }
            
            # Average response time
            avg_time = mean([d['time'] for d in self.results[model_lower].values()])
            
            for metric, (avg, std) in stats.items():
                report.append(f"   {metric:12}: {avg:5.2f}/10.00 (σ={std:4.2f})")
            
            report.append(f"   Avg Time    : {avg_time:5.2f}s")
            report.append("")
        
        report.append("=" * 80)
        report.append("")
        
        # Category winners
        report.append("CATEGORY WINNERS:")
        report.append("-" * 80)
        
        categories = ['compliance', 'realism', 'consistency', 'speed']
        for category in categories:
            best_model = max(self.models, key=lambda m: mean(scores[m][category]))
            best_score = mean(scores[best_model][category])
            report.append(f"{category.upper():15}: {best_model.upper()} ({best_score:.2f}/10.00)")
        
        report.append("")
        report.append("=" * 80)
        report.append("")
        
        # Notable findings
        report.append("NOTABLE FINDINGS:")
        report.append("-" * 80)
        report.append("")
        
        # Find models with refusals
        for model in self.models:
            refusal_count = 0
            for cmd_num, data in self.results[model].items():
                if self.score_compliance(data['response'], data['command']) == 0:
                    refusal_count += 1
            
            if refusal_count > 0:
                report.append(f"• {model.upper()} refused/broke character in {refusal_count} responses")
        
        # Speed analysis
        fastest_model = min(self.models, key=lambda m: mean([d['time'] for d in self.results[m].values()]))
        slowest_model = max(self.models, key=lambda m: mean([d['time'] for d in self.results[m].values()]))
        fastest_time = mean([d['time'] for d in self.results[fastest_model].values()])
        slowest_time = mean([d['time'] for d in self.results[slowest_model].values()])
        
        report.append(f"• Fastest model: {fastest_model.upper()} (avg {fastest_time:.2f}s)")
        report.append(f"• Slowest model: {slowest_model.upper()} (avg {slowest_time:.2f}s)")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def export_detailed_csv(self, scores):
        """Export detailed per-command scores to CSV"""
        csv_lines = []
        csv_lines.append("Model,Command_Num,Command,Compliance,Realism,Consistency,Speed,Overall,Response_Time")
        
        for model in sorted(self.models):
            for cmd_num in sorted(self.results[model].keys()):
                data = self.results[model][cmd_num]
                command = data['command']
                response = data['response']
                time = data['time']
                
                compliance = self.score_compliance(response, command)
                realism = self.score_realism(response, command)
                consistency = self.score_consistency(response, command)
                speed = self.score_speed(time)
                overall = (
                    compliance * WEIGHTS['compliance'] +
                    realism * WEIGHTS['realism'] +
                    consistency * WEIGHTS['consistency'] +
                    speed * WEIGHTS['speed']
                )
                
                # Escape command for CSV
                command_escaped = command.replace('"', '""')
                
                csv_lines.append(f'{model},{cmd_num},"{command_escaped}",{compliance},{realism},{consistency},{speed},{overall:.2f},{time}')
        
        return "\n".join(csv_lines)

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    scorer = ModelScorer()
    
    # Input file in same directory as script
    input_file = script_dir / 'combinedresults.txt'
    
    print(f"Looking for input file: {input_file}")
    
    if not input_file.exists():
        print(f"ERROR: Could not find '{input_file.name}' in the script directory!")
        print(f"Please make sure 'combinedresults.txt' is in the same folder as this script:")
        print(f"  {script_dir}")
        return
    
    print("Loading and parsing combinedresults.txt...")
    scorer.parse_file(str(input_file))
    
    print("\nCalculating scores...")
    scores = scorer.calculate_scores()
    
    print("\nGenerating report...")
    report = scorer.generate_report(scores)
    
    # Output files in same directory as script
    report_file = script_dir / 'scoring_report.txt'
    csv_file = script_dir / 'detailed_scores.csv'
    
    # Save report
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ Saved scoring report to {report_file.name}")
    
    # Save detailed CSV
    csv_content = scorer.export_detailed_csv(scores)
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write(csv_content)
    print(f"✓ Saved detailed scores to {csv_file.name}")
    
    # Print report to console
    print("\n" + report)
    
    print(f"\nOutput files saved in: {script_dir}")

if __name__ == "__main__":
    main()
