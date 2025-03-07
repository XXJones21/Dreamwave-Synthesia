"""
Dreamwave Texture Generator - ComfyUI Bridge
Implementation for connecting to ComfyUI server.
"""

import unreal
import os
import sys
import json
import uuid
import tempfile
import time

class ComfyBridge:
    """A bridge class for interacting with ComfyUI."""
    
    def __init__(self, server_url="http://127.0.0.1:8188"):
        """Initialize the ComfyBridge."""
        self.server_url = server_url
        unreal.log(f"ComfyBridge initialized with server URL: {server_url}")
        
        # Try to import requests or use a fallback
        try:
            import requests
            self.requests = requests
        except ImportError:
            # Use the fallback implementation from dreamwave_texgen_api
            try:
                from dreamwave_texgen_api import RequestsFallback
                self.requests = RequestsFallback
                unreal.log("Using fallback requests implementation for ComfyBridge")
            except ImportError:
                unreal.log_error("Failed to import requests or fallback implementation")
                
    def prompt_to_image(self, prompt, negative_prompt="", width=1024, height=1024, output_dir=None):
        """Generate an image from a prompt using ComfyUI."""
        try:
            # Create a unique filename
            filename = f"dreamwave_{str(uuid.uuid4())[:8]}.png"
            
            # Use the temp directory if no output directory is specified
            if not output_dir:
                output_dir = tempfile.gettempdir()
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Full path to the output file
            output_path = os.path.join(output_dir, filename)
            
            # Construct a basic workflow for text-to-image using ComfyUI API
            workflow = {
                "prompt": {
                    "1": {
                        "class_type": "KSampler",
                        "inputs": {
                            "seed": 123456789,
                            "steps": 20,
                            "cfg": 7.0,
                            "sampler_name": "euler_a",
                            "scheduler": "normal",
                            "denoise": 1.0,
                            "model": ["3", 0],
                            "positive": ["4", 0],
                            "negative": ["5", 0],
                            "latent_image": ["6", 0]
                        }
                    },
                    "2": {
                        "class_type": "SaveImage",
                        "inputs": {
                            "filename_prefix": "dreamwave",
                            "images": ["7", 0]
                        }
                    },
                    "3": {
                        "class_type": "CheckpointLoaderSimple",
                        "inputs": {
                            "ckpt_name": "v1-5-pruned-emaonly.safetensors"
                        }
                    },
                    "4": {
                        "class_type": "CLIPTextEncode",
                        "inputs": {
                            "text": prompt,
                            "clip": ["3", 1]
                        }
                    },
                    "5": {
                        "class_type": "CLIPTextEncode",
                        "inputs": {
                            "text": negative_prompt,
                            "clip": ["3", 1]
                        }
                    },
                    "6": {
                        "class_type": "EmptyLatentImage",
                        "inputs": {
                            "width": width,
                            "height": height,
                            "batch_size": 1
                        }
                    },
                    "7": {
                        "class_type": "VAEDecode",
                        "inputs": {
                            "samples": ["1", 0],
                            "vae": ["3", 2]
                        }
                    }
                }
            }
            
            # Queue the prompt
            try:
                unreal.log("Sending generation request to ComfyUI...")
                queue_response = self.requests.post(f"{self.server_url}/prompt", json={"prompt": workflow})
                queue_response.raise_for_status()
                prompt_id = queue_response.json().get("prompt_id")
                
                if not prompt_id:
                    unreal.log_error("Failed to get prompt_id from ComfyUI response")
                    return None
                
                # Wait for the result (poll the history endpoint)
                unreal.log(f"Waiting for ComfyUI to process prompt {prompt_id}...")
                max_wait_time = 180  # Maximum wait time in seconds
                start_time = time.time()
                
                while (time.time() - start_time) < max_wait_time:
                    history_response = self.requests.get(f"{self.server_url}/history/{prompt_id}")
                    if history_response.status_code == 200:
                        history = history_response.json()
                        if prompt_id in history and "outputs" in history[prompt_id]:
                            # Get the image filename
                            for node_id, node_output in history[prompt_id]["outputs"].items():
                                if node_id.startswith("2") and "images" in node_output:
                                    for image_data in node_output["images"]:
                                        image_filename = image_data["filename"]
                                        # Download the image
                                        image_url = f"{self.server_url}/view?filename={image_filename}"
                                        image_response = self.requests.get(image_url)
                                        
                                        # Save the image to the output path
                                        with open(output_path, "wb") as f:
                                            f.write(image_response.content)
                                        
                                        unreal.log(f"Generated image saved to: {output_path}")
                                        return output_path
                    
                    # Sleep for a short time before checking again
                    time.sleep(1)
                
                unreal.log_error(f"Timed out waiting for ComfyUI to process prompt {prompt_id}")
                return None
            
            except Exception as e:
                unreal.log_error(f"Error communicating with ComfyUI: {str(e)}")
                return None
                
        except Exception as e:
            unreal.log_error(f"Error in prompt_to_image: {str(e)}")
            return None 