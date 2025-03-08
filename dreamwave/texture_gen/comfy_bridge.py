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
    
    def generate_texture(self, prompt: str, output_dir: Optional[str] = None, workflow_path: Optional[str] = None, negative_prompt: str = "", width: int = 1024, height: int = 1024) -> str:
        """Generate a texture using ComfyUI.
        
        Args:
            prompt: Text description of the texture
            output_dir: Directory to save the output
            workflow_path: Path to a workflow JSON file (optional)
            negative_prompt: Text to avoid in the generation
            width: Width of the image
            height: Height of the image
            
        Returns:
            Path to the generated texture
        """
        try:
            print(f"Generating texture with prompt: {prompt}")
            print(f"Using workflow path: {workflow_path if workflow_path else 'default workflow'}")
            
            # Use the workflow from file if provided, otherwise use default
            if workflow_path and os.path.exists(workflow_path):
                return self.run_workflow_with_prompt(
                    workflow_path=workflow_path,
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    output_dir=output_dir
                )
            else:
                # Use the simpler prompt_to_image method with default workflow
                return self.prompt_to_image(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    output_dir=output_dir
                )
                
        except Exception as e:
            print(f"Error generating texture: {e}")
            raise

    def get_available_models_and_samplers(self):
        """Query the ComfyUI server to get available models and samplers.
        
        Returns:
            Tuple[List[str], List[str], List[str]]: Lists of available model names, sampler names, and scheduler names
        """
        try:
            # Get the object info from the server
            object_info_url = self._get_api_url("object_info")
            response = requests.get(object_info_url, timeout=5)
            if response.status_code != 200:
                print(f"Error getting object info: {response.status_code}")
                return [], [], []
                
            data = response.json()
            
            # Extract available models (checkpoint names)
            models = []
            if "CheckpointLoaderSimple" in data:
                checkpoint_info = data["CheckpointLoaderSimple"]
                if "input" in checkpoint_info and "required" in checkpoint_info["input"]:
                    if "ckpt_name" in checkpoint_info["input"]["required"]:
                        models = checkpoint_info["input"]["required"]["ckpt_name"][0]
            
            # Extract available samplers
            samplers = []
            schedulers = []
            if "KSampler" in data:
                sampler_info = data["KSampler"]
                if "input" in sampler_info and "required" in sampler_info["input"]:
                    if "sampler_name" in sampler_info["input"]["required"]:
                        samplers = sampler_info["input"]["required"]["sampler_name"][0]
                    if "scheduler" in sampler_info["input"]["required"]:
                        schedulers = sampler_info["input"]["required"]["scheduler"][0]
            
            print(f"Available models: {models[:5]}...")
            print(f"Available samplers: {samplers[:5]}...")
            print(f"Available schedulers: {schedulers[:5]}...")
            return models, samplers, schedulers
        except Exception as e:
            print(f"Error getting available models and samplers: {e}")
            return [], [], []

    def prompt_to_image(
        self, 
        prompt: str, 
        negative_prompt: str = "",
        width: int = 1024, 
        height: int = 1024,
        output_dir: Optional[str] = None
    ) -> str:
        """Generate an image from a prompt using a standard workflow.
        
        This method is compatible with the SimpleBridge interface used in the UE5 plugin.
        
        Args:
            prompt: Text description of the texture
            negative_prompt: Text to avoid in the generation
            width: Width of the image
            height: Height of the image
            output_dir: Directory to save the output (uses temp dir if not specified)
            
        Returns:
            Path to the generated image
        """
        import random
        import tempfile
        
        # Use temp dir if output_dir is not specified
        if not output_dir:
            output_dir = tempfile.gettempdir()
            
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a unique filename
        filename = f"dreamwave_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(output_dir, filename)
        
        # Get available models and samplers from the server
        available_models, available_samplers, available_schedulers = self.get_available_models_and_samplers()
        
        # Use the first available model, or fallback to a default
        model_name = "model.ckpt"  # Default fallback
        if available_models:
            model_name = available_models[0]
            print(f"Using model: {model_name}")
        else:
            print("Warning: No models found, using default name which may not work")
            
        # Use the first available sampler, or fallback to a default
        sampler_name = "euler"  # Default fallback
        if available_samplers:
            sampler_name = available_samplers[0]
            print(f"Using sampler: {sampler_name}")
        else:
            print("Warning: No samplers found, using default name which may not work")
            
        # Use the first available scheduler, or fallback to a default
        scheduler_name = "normal"  # Default fallback
        if available_schedulers:
            scheduler_name = available_schedulers[0]
            print(f"Using scheduler: {scheduler_name}")
        else:
            print("Warning: No schedulers found, using default name which may not work")
        
        # Create a standard workflow format compatible with ComfyUI
        workflow = {
            "3": {
                "inputs": {
                    "ckpt_name": model_name
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "4": {
                "inputs": {
                    "text": prompt,
                    "clip": ["3", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "5": {
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["3", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "6": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "7": {
                "inputs": {
                    "seed": random.randint(1, 999999999),
                    "steps": 20,
                    "cfg": 7.0,
                    "sampler_name": sampler_name,
                    "scheduler": scheduler_name,
                    "denoise": 1.0,
                    "model": ["3", 0],
                    "positive": ["4", 0],
                    "negative": ["5", 0],
                    "latent_image": ["6", 0]
                },
                "class_type": "KSampler"
            },
            "8": {
                "inputs": {
                    "samples": ["7", 0],
                    "vae": ["3", 2]
                },
                "class_type": "VAEDecode"
            },
            "9": {
                "inputs": {
                    "filename_prefix": "dreamwave",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage"
            }
        }
        
        try:
            # Queue workflow for execution
            prompt_id = self.queue_prompt(workflow)
            print(f"Prompt queued with ID: {prompt_id}")
            
            # Wait for results
            results = self.wait_for_execution(prompt_id)
            
            # Extract image filename
            output_images = []
            for node_id, node_output in results.get("outputs", {}).items():
                if "images" in node_output:
                    for img in node_output["images"]:
                        if "filename" in img:
                            output_images.append(img["filename"])
            
            if not output_images:
                raise ValueError("No images were generated")
            
            # Download the first image
            downloaded_path = self.download_image(output_images[0], output_dir)
            
            # Rename to our desired output path if necessary
            if os.path.abspath(downloaded_path) != os.path.abspath(output_path):
                import shutil
                shutil.copy(downloaded_path, output_path)
                try:
                    os.remove(downloaded_path)  # Clean up the original file
                except:
                    pass  # Ignore errors during cleanup
            
            print(f"Generated image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error in prompt_to_image: {e}")
            import traceback
            traceback.print_exc()
            return None

    def run_workflow_with_prompt(
        self, 
        workflow_path: str, 
        prompt: str, 
        negative_prompt: str = "",
        width: int = 1024, 
        height: int = 1024,
        output_dir: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """Run a workflow from a file with the specified prompt.
        
        Args:
            workflow_path: Path to the workflow JSON file
            prompt: Text description of the texture
            negative_prompt: Text to avoid in the generation
            width: Width of the image
            height: Height of the image  
            output_dir: Directory to save output
            output_path: Specific file path for the output
            
        Returns:
            Path to the generated image
        """
        if not os.path.exists(workflow_path):
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
            
        try:
            # Load workflow from file
            with open(workflow_path, 'r') as f:
                workflow = json.load(f)
                
            # Find text nodes in the workflow
            text_nodes = {}
            empty_latent_nodes = {}
            
            for node_id, node in workflow.items():
                if node.get("class_type") == "CLIPTextEncode":
                    # This is a text encoding node
                    if "inputs" in node and "text" in node["inputs"]:
                        # Check if this appears to be a positive or negative prompt
                        current_text = node["inputs"]["text"]
                        if current_text == "" or "positive" in current_text.lower():
                            text_nodes["positive"] = node_id
                        elif "negative" in current_text.lower():
                            text_nodes["negative"] = node_id
                        else:
                            # If we can't determine, assume it's positive
                            if "positive" not in text_nodes:
                                text_nodes["positive"] = node_id
                
                # Find latent image node to update width/height
                if node.get("class_type") == "EmptyLatentImage":
                    if "inputs" in node and "width" in node["inputs"] and "height" in node["inputs"]:
                        empty_latent_nodes[node_id] = node
            
            # Update the prompt nodes
            if "positive" in text_nodes:
                workflow[text_nodes["positive"]]["inputs"]["text"] = prompt
                print(f"Updated positive prompt node {text_nodes['positive']} with text: {prompt}")
                
            if "negative" in text_nodes and negative_prompt:
                workflow[text_nodes["negative"]]["inputs"]["text"] = negative_prompt
                print(f"Updated negative prompt node {text_nodes['negative']} with text: {negative_prompt}")
                
            # Update width and height in empty latent nodes
            for node_id, node in empty_latent_nodes.items():
                node["inputs"]["width"] = width
                node["inputs"]["height"] = height
                print(f"Updated node {node_id} dimensions to {width}x{height}")
            
            # Process the workflow
            print(f"Queuing workflow from file: {workflow_path}")
            prompt_id = self.queue_prompt(workflow)
            print(f"Workflow queued with prompt ID: {prompt_id}")
            
            # Wait for results
            results = self.wait_for_execution(prompt_id)
            
            # Extract image filename 
            output_images = []
            for node_id, node_output in results.get("outputs", {}).items():
                if "images" in node_output:
                    for img in node_output["images"]:
                        if "filename" in img:
                            output_images.append(img["filename"])
            
            if not output_images:
                raise ValueError("No images were generated")
            
            # Use the provided output path or generate one
            if not output_dir and not output_path:
                import tempfile
                output_dir = tempfile.gettempdir()
                
            if not output_path:
                filename = f"dreamwave_{uuid.uuid4().hex[:8]}.png"
                output_path = os.path.join(output_dir, filename)
            
            # Download the first image
            downloaded_path = self.download_image(output_images[0], os.path.dirname(output_path))
            
            # Rename to our desired output path if necessary
            if os.path.abspath(downloaded_path) != os.path.abspath(output_path):
                import shutil
                shutil.copy(downloaded_path, output_path)
                try:
                    os.remove(downloaded_path)  # Clean up the original file
                except:
                    pass  # Ignore errors during cleanup
            
            print(f"Generated image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error in run_workflow_with_prompt: {e}")
            import traceback
            traceback.print_exc()
            raise 