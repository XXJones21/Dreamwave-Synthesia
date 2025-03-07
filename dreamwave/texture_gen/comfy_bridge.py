"""
ComfyUI Bridge for Texture Generation

This module provides a bridge between Unreal Engine and ComfyUI
for generating textures using AI models.
"""

import os
import sys
import json
import requests
import websocket
import urllib.parse
import uuid
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

class ComfyBridge:
    """Bridge class for interacting with ComfyUI server."""
    
    def __init__(self, server_address: str = "http://127.0.0.1:8188"):
        """Initialize the ComfyUI bridge.
        
        Args:
            server_address: URL of the ComfyUI server
        """
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.ws = None
        self.workflow_file = None
    
    def _get_api_url(self, endpoint: str) -> str:
        """Build the complete API URL for a given endpoint."""
        return f"{self.server_address}/{endpoint}"
    
    def connect_websocket(self) -> None:
        """Connect to the ComfyUI websocket for real-time updates."""
        ws_url = f"{self.server_address.replace('http', 'ws')}/ws?clientId={self.client_id}"
        self.ws = websocket.create_connection(ws_url)
        print(f"Connected to ComfyUI websocket with client ID: {self.client_id}")
    
    def disconnect_websocket(self) -> None:
        """Disconnect from the ComfyUI websocket."""
        if self.ws:
            self.ws.close()
            self.ws = None
            print("Disconnected from ComfyUI websocket")
    
    def load_workflow(self, workflow_path: str) -> Dict[str, Any]:
        """Load a ComfyUI workflow from a JSON file.
        
        Args:
            workflow_path: Path to the workflow JSON file
            
        Returns:
            Workflow data as a dictionary
        """
        self.workflow_file = workflow_path
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        return workflow
    
    def set_prompt_text(self, workflow: Dict[str, Any], node_id: int, text: str) -> Dict[str, Any]:
        """Set the text in a prompt node of the workflow.
        
        Args:
            workflow: ComfyUI workflow dictionary
            node_id: ID of the prompt node to modify
            text: Text prompt to set
            
        Returns:
            Modified workflow
        """
        for node in workflow["nodes"]:
            if node["id"] == node_id:
                if "inputs" in node and "text" in node["inputs"]:
                    node["inputs"]["text"] = text
                    break
        return workflow
    
    def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """Queue a workflow for processing on the ComfyUI server.
        
        Args:
            workflow: ComfyUI workflow dictionary
            
        Returns:
            Prompt ID assigned by ComfyUI
        """
        p = {"prompt": workflow, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        
        url = self._get_api_url("prompt")
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        return response.json()["prompt_id"]
    
    def wait_for_execution(self, prompt_id: str) -> Dict[str, Any]:
        """Wait for a workflow execution to complete and collect the results.
        
        Args:
            prompt_id: ID of the prompt to wait for
            
        Returns:
            Dictionary containing the execution results
        """
        if not self.ws:
            self.connect_websocket()
        
        while True:
            out = json.loads(self.ws.recv())
            if out["type"] == "executing":
                data = out["data"]
                if data["node"] is None and data["prompt_id"] == prompt_id:
                    break
        
        # Get the outputs
        url = self._get_api_url(f"history/{prompt_id}")
        response = requests.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def download_image(self, filename: str, output_dir: str) -> str:
        """Download a generated image from the ComfyUI server.
        
        Args:
            filename: Name of the file on the server
            output_dir: Local directory to save the image
            
        Returns:
            Path to the downloaded image
        """
        url = self._get_api_url(f"view?filename={urllib.parse.quote(filename)}")
        
        os.makedirs(output_dir, exist_ok=True)
        local_path = os.path.join(output_dir, os.path.basename(filename))
        
        response = requests.get(url)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        return local_path
    
    def generate_texture(
        self, 
        prompt: str, 
        node_id: int = 3,  # Default node ID for text prompt
        output_dir: str = "./output",
        workflow_path: Optional[str] = None
    ) -> str:
        """Generate a texture using the specified prompt.
        
        Args:
            prompt: Text description of the texture
            node_id: ID of the prompt node in the workflow
            output_dir: Directory to save the output
            workflow_path: Path to workflow file (if different from last used)
            
        Returns:
            Path to the generated texture
        """
        try:
            # Load workflow
            if workflow_path or not self.workflow_file:
                workflow = self.load_workflow(workflow_path or self.workflow_file)
            else:
                with open(self.workflow_file, 'r') as f:
                    workflow = json.load(f)
            
            # Set prompt
            workflow = self.set_prompt_text(workflow, node_id, prompt)
            
            # Queue workflow for execution
            prompt_id = self.queue_prompt(workflow)
            print(f"Prompt queued with ID: {prompt_id}")
            
            # Wait for results
            results = self.wait_for_execution(prompt_id)
            
            # Extract image filename
            output_images = []
            for node_id, node_output in results["outputs"].items():
                if "images" in node_output:
                    for img in node_output["images"]:
                        if "filename" in img:
                            output_images.append(img["filename"])
            
            if not output_images:
                raise ValueError("No images were generated")
            
            # Download the first image
            texture_path = self.download_image(output_images[0], output_dir)
            print(f"Generated texture saved to: {texture_path}")
            
            return texture_path
            
        except Exception as e:
            print(f"Error generating texture: {e}")
            raise 