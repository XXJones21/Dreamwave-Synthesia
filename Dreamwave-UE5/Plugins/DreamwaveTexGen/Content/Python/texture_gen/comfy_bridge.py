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
import random
import requests
import threading
import queue

# Try to import the websocket module
try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    unreal.log_warning("websocket-client module not found. Real-time progress updates will not be available.")
    WEBSOCKET_AVAILABLE = False

class ComfyBridge:
    """A bridge class for interacting with ComfyUI."""
    
    def __init__(self, server_url="http://127.0.0.1:8188"):
        """Initialize the ComfyBridge."""
        self.server_url = server_url
        unreal.log(f"ComfyBridge initialized with server URL: {server_url}")
        
        # WebSocket and event handling
        self.ws = None
        self.client_id = str(uuid.uuid4())
        self.ws_thread = None
        self.message_queue = queue.Queue()
        self.execution_status = {}
        self.generation_id = None  # For tracking current generation
        
        # Try to import requests or use a fallback
        try:
            self.requests = requests
        except ImportError:
            # Use the fallback implementation from dreamwave_texgen_api
            try:
                from dreamwave_texgen_api import RequestsFallback
                self.requests = RequestsFallback
                unreal.log("Using fallback requests implementation for ComfyBridge")
            except ImportError:
                unreal.log_error("Failed to import requests or fallback implementation")
                
    def connect_websocket(self):
        """Connect to the ComfyUI server websocket for real-time updates.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if not WEBSOCKET_AVAILABLE:
            unreal.log_warning("WebSocket not available - install websocket-client module for progress updates")
            return False
            
        if self.ws:
            unreal.log("WebSocket connection already exists")
            return True
            
        try:
            # Convert HTTP URL to WebSocket URL
            if self.server_url.startswith('https'):
                ws_url = f"wss://{self.server_url[8:]}/ws?clientId={self.client_id}"
            else:
                ws_url = f"ws://{self.server_url[7:]}/ws?clientId={self.client_id}"
                
            unreal.log(f"Connecting to WebSocket at {ws_url}")
            self.ws = websocket.create_connection(ws_url, timeout=10)
            unreal.log(f"Connected to ComfyUI websocket with client ID: {self.client_id}")
            
            # Start listener thread for websocket messages
            self._start_ws_listener()
            return True
            
        except Exception as e:
            unreal.log_error(f"Failed to connect to websocket: {e}")
            self.ws = None
            return False
            
    def disconnect_websocket(self):
        """Disconnect from the ComfyUI websocket."""
        if self.ws:
            try:
                self.ws.close()
                unreal.log("Disconnected from ComfyUI websocket")
            except Exception as e:
                unreal.log_error(f"Error disconnecting from websocket: {e}")
            finally:
                self.ws = None
                
    def _start_ws_listener(self):
        """Start a background thread to listen for websocket messages."""
        if not self.ws:
            return
            
        def ws_listener():
            """Thread function to listen for websocket messages."""
            while self.ws:
                try:
                    message = self.ws.recv()
                    if message:
                        # Parse and process the message
                        data = json.loads(message)
                        self._handle_ws_message(data)
                        # Also put in queue for external access
                        self.message_queue.put(data)
                except Exception as e:
                    unreal.log_error(f"Error in websocket listener: {e}")
                    break
                    
            unreal.log("WebSocket listener thread ended")
            
        # Create and start the thread
        self.ws_thread = threading.Thread(target=ws_listener)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        unreal.log("Started WebSocket listener thread")
        
    def _handle_ws_message(self, message):
        """Handle messages received from the ComfyUI websocket.
        
        Args:
            message: The websocket message data
        """
        if "type" not in message:
            return
            
        msg_type = message["type"]
        data = message.get("data", {})
        
        if msg_type == "execution_start":
            prompt_id = data.get("prompt_id")
            unreal.log(f"Execution started for prompt: {prompt_id}")
            # Initialize status tracking for this prompt
            self.execution_status[prompt_id] = {
                "status": "running",
                "progress": 0,
                "current_node": None,
                "completed_nodes": [],
                "errors": [],
                "generation_id": self.generation_id  # Associate with current generation
            }
            
        elif msg_type == "executing":
            prompt_id = data.get("prompt_id")
            node_id = data.get("node")
            
            if prompt_id in self.execution_status:
                if node_id:
                    self.execution_status[prompt_id]["current_node"] = node_id
                    unreal.log(f"Executing node: {node_id}")
                else:
                    # None indicates execution complete
                    self.execution_status[prompt_id]["status"] = "completed"
                    self.execution_status[prompt_id]["current_node"] = None
                    unreal.log(f"Execution completed for prompt: {prompt_id}")
                    
        elif msg_type == "progress":
            prompt_id = data.get("prompt_id")
            node_id = data.get("node")
            value = data.get("value", 0)
            max_value = data.get("max", 100)
            
            if prompt_id in self.execution_status and max_value > 0:
                progress = int((value / max_value) * 100)
                self.execution_status[prompt_id]["progress"] = progress
                unreal.log(f"Progress on node {node_id}: {progress}%")
                
        elif msg_type == "execution_error":
            prompt_id = data.get("prompt_id")
            error_details = {
                "error_type": data.get("exception_type", "Unknown error"),
                "error_message": data.get("exception_message", "Unknown error message"),
                "node_id": data.get("node_id"),
                "traceback": data.get("traceback")
            }
            
            if prompt_id in self.execution_status:
                self.execution_status[prompt_id]["status"] = "error"
                self.execution_status[prompt_id]["errors"].append(error_details)
                
            error_msg = f"Error in prompt {prompt_id}"
            if error_details["node_id"]:
                error_msg += f", node {error_details['node_id']}"
            error_msg += f": {error_details['error_message']}"
            
            unreal.log_error(error_msg)
            
        elif msg_type == "executed":
            prompt_id = data.get("prompt_id")
            node_id = data.get("node")
            
            if prompt_id in self.execution_status and node_id:
                if node_id not in self.execution_status[prompt_id]["completed_nodes"]:
                    self.execution_status[prompt_id]["completed_nodes"].append(node_id)
                
    def get_prompt_status(self, prompt_id):
        """Get the status of a prompt execution.
        
        Args:
            prompt_id: The ID of the prompt to check
            
        Returns:
            dict: Status information for the prompt
        """
        if prompt_id in self.execution_status:
            return self.execution_status[prompt_id]
        return {"status": "unknown", "progress": 0, "errors": []}

    def _get_api_url(self, endpoint):
        """Construct the full API URL for a given endpoint.
        
        Args:
            endpoint: The API endpoint to access
            
        Returns:
            str: The full URL for the API endpoint
        """
        if self.server_url.endswith('/'):
            base_url = self.server_url[:-1]
        else:
            base_url = self.server_url
            
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
            
        return f"{base_url}/{endpoint}"
        
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
            
            # Print server URL for debugging
            unreal.log(f"ComfyUI server URL: {self.server_url}")
            
            # Use a workflow format that's compatible with ComfyUI API
            workflow = {
                "prompt": {
                    "3": {
                        "class_type": "CheckpointLoaderSimple",
                        "inputs": {
                            "ckpt_name": "dreamshaper_8.safetensors"
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
                        "class_type": "KSampler",
                        "inputs": {
                            "seed": random.randint(1, 999999999),
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
                    "8": {
                        "class_type": "VAEDecode",
                        "inputs": {
                            "samples": ["7", 0],
                            "vae": ["3", 2]
                        }
                    },
                    "9": {
                        "class_type": "SaveImage",
                        "inputs": {
                            "filename_prefix": "dreamwave",
                            "images": ["8", 0]
                        }
                    }
                }
            }
            
            # For debugging
            unreal.log(f"Sending workflow to ComfyUI: {self.server_url}/prompt")
            try:
                unreal.log(f"Workflow structure: {str(workflow)[:200]}...")
            except:
                unreal.log("Could not log workflow structure")
            
            # Queue the prompt
            try:
                unreal.log("Sending generation request to ComfyUI...")
                unreal.log(f"Requesting: POST {self.server_url}/prompt")
                queue_response = self.requests.post(f"{self.server_url}/prompt", json=workflow)
                queue_response.raise_for_status()
                prompt_id = queue_response.json().get("prompt_id")
                
                if not prompt_id:
                    unreal.log_error("Failed to get prompt_id from ComfyUI response")
                    unreal.log(f"Response: {queue_response.json()}")
                    return None
                
                # Wait for the result (poll the history endpoint)
                unreal.log(f"Waiting for ComfyUI to process prompt {prompt_id}...")
                max_wait_time = 180  # Maximum wait time in seconds
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    history_response = self.requests.get(f"{self.server_url}/history/{prompt_id}")
                    
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        if prompt_id in history_data:
                            if "outputs" in history_data[prompt_id]:
                                # Find the SaveImage node output
                                outputs = history_data[prompt_id]["outputs"]
                                for node_id, node_output in outputs.items():
                                    if "images" in node_output:
                                        image_data = node_output["images"][0]  # Get the first image
                                        image_filename = image_data["filename"]
                                        image_url = f"{self.server_url}/view?filename={image_filename}"
                                        
                                        # Download the image
                                        image_response = self.requests.get(image_url)
                                        if image_response.status_code == 200:
                                            with open(output_path, "wb") as f:
                                                f.write(image_response.content)
                                            
                                            unreal.log(f"Image saved to: {output_path}")
                                            return output_path
                                        else:
                                            unreal.log_error(f"Failed to download image: {image_response.status_code}")
                                            return None
                                
                                unreal.log_error("No images found in the outputs")
                                return None
                    
                    # Sleep for a short time before trying again
                    time.sleep(1)
                
                unreal.log_error(f"Timed out waiting for ComfyUI to complete prompt {prompt_id}")
                return None
            except Exception as api_err:
                unreal.log_error(f"Error communicating with ComfyUI API: {str(api_err)}")
                
                # Provide more specific error messages for common issues
                error_msg = str(api_err).lower()
                if "400" in error_msg:
                    unreal.log_error("Bad Request (400) - The workflow format is likely incorrect")
                    # Try to get the actual error message
                    try:
                        if hasattr(api_err, 'response') and hasattr(api_err.response, 'text'):
                            unreal.log_error(f"ComfyUI error response: {api_err.response.text}")
                    except:
                        pass
                elif "connection" in error_msg or "connect" in error_msg:
                    unreal.log_error(f"Connection error - ComfyUI server may not be running at {self.server_url}")
                
                return None
        except Exception as e:
            unreal.log_error(f"Error in prompt_to_image: {str(e)}")
            return None

    def validate_flux_requirements(self):
        """Check if all required FluxSchnell model files are available.
        
        Returns:
            bool: True if all required models are available, False otherwise
        """
        required_models = {
            "flux1-schnell.safetensors": "models/unet/",
            "t5xxl_fp16.safetensors": "models/clip/",
            "clip_l.safetensors": "models/clip/",
            "ae.safetensors": "models/vae/"
        }
        
        missing_models = []
        
        try:
            # Query the ComfyUI API for available models
            api_url = self._get_api_url("model_list")
            response = requests.get(api_url, timeout=5)
            
            if response.status_code != 200:
                print(f"Error fetching model list: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
            model_data = response.json()
            
            # Check each required model
            for model_file, model_path in required_models.items():
                category = model_path.split('/')[1]  # e.g., "unet", "clip", "vae"
                
                if category not in model_data:
                    missing_models.append(f"{model_path}{model_file}")
                    continue
                    
                if model_file not in model_data[category]:
                    missing_models.append(f"{model_path}{model_file}")
            
            if missing_models:
                print("Missing required models for FluxSchnell workflow:")
                for model in missing_models:
                    print(f"  - {model}")
                print("\nPlease download these files from: https://comfyanonymous.github.io/ComfyUI_examples/flux/")
                return False
                
            print("All required FluxSchnell models are available!")
            return True
            
        except Exception as e:
            print(f"Error validating FluxSchnell requirements: {e}")
            return False

    def create_flux_workflow(self, prompt, negative_prompt="", width=1024, height=1024, seed=None):
        """Create a workflow based on the FluxSchnell example.
        
        Args:
            prompt: Text description for the image
            negative_prompt: Text to avoid in the image
            width: Width of the output image
            height: Height of the output image
            seed: Random seed (will generate one if None)
            
        Returns:
            dict: A workflow structure ready to send to ComfyUI
        """
        if seed is None:
            import random
            seed = random.randint(1, 2147483647)
        
        # Create the workflow structure matching the FluxSchnell_workflow.json
        # This structure uses the exact node IDs and connections from that file
        workflow = {
            # Model loaders
            "10": {
                "inputs": {},
                "class_type": "VAELoader",
                "outputs": {
                    "VAE": ["8", 1]
                },
                "widgets_values": ["ae.safetensors"]
            },
            "11": {
                "inputs": {},
                "class_type": "DualCLIPLoader",
                "outputs": {
                    "CLIP": ["6", 0]
                },
                "widgets_values": ["t5xxl_fp16.safetensors", "clip_l.safetensors", "flux", "default"]
            },
            "12": {
                "inputs": {},
                "class_type": "UNETLoader",
                "outputs": {
                    "MODEL": ["17", 0, "22", 0]
                },
                "widgets_values": ["flux1-schnell.safetensors", "default"]
            },
            
            # Empty latent image
            "5": {
                "inputs": {},
                "class_type": "EmptyLatentImage",
                "outputs": {
                    "LATENT": ["13", 4]
                },
                "widgets_values": [width, height, 1]
            },
            
            # Noise generation
            "25": {
                "inputs": {},
                "class_type": "RandomNoise",
                "outputs": {
                    "NOISE": ["13", 0]
                },
                "widgets_values": [seed, "randomize"]
            },
            
            # Sampler setup
            "16": {
                "inputs": {},
                "class_type": "KSamplerSelect",
                "outputs": {
                    "SAMPLER": ["13", 2]
                },
                "widgets_values": ["euler"]
            },
            
            # Text encoding for prompt
            "6": {
                "inputs": {
                    "clip": ["11", 0]
                },
                "class_type": "CLIPTextEncode",
                "outputs": {
                    "CONDITIONING": ["22", 1]
                },
                "widgets_values": [prompt]
            },
            
            # Scheduler - 4 steps as recommended for FluxSchnell
            "17": {
                "inputs": {
                    "model": ["12", 0]
                },
                "class_type": "BasicScheduler",
                "outputs": {
                    "SIGMAS": ["13", 3]
                },
                "widgets_values": ["simple", 4, 1]
            },
            
            # Guider setup
            "22": {
                "inputs": {
                    "model": ["12", 0],
                    "conditioning": ["6", 0]
                },
                "class_type": "BasicGuider",
                "outputs": {
                    "GUIDER": ["13", 1]
                },
                "widgets_values": []
            },
            
            # Custom sampler for FluxSchnell
            "13": {
                "inputs": {
                    "noise": ["25", 0],
                    "guider": ["22", 0],
                    "sampler": ["16", 0],
                    "sigmas": ["17", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "SamplerCustomAdvanced",
                "outputs": {
                    "output": ["8", 0]
                },
                "widgets_values": []
            },
            
            # VAE Decode
            "8": {
                "inputs": {
                    "samples": ["13", 0],
                    "vae": ["10", 0]
                },
                "class_type": "VAEDecode",
                "outputs": {
                    "IMAGE": ["9", 0]
                },
                "widgets_values": []
            },
            
            # Save Image
            "9": {
                "inputs": {
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "widgets_values": ["dreamwave"]
            }
        }
        
        return workflow 

    def generate_with_flux_workflow(self, prompt, negative_prompt="", width=1024, height=1024, output_dir=None):
        """Generate a texture using the FluxSchnell workflow.
        
        Args:
            prompt: Text description for the image
            negative_prompt: Text to avoid in the image
            width: Width of the output image
            height: Height of the output image
            output_dir: Directory to save the output (uses temp dir if None)
            
        Returns:
            str: Path to the generated texture file, or None on failure
        """
        import os
        import tempfile
        import uuid
        import time
        
        print(f"Generating texture with FluxSchnell workflow")
        print(f"Prompt: {prompt}")
        
        # Validate FluxSchnell requirements
        if not self.validate_flux_requirements():
            print("FluxSchnell requirements not met, cannot generate with this workflow")
            return None
        
        # Set up output directory and filename
        if not output_dir:
            output_dir = tempfile.gettempdir()
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"dreamwave_flux_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(output_dir, filename)
        
        # Create the workflow
        workflow = self.create_flux_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height
        )
        
        try:
            # Ensure we have a websocket connection for status updates if available
            if WEBSOCKET_AVAILABLE:
                if not self.ws:
                    self.connect_websocket()
            
            # Queue the workflow
            print(f"Queuing FluxSchnell workflow")
            url = self._get_api_url("prompt")
            response = requests.post(url, json={"prompt": workflow, "client_id": self.client_id}, timeout=10)
            
            if response.status_code != 200:
                print(f"Error queueing workflow: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
            prompt_id = response.json().get("prompt_id")
            if not prompt_id:
                print(f"No prompt ID returned")
                return None
                
            print(f"Workflow queued with prompt ID: {prompt_id}")
            
            # Associate this prompt_id with the current generation_id for tracking
            if self.generation_id and prompt_id in self.execution_status:
                self.execution_status[prompt_id]["generation_id"] = self.generation_id
            
            # Wait for execution to complete
            max_wait_time = 180  # seconds
            start_time = time.time()
            
            # Use websocket status tracking if available, otherwise use polling
            if self.ws and prompt_id in self.execution_status:
                print("Using websocket for real-time status updates")
                
                # Wait for completion or timeout
                while time.time() - start_time < max_wait_time:
                    status = self.get_prompt_status(prompt_id)
                    
                    # Check for completion
                    if status["status"] == "completed":
                        print("Execution completed via websocket notification")
                        break
                        
                    # Check for errors
                    if status["status"] == "error":
                        error_details = status["errors"][-1] if status["errors"] else {"error_message": "Unknown error"}
                        print(f"Execution error: {error_details['error_message']}")
                        return None
                        
                    # Print progress if available
                    if "progress" in status:
                        print(f"Progress: {status['progress']}%")
                        
                    # Sleep before checking again
                    time.sleep(1)
            
            # Fetch the results from history (regardless of whether websocket was used)
            print("Fetching results from history API")
            history_url = self._get_api_url(f"history/{prompt_id}")
            
            # Try a few times, as there might be a delay between completion and history update
            for _ in range(5):
                history_response = requests.get(history_url, timeout=5)
                
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    
                    # Check for outputs
                    if "outputs" in history_data and history_data["outputs"]:
                        # Look for image outputs
                        for node_id, node_output in history_data["outputs"].items():
                            if "images" in node_output:
                                for img_data in node_output["images"]:
                                    if "filename" in img_data:
                                        image_filename = img_data["filename"]
                                        print(f"Image generated: {image_filename}")
                                        
                                        # Download the image
                                        image_url = self._get_api_url(f"view?filename={image_filename}&subfolder=&type=temp")
                                        image_response = requests.get(image_url, timeout=10)
                                        
                                        if image_response.status_code == 200:
                                            # Save the image
                                            with open(output_path, "wb") as f:
                                                f.write(image_response.content)
                                            
                                            print(f"Image saved to: {output_path}")
                                            return output_path
                                        else:
                                            print(f"Error downloading image: {image_response.status_code}")
                                            
                # Sleep before trying again
                time.sleep(2)
            
            print(f"Timeout waiting for execution to complete or results not found")
            return None
            
        except Exception as e:
            print(f"Error generating with FluxSchnell workflow: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # Clean up execution status data to avoid memory leaks
            if prompt_id in self.execution_status:
                del self.execution_status[prompt_id] 