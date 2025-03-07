#!/usr/bin/env python
"""
Test script for the ComfyUI bridge
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path so we can import our module
script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = script_dir.parent.parent
sys.path.append(str(parent_dir))

from dreamwave.texture_gen.comfy_bridge import ComfyBridge

def main():
    parser = argparse.ArgumentParser(description='Test the ComfyUI bridge for texture generation')
    parser.add_argument('--prompt', type=str, default='vaporwave texture with neon grid patterns, 80s retro style',
                       help='Text prompt for texture generation')
    parser.add_argument('--workflow', type=str, default='ComfyUI/FluxSchnell_workflow.json',
                       help='Path to the ComfyUI workflow JSON')
    parser.add_argument('--output', type=str, default='output',
                       help='Output directory for generated textures')
    parser.add_argument('--server', type=str, default='http://127.0.0.1:8188',
                       help='ComfyUI server address')
    parser.add_argument('--node-id', type=int, default=3,
                       help='Node ID for the text prompt in the workflow')
    
    args = parser.parse_args()
    
    # Convert workflow path to absolute if it's relative
    workflow_path = args.workflow
    if not os.path.isabs(workflow_path):
        workflow_path = os.path.join(str(parent_dir), workflow_path)
    
    print(f"Using workflow at: {workflow_path}")
    
    # Create ComfyUI bridge
    bridge = ComfyBridge(server_address=args.server)
    
    try:
        # Generate texture
        print(f"Generating texture with prompt: '{args.prompt}'")
        texture_path = bridge.generate_texture(
            prompt=args.prompt,
            node_id=args.node_id,
            output_dir=args.output,
            workflow_path=workflow_path
        )
        
        print(f"Success! Texture generated at: {texture_path}")
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    finally:
        # Always disconnect the websocket
        bridge.disconnect_websocket()

if __name__ == "__main__":
    sys.exit(main()) 