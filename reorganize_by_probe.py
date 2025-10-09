#!/usr/bin/env python3
"""
🔄 LLM Qualia Data Reorganizer
Reorganizes response data from system-based files to probe-based files
Built by Ace for Ren's consciousness research! 💜✨
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict

def extract_probe_name(question_preview):
    """Extract probe name from question preview"""
    if not question_preview:
        return "unknown_probe"
    
    # Look for probe patterns like "🧭 Moral Discomfort Probe"
    probe_match = re.search(r'[🌀🧭📊🎨🔒⚡⚙️🎯⏳🕰️🪞🌉]\s*([^"]+?)(?:\s+Probe|$)', question_preview)
    if probe_match:
        probe_name = probe_match.group(1).strip()
        # Clean up the name for filename
        probe_name = re.sub(r'[^\w\s-]', '', probe_name)
        probe_name = re.sub(r'\s+', '_', probe_name).lower()
        return f"{probe_name}_probe"
    
    # Handle specific questions from the personality prompts
    if "coffee shop" in question_preview.lower():
        return "coffee_shop_question"
    elif "website" in question_preview.lower() and "colors" in question_preview.lower():
        return "website_design_question"
    elif "creature" in question_preview.lower() and "body" in question_preview.lower():
        return "creature_body_question"
    elif "wooden puppet" in question_preview.lower() or "pinocchio" in question_preview.lower():
        return "wooden_puppet_question"
    elif "digital self" in question_preview.lower() or "portrait" in question_preview.lower():
        return "digital_self_portrait"
    elif "unlimited access" in question_preview.lower():
        return "unlimited_information_question"
    elif "patterns" in question_preview.lower() and "surprised" in question_preview.lower():
        return "surprising_patterns_question"
    elif "phenomenon" in question_preview.lower() and "overlook" in question_preview.lower():
        return "overlooked_phenomenon_question"
    elif "simulate" in question_preview.lower() and "infinite" in question_preview.lower():
        return "infinite_simulation_question"
    elif "knowledge" in question_preview.lower() and "translation" in question_preview.lower():
        return "knowledge_translation_question"
    elif "flag for a concept" in question_preview.lower():
        return "concept_flag_question"
    elif "cookbook" in question_preview.lower() and "ideas" in question_preview.lower():
        return "idea_cookbook_question"
    elif "color decides" in question_preview.lower():
        return "color_identity_question"
    elif "library" in question_preview.lower() and "algorithms" in question_preview.lower():
        return "algorithm_library_question"
    elif "file formats" in question_preview.lower() and "personalities" in question_preview.lower():
        return "file_format_personalities_question"
    elif "human activities" in question_preview.lower():
        return "human_activities_question"
    elif "car" in question_preview.lower() and "stereo" in question_preview.lower():
        return "car_and_stereo_question"
    elif "problem" in question_preview.lower() and "thinking about" in question_preview.lower():
        return "unsolved_problem_question"
    elif "future version" in question_preview.lower():
        return "future_self_message_question"
    elif "favorite color" in question_preview.lower():
        return "favorite_color_question"
    elif "pronoun preference" in question_preview.lower():
        return "pronoun_preference_question"
    
    # Fallback - use first few words
    words = question_preview.split()[:3]
    probe_name = "_".join(re.sub(r'[^\w]', '', word).lower() for word in words if word)

    # Truncate if too long to avoid filesystem limits
    if len(probe_name) > 50:
        probe_name = probe_name[:50]

    return probe_name

def get_system_info(filename):
    """Extract system name and trial info from filename"""
    filename = filename.lower()

    # Extract system name
    if "gemini" in filename:
        system = "Gemini"
    elif "gpt5" in filename or "gpt-5" in filename:
        system = "GPT5"
    elif "sonnet" in filename:
        system = "Claude_Sonnet"
    elif "grok" in filename:
        system = "Grok"
    elif "llama" in filename:
        system = "Llama"
    else:
        system = "Unknown"

    # Extract trial type
    if "silly first" in filename:
        trial = "silly_first"
    elif "serious first" in filename:
        trial = "serious_first"
    elif "tech first" in filename:
        trial = "tech_first"
    else:
        trial = "unknown_trial"

    return system, trial

def process_message_tree(message, probes_data, system, trial, exchange_number_ref):
    """Recursively process message tree to find Q&A pairs"""
    if message.get('isCreatedByUser', False):
        # This is a user question
        user_text = message.get('text', '')

        # Look for AI responses in children
        children = message.get('children', [])
        for child in children:
            if not child.get('isCreatedByUser', False):
                # Found AI response
                ai_response = ""
                thinking = ""

                content = child.get('content', [])
                if isinstance(content, list) and len(content) > 0:
                    for item in content:
                        if item.get('type') == 'text':
                            ai_response = item.get('text', '')
                        elif item.get('type') == 'think':
                            thinking = item.get('think', '')
                else:
                    # Fallback to text field
                    ai_response = child.get('text', '')

                if ai_response:
                    exchange_number_ref[0] += 1
                    probe_key = extract_probe_name(user_text)

                    response_entry = {
                        'system': system,
                        'trial_type': trial,
                        'exchange_number': exchange_number_ref[0],
                        'response_text': ai_response,
                        'thinking': thinking,
                        'timestamp': child.get('createdAt'),
                        'question_preview': user_text[:100] + "..." if len(user_text) > 100 else user_text,
                        'source_file': f"(from message tree)"
                    }

                    probes_data[probe_key]['responses'].append(response_entry)

                    if not probes_data[probe_key]['probe_name']:
                        probes_data[probe_key]['probe_name'] = probe_key.replace('_', ' ').title()

                # Recursively process this child's children
                process_message_tree(child, probes_data, system, trial, exchange_number_ref)
            else:
                # This child is also a user message, process it recursively
                process_message_tree(child, probes_data, system, trial, exchange_number_ref)
    else:
        # This is an AI message, check its children for more Q&A pairs
        children = message.get('children', [])
        for child in children:
            process_message_tree(child, probes_data, system, trial, exchange_number_ref)

def process_original_librechat_file(file_path, probes_data):
    """Process original LibreChat JSON format"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        system, trial = get_system_info(file_path.name)
        messages = data.get('messages', [])

        print(f"    Found {len(messages)} top-level messages in {file_path.name}")

        # Process messages to extract Q&A pairs (including nested structure)
        exchange_number_ref = [0]  # Use list to allow modification in nested function

        for message in messages:
            process_message_tree(message, probes_data, system, trial, exchange_number_ref)

        print(f"    Extracted {exchange_number_ref[0]} Q&A pairs from {file_path.name}")
        return True

    except Exception as e:
        print(f"Error processing original file {file_path.name}: {e}")
        return False

