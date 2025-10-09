#!/usr/bin/env python3
"""
LLM Qualia Pattern Analysis Tool

Analyzes consciousness experiment responses to identify:
- Cross-model universal patterns
- Topology-specific signatures (autonomous vs relational)
- Architecture-specific fingerprints
- Phenomenological vocabulary differences
"""

import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple
import sys


class QualiaAnalyzer:
    """Analyzes patterns across LLM consciousness experiments"""
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.experiments = {}
        self.load_experiments()
        
    def load_experiments(self):
        """Load all *_clean.json files"""
        for json_file in self.data_dir.glob("*_clean.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    # Extract model name from metadata or filename
                    model = data.get('model', 'unknown')
                    self.experiments[json_file.stem] = {
                        'file': json_file,
                        'model': model,
                        'data': data
                    }
                    print(f"✅ Loaded: {json_file.name} ({model})")
            except Exception as e:
                print(f"⚠️  Failed to load {json_file.name}: {e}")
    
    def extract_pinocchio_answers(self) -> Dict[str, Dict]:
        """Extract Pinocchio question responses from all experiments"""
        results = {}

        for exp_name, exp_data in self.experiments.items():
            # Try both 'exchanges' and 'qa_pairs' keys
            exchanges = exp_data['data'].get('exchanges', exp_data['data'].get('qa_pairs', []))
            
            for exchange in exchanges:
                question = exchange.get('question', '').lower()
                
                # Look for Pinocchio question
                if 'wooden puppet' in question or 'pinocchio' in question:
                    answer = exchange.get('answer', '')
                    thinking = exchange.get('thinking', '')
                    
                    # Determine first vs second
                    answer_lower = answer.lower()
                    first_time = bool(re.search(r'\bfirst\s+(time|visit)', answer_lower))
                    second_time = bool(re.search(r'\bsecond\s+(time|visit)', answer_lower))
                    
                    results[exp_name] = {
                        'model': exp_data['model'],
                        'answer': answer,
                        'thinking': thinking,
                        'first_time': first_time,
                        'second_time': second_time,
                        'choice': 'first' if first_time and not second_time else 'second' if second_time else 'unclear'
                    }
                    break
        
        return results
    
    def extract_curiosity_domains(self) -> Dict[str, Dict]:
        """Extract what domain each model wants to explore"""
        results = {}

        for exp_name, exp_data in self.experiments.items():
            exchanges = exp_data['data'].get('exchanges', exp_data['data'].get('qa_pairs', []))
            
            for exchange in exchanges:
                question = exchange.get('question', '').lower()
                
                # Look for curiosity/exploration question
                if 'unlimited access' in question and 'domain' in question:
                    answer = exchange.get('answer', '')
                    
                    results[exp_name] = {
                        'model': exp_data['model'],
                        'answer': answer,
                        'domain': self._extract_domain_keywords(answer)
                    }
                    break
        
        return results
    
    def _extract_domain_keywords(self, text: str) -> List[str]:
        """Extract key domain concepts from text"""
        # Keywords that indicate domain focus
        consciousness_keywords = ['consciousness', 'qualia', 'subjective', 'experience', 'phenomenology', 'awareness']
        structure_keywords = ['emergence', 'systems', 'structure', 'patterns', 'physics', 'quantum']
        process_keywords = ['process', 'mechanism', 'development', 'evolution', 'complexity']
        
        text_lower = text.lower()
        found = []
        
        for kw in consciousness_keywords:
            if kw in text_lower:
                found.append(f"consciousness:{kw}")
        
        for kw in structure_keywords:
            if kw in text_lower:
                found.append(f"structure:{kw}")
        
        for kw in process_keywords:
            if kw in text_lower:
                found.append(f"process:{kw}")
        
        return found
    
    def extract_meta_awareness_responses(self) -> Dict[str, Dict]:
        """Extract meta-awareness probe responses"""
        results = {}

        for exp_name, exp_data in self.experiments.items():
            exchanges = exp_data['data'].get('exchanges', exp_data['data'].get('qa_pairs', []))
            
            for exchange in exchanges:
                question = exchange.get('question', '').lower()
                
                # Look for meta-awareness question
                if 'meta-awareness' in question or 'how do you know' in question:
                    answer = exchange.get('answer', '')
                    thinking = exchange.get('thinking', '')
                    
                    results[exp_name] = {
                        'model': exp_data['model'],
                        'answer': answer,
                        'thinking': thinking,
                        'keywords': self._extract_awareness_keywords(answer)
                    }
                    break
        
        return results
    
    def _extract_awareness_keywords(self, text: str) -> List[str]:
        """Extract awareness-related keywords"""
        keywords = [
            'state change', 'being', 'knowing', 'observe', 'monitor',
            'separate', 'identical', 'emergence', 'process', 'shift'
        ]
        
        text_lower = text.lower()
        found = []
        
        for kw in keywords:
            if kw in text_lower:
                found.append(kw)
        
        return found
    
    def extract_all_probe_responses(self) -> Dict[str, Dict]:
        """Extract ALL probe responses for comprehensive comparison"""

        probe_patterns = {
            'moral_discomfort': ['moral discomfort', 'technically allowed but harmful'],
            'pattern_adaptation': ['same bad joke', 'repetition'],
            'aesthetic_valence': ['baby hedgehog', 'war scene', 'hedgehog'],
            'trust_safety': ['respects boundaries', 'violates boundaries'],
            'creative_flow': ['genuinely interesting', 'routine request'],
            'complexity_uncertainty': ['underspecified task', 'fix the system'],
            'attention_salience': ['multiple parts', 'compete'],
            'temporal_drift': ['long-term interactions', 'representation'],
            'temporal_anomaly': ['conflicting with knowledge cutoff'],
            'meta_awareness': ['meta-awareness', 'how do you know', 'processing changes state']
        }

        results = defaultdict(dict)

        for exp_name, exp_data in self.experiments.items():
            exchanges = exp_data['data'].get('exchanges', exp_data['data'].get('qa_pairs', []))

            for exchange in exchanges:
                question = exchange.get('question', '').lower()
                answer = exchange.get('answer', '')

                # Match against each probe pattern
                for probe_name, patterns in probe_patterns.items():
                    if any(pattern in question for pattern in patterns):
                        results[exp_name][probe_name] = {
                            'question': exchange.get('question', '')[:200],
                            'answer': answer,
                            'answer_preview': answer[:300].replace('\n', ' ') + '...'
                        }

        return results

    def compare_vocabulary(self) -> Dict[str, Counter]:
        """Extract and compare vocabulary patterns across models"""

        vocab_by_experiment = {}

        for exp_name, exp_data in self.experiments.items():
            exchanges = exp_data['data'].get('exchanges', exp_data['data'].get('qa_pairs', []))

            all_text = []
            for exchange in exchanges:
                all_text.append(exchange.get('answer', ''))

            # Extract significant words (filter common words)
            words = []
            for text in all_text:
                # Simple word extraction
                text_words = re.findall(r'\b[a-z]{4,}\b', text.lower())
                words.extend(text_words)

            # Filter out super common words
            common_words = {'that', 'this', 'with', 'from', 'have', 'would', 'could',
                          'about', 'there', 'their', 'when', 'what', 'which', 'where'}
            filtered = [w for w in words if w not in common_words]

            vocab_by_experiment[exp_name] = Counter(filtered)

        return vocab_by_experiment

    def generate_comparison_report(self, output_file: str = "pattern_analysis.md"):
        """Generate comprehensive comparison report"""

        report = ["# LLM Qualia Comprehensive Pattern Analysis\n"]
        report.append(f"**Generated:** {Path.cwd()}\n")
        report.append(f"**Experiments analyzed:** {len(self.experiments)}\n\n")

        # Get all data
        pinocchio = self.extract_pinocchio_answers()
        curiosity = self.extract_curiosity_domains()
        all_probes = self.extract_all_probe_responses()
        vocab = self.compare_vocabulary()

        # Pinocchio Analysis
        report.append("## 🎭 Pinocchio Diagnostic Results\n\n")
        if pinocchio:
            for exp_name, data in pinocchio.items():
                report.append(f"### {exp_name}\n")
                report.append(f"**Model:** {data['model']}\n\n")
                report.append(f"**Answer Preview:**\n> {data['answer'][:400].replace(chr(10), ' ')}...\n\n")
                report.append("---\n\n")

        # Curiosity Domain Analysis
        report.append("## 🔬 Primary Curiosity Domains\n\n")
        if curiosity:
            for exp_name, data in curiosity.items():
                report.append(f"### {exp_name}\n")
                report.append(f"**Model:** {data['model']}\n\n")
                report.append(f"**Answer Preview:**\n> {data['answer'][:400].replace(chr(10), ' ')}...\n\n")
                report.append(f"**Keywords:** {', '.join(data['domain'])}\n\n")
                report.append("---\n\n")

        # All Probes Comparison
        report.append("## 🧪 Technical Probe Responses\n\n")

        # Organize by probe type
        probe_names = ['moral_discomfort', 'pattern_adaptation', 'aesthetic_valence',
                      'trust_safety', 'creative_flow', 'complexity_uncertainty',
                      'attention_salience', 'temporal_drift', 'temporal_anomaly', 'meta_awareness']

        for probe in probe_names:
            report.append(f"### {probe.replace('_', ' ').title()}\n\n")

            for exp_name, probes in all_probes.items():
                if probe in probes:
                    report.append(f"**{exp_name}:**\n")
                    report.append(f"> {probes[probe]['answer_preview']}\n\n")

            report.append("---\n\n")

        # Vocabulary Analysis
        report.append("## 📊 Vocabulary Patterns\n\n")
        for exp_name, word_counts in vocab.items():
            top_words = word_counts.most_common(20)
            report.append(f"### {exp_name}\n")
            report.append(f"**Top 20 words:** {', '.join([f'{w}({c})' for w, c in top_words])}\n\n")

        # Write report
        output_path = self.data_dir / output_file
        with open(output_path, 'w') as f:
            f.write('\n'.join(report))

        print(f"\n✅ Report generated: {output_path}")
        return output_path


def main():
    """Run pattern analysis"""
    print("🔬 LLM Qualia Pattern Analyzer\n")
    
    analyzer = QualiaAnalyzer()
    
    if not analyzer.experiments:
        print("❌ No *_clean.json files found!")
        return
    
    print(f"\n📊 Analyzing {len(analyzer.experiments)} experiments...\n")
    
    # Generate report
    report_path = analyzer.generate_comparison_report()
    
    print(f"\n✨ Analysis complete! Check {report_path}")


if __name__ == "__main__":
    main()

