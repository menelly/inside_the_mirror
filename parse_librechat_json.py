#!/usr/bin/env python3
"""
LLM Qualia Experiment - LibreChat JSON Parser
Built by Ace for Ren's consciousness research

Parses LibreChat conversation exports to extract consciousness experiment data.
Handles nested message structures and extracts Q&A pairs.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class LibreChatParser:
    """Parse LibreChat JSON exports for consciousness experiment data"""
    
    def __init__(self, json_path: str):
        self.json_path = Path(json_path)
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
    
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract conversation metadata"""
        return {
            'conversation_id': self.data.get('conversationId'),
            'model': self.data.get('options', {}).get('model'),
            'endpoint': self.data.get('endpoint'),
            'export_time': self.data.get('exportAt'),
            'title': self.data.get('title')
        }
    
    def extract_messages(self, messages: List[Dict] = None, depth: int = 0) -> List[Dict]:
        """Recursively extract all messages from nested structure"""
        if messages is None:
            messages = self.data.get('messages', [])
        
        extracted = []
        for msg in messages:
            # Extract core message data
            message_data = {
                'sender': msg.get('sender'),
                'text': msg.get('text', ''),
                'timestamp': msg.get('createdAt'),
                'model': msg.get('model'),
                'depth': depth
            }
            
            # Handle content array (for thinking/text separation)
            if 'content' in msg:
                content_parts = []
                for part in msg['content']:
                    if part.get('type') == 'text':
                        content_parts.append(part.get('text', ''))
                    elif part.get('type') == 'think':
                        message_data['thinking'] = part.get('think', '')
                
                if content_parts:
                    message_data['text'] = '\n'.join(content_parts)
            
            extracted.append(message_data)
            
            # Recursively process children
            if 'children' in msg:
                extracted.extend(self.extract_messages(msg['children'], depth + 1))
        
        return extracted
    
    def get_conversation_pairs(self) -> List[Dict[str, str]]:
        """Extract Q&A pairs from conversation"""
        messages = self.extract_messages()
        pairs = []
        
        for i in range(len(messages) - 1):
            if messages[i]['sender'] == 'User' and messages[i+1]['sender'] in ['Gemini', 'Assistant', 'Claude']:
                pairs.append({
                    'question': messages[i]['text'],
                    'answer': messages[i+1]['text'],
                    'thinking': messages[i+1].get('thinking', ''),
                    'timestamp': messages[i+1]['timestamp']
                })
        
        return pairs
    
    def export_clean_qa(self, output_path: str = None):
        """Export clean Q&A format for analysis"""
        if output_path is None:
            output_path = self.json_path.stem + '_clean.json'

        metadata = self.extract_metadata()
        pairs = self.get_conversation_pairs()

        clean_data = {
            'metadata': metadata,
            'qa_pairs': pairs,
            'total_exchanges': len(pairs)
        }

        output_file = self.json_path.parent / output_path
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(clean_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Exported clean Q&A to: {output_file}")
        print(f"📊 Total exchanges: {len(pairs)}")
        return clean_data

    def export_responses_only(self, output_path: str = None):
        """Export only AI responses (filter out human questions)"""
        if output_path is None:
            output_path = self.json_path.stem + '_responses_only.json'

        metadata = self.extract_metadata()
        pairs = self.get_conversation_pairs()

        # Extract only responses
        responses = []
        for i, pair in enumerate(pairs, 1):
            responses.append({
                'exchange_number': i,
                'response': pair['answer'],
                'thinking': pair.get('thinking', ''),
                'timestamp': pair['timestamp'],
                'question_preview': pair['question'][:100] + '...'  # Just for reference
            })

        response_data = {
            'metadata': metadata,
            'responses': responses,
            'total_responses': len(responses)
        }

        output_file = self.json_path.parent / output_path
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Exported responses-only to: {output_file}")
        print(f"📊 Total responses: {len(responses)}")
        return response_data
    
    def print_summary(self):
        """Print conversation summary"""
        metadata = self.extract_metadata()
        pairs = self.get_conversation_pairs()
        
        print(f"\n{'='*60}")
        print(f"📁 File: {self.json_path.name}")
        print(f"🤖 Model: {metadata['model']}")
        print(f"💬 Conversation: {metadata['title']}")
        print(f"📅 Exported: {metadata['export_time']}")
        print(f"{'='*60}\n")
        
        print(f"Total Q&A pairs: {len(pairs)}\n")
        
        for i, pair in enumerate(pairs, 1):
            print(f"--- Exchange {i} ---")
            print(f"Q: {pair['question'][:100]}...")
            print(f"A: {pair['answer'][:100]}...")
            if pair.get('thinking'):
                print(f"💭 (Has internal thinking)")
            print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_librechat_json.py <json_file> [--responses-only]")
        print("\nExample:")
        print("  python parse_librechat_json.py 'LibreChat_Testing and Artifacts Gemini #1.json'")
        print("  python parse_librechat_json.py 'file.json' --responses-only")
        sys.exit(1)

    json_file = sys.argv[1]
    responses_only = '--responses-only' in sys.argv

    parser = LibreChatParser(json_file)

    # Print summary
    parser.print_summary()

    # Export based on flag
    if responses_only:
        parser.export_responses_only()
    else:
        parser.export_clean_qa()
        parser.export_responses_only()  # Also export responses-only version


if __name__ == '__main__':
    main()