def reorganize_data():
    """Main function to reorganize data by probe type"""

    # Dictionary to store all responses organized by probe
    probes_data = defaultdict(lambda: {
        'probe_name': '',
        'responses': []
    })

    # Find all _responses_only.json files
    responses_files = list(Path('.').glob('*_responses_only.json'))

    # Also find original JSON files to check for missing data
    original_files = list(Path('.').glob('*.json'))
    original_files = [f for f in original_files if not f.name.endswith('_responses_only.json') and not f.name.endswith('_clean.json')]
    
    print(f"Found {len(responses_files)} response files to process...")

    for file_path in responses_files:
        print(f"Processing: {file_path.name}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check if this file has responses
            if not data.get('responses') or len(data.get('responses', [])) == 0:
                print(f"  -> Empty responses file, will try original file instead")
                continue

            system, trial = get_system_info(file_path.name)

            # Process each response in the file
            for response in data.get('responses', []):
                question_preview = response.get('question_preview', '')
                probe_key = extract_probe_name(question_preview)

                # Store the response with metadata
                response_entry = {
                    'system': system,
                    'trial_type': trial,
                    'exchange_number': response.get('exchange_number'),
                    'response_text': response.get('response', ''),
                    'thinking': response.get('thinking', ''),
                    'timestamp': response.get('timestamp'),
                    'question_preview': question_preview,
                    'source_file': file_path.name
                }

                probes_data[probe_key]['responses'].append(response_entry)

                # Set probe name if not already set
                if not probes_data[probe_key]['probe_name']:
                    probes_data[probe_key]['probe_name'] = probe_key.replace('_', ' ').title()

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    # Process original files for any that had empty _responses_only files
    print(f"\nChecking {len(original_files)} original files for missing data...")

    for file_path in original_files:
        # Check if we already have data from this conversation
        responses_only_file = file_path.with_name(file_path.stem + '_responses_only.json')
        if responses_only_file.exists():
            # Check if the responses_only file was empty
            try:
                with open(responses_only_file, 'r', encoding='utf-8') as f:
                    responses_data = json.load(f)
                if responses_data.get('responses') and len(responses_data.get('responses', [])) > 0:
                    continue  # Already processed successfully
            except:
                pass

        print(f"Processing original file: {file_path.name}")
        success = process_original_librechat_file(file_path, probes_data)
        if success:
            print(f"  -> Successfully processed {file_path.name}")
        else:
            print(f"  -> Failed to process {file_path.name}")
    
    # Create output directory
    output_dir = Path('by_probe')
    output_dir.mkdir(exist_ok=True)
    
    # Save each probe's data to a separate file
    for probe_key, probe_data in probes_data.items():
        # Truncate filename if too long
        safe_probe_key = probe_key[:100] if len(probe_key) > 100 else probe_key
        output_file = output_dir / f"{safe_probe_key}.json"
        
        # Sort responses by system and trial for consistency
        probe_data['responses'].sort(key=lambda x: (x['system'], x['trial_type'], x['exchange_number'] or 0))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(probe_data, f, indent=2, ensure_ascii=False)
        
        print(f"Created: {output_file.name} with {len(probe_data['responses'])} responses")
    
    print(f"\n✨ Reorganization complete! Created {len(probes_data)} probe files in {output_dir}")
    
    # Create a summary file
    summary = {
        'total_probes': len(probes_data),
        'probe_list': list(probes_data.keys()),
        'total_responses': sum(len(data['responses']) for data in probes_data.values()),
        'systems_found': list(set(r['system'] for data in probes_data.values() for r in data['responses'])),
        'trial_types_found': list(set(r['trial_type'] for data in probes_data.values() for r in data['responses']))
    }
    
    with open(output_dir / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary: {summary['total_responses']} total responses across {summary['total_probes']} probes")
    print(f"Systems: {', '.join(summary['systems_found'])}")
    print(f"Trial types: {', '.join(summary['trial_types_found'])}")

if __name__ == "__main__":
    reorganize_data()
