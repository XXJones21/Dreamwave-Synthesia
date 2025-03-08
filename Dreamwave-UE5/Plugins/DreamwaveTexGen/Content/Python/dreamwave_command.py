"""
Dreamwave Command - A simple direct Python command to launch Dreamwave
"""

import unreal
import os
import sys

def run_dreamwave():
    """Run the Dreamwave Texture Generator UI."""
    try:
        unreal.log("Launching Dreamwave Texture Generator...")
        
        # Add plugin directory to path if needed
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        if plugin_dir not in sys.path:
            sys.path.append(plugin_dir)
            
        # Import the required modules
        import dreamwave_texgen_api
        import dreamwave_texgen_ui
        
        # Create API and run UI
        api = dreamwave_texgen_api.DreamwaveTexGenAPI()
        dreamwave_texgen_ui.show_ui(api)
        
        return True
    except Exception as e:
        unreal.log_error(f"Failed to launch Dreamwave: {str(e)}")
        try:
            unreal.EditorDialog.show_message(
                title="Dreamwave Error",
                message=f"Failed to launch Dreamwave: {str(e)}",
                message_type=unreal.AppMsgType.OK
            )
        except:
            unreal.log_error(f"Failed to show error dialog: {str(e)}")
        
        return False

def check_comfyui():
    """Check the status of the ComfyUI server."""
    try:
        unreal.log("Checking ComfyUI server status...")
        
        # Add plugin directory to path if needed
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        if plugin_dir not in sys.path:
            sys.path.append(plugin_dir)
            
        # Import and check the server
        import dreamwave_texgen_ui
        dreamwave_texgen_ui.check_comfyui_status()
        
        return True
    except Exception as e:
        unreal.log_error(f"Failed to check ComfyUI server status: {str(e)}")
        return False

def launch_comfyui():
    """Launch the ComfyUI server."""
    try:
        unreal.log("Launching ComfyUI server...")
        
        # Add plugin directory to path if needed
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        if plugin_dir not in sys.path:
            sys.path.append(plugin_dir)
            
        # Import and launch the server
        import dreamwave_texgen_ui
        dreamwave_texgen_ui.launch_comfyui_server()
        
        return True
    except Exception as e:
        unreal.log_error(f"Failed to launch ComfyUI server: {str(e)}")
        return False

def shutdown_comfyui():
    """Shut down the ComfyUI server if it's running."""
    try:
        unreal.log("Shutting down ComfyUI server...")
        
        # Add plugin directory to path if needed
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        if plugin_dir not in sys.path:
            sys.path.append(plugin_dir)
            
        # Import and shut down the server
        import dreamwave_texgen_api
        api = dreamwave_texgen_api.DreamwaveTexGenAPI()
        result = dreamwave_texgen_api.DreamwaveTexGenAPI.shutdown_comfyui_server()
        
        if result:
            message = "ComfyUI server shut down successfully"
            unreal.log(message)
            
            # Try to show a confirmation dialog
            try:
                import unreal
                unreal.EditorDialog.show_message(
                    title="ComfyUI Server",
                    message=message,
                    message_type=unreal.AppMsgType.OK
                )
            except:
                pass
        else:
            # Try the forceful Windows-specific method as a last resort
            if os.name == 'nt':  # Windows
                try:
                    unreal.log("Attempting forceful Windows-specific shutdown...")
                    
                    # Use netstat to find processes on port 8188
                    import subprocess
                    netstat_output = subprocess.check_output(
                        "netstat -ano | findstr :8188", 
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    ).decode('utf-8')
                    
                    lines = netstat_output.strip().split('\n')
                    pids = set()
                    
                    for line in lines:
                        if '8188' in line:
                            try:
                                pid = line.strip().split()[-1]
                                pids.add(pid)
                            except:
                                pass
                    
                    for pid in pids:
                        try:
                            unreal.log(f"Forcefully terminating process with PID {pid}")
                            subprocess.call(
                                f"taskkill /F /PID {pid}", 
                                shell=True,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                            result = True
                        except:
                            pass
                            
                    # Also try to kill any python.exe running main.py
                    try:
                        unreal.log("Attempting to forcefully terminate Python processes running main.py...")
                        subprocess.call(
                            'wmic process where "commandline like \'%main.py%\'" call terminate',
                            shell=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        result = True
                    except:
                        pass
                except Exception as e:
                    unreal.log_warning(f"Forceful shutdown attempt failed: {e}")
            
            if result:
                message = "ComfyUI server shut down successfully using forceful method"
            else:
                message = "No running ComfyUI server found to shut down"
                
            unreal.log(message)
            
            # Try to show an info dialog
            try:
                import unreal
                unreal.EditorDialog.show_message(
                    title="ComfyUI Server",
                    message=message,
                    message_type=unreal.AppMsgType.OK
                )
            except:
                pass
                
        return True
    except Exception as e:
        unreal.log_error(f"Failed to shut down ComfyUI server: {str(e)}")
        
        # Try to show an error dialog
        try:
            import unreal
            unreal.EditorDialog.show_message(
                title="ComfyUI Shutdown Error",
                message=f"Failed to shut down ComfyUI server: {str(e)}",
                message_type=unreal.AppMsgType.OK
            )
        except:
            pass
            
        return False

def force_kill_comfyui():
    """Forcefully kill all ComfyUI server processes."""
    try:
        unreal.log("Forcefully killing all ComfyUI server processes...")
        
        if os.name == 'nt':  # Windows
            import subprocess
            
            # Method 1: Kill by port
            try:
                unreal.log("Finding processes using port 8188...")
                netstat_output = subprocess.check_output(
                    "netstat -ano | findstr :8188", 
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                ).decode('utf-8')
                
                lines = netstat_output.strip().split('\n')
                pids_killed = []
                
                for line in lines:
                    if '8188' in line:
                        try:
                            pid = line.strip().split()[-1]
                            unreal.log(f"Killing process on port 8188 with PID: {pid}")
                            subprocess.call(
                                f"taskkill /F /PID {pid}", 
                                shell=True,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                            pids_killed.append(pid)
                        except Exception as e:
                            unreal.log_warning(f"Error killing process: {e}")
                
                if pids_killed:
                    unreal.log(f"Killed processes using port 8188: {', '.join(pids_killed)}")
            except Exception as e:
                unreal.log_warning(f"Error finding processes by port: {e}")
            
            # Method 2: Kill any Python process running main.py
            try:
                unreal.log("Killing all Python processes running main.py...")
                result = subprocess.call(
                    'wmic process where "commandline like \'%main.py%\'" call terminate',
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                unreal.log(f"WMIC command executed with result: {result}")
            except Exception as e:
                unreal.log_warning(f"Error killing Python processes: {e}")
                
            # Method 3: Kill Python.exe processes (more aggressive approach)
            try:
                # Get a list of Python processes
                result = subprocess.check_output(
                    'wmic process where "name=\'python.exe\'" get processid',
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                ).decode('utf-8')
                
                # Extract PIDs
                lines = result.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    line = line.strip()
                    if line:
                        try:
                            unreal.log(f"Checking Python process with PID: {line}")
                            # Check if this process is related to ComfyUI
                            cmd_result = subprocess.check_output(
                                f'wmic process where "processid=\'{line}\'" get commandline',
                                shell=True,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            ).decode('utf-8')
                            
                            if 'main.py' in cmd_result or 'comfyui' in cmd_result.lower():
                                unreal.log(f"Killing Python process with PID {line} (appears to be ComfyUI related)")
                                subprocess.call(
                                    f"taskkill /F /PID {line}", 
                                    shell=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                        except Exception as e:
                            unreal.log_warning(f"Error processing Python process {line}: {e}")
            except Exception as e:
                unreal.log_warning(f"Error listing Python processes: {e}")
            
            # Also check for remnant batch files and delete them
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                batch_files = [
                    os.path.join(script_dir, "comfyui_process_watcher.bat"),
                    os.path.join(script_dir, "kill_comfyui_server.bat"),
                    os.path.join(script_dir, "launch_comfyui.bat")
                ]
                
                for batch_file in batch_files:
                    if os.path.exists(batch_file):
                        try:
                            os.remove(batch_file)
                            unreal.log(f"Removed batch file: {batch_file}")
                        except Exception as e:
                            unreal.log_warning(f"Failed to remove batch file {batch_file}: {e}")
            except Exception as e:
                unreal.log_warning(f"Error cleaning up batch files: {e}")
                
            # Display success message
            message = "Force kill completed. Any ComfyUI processes should be terminated."
            unreal.log(message)
            
            try:
                import unreal
                unreal.EditorDialog.show_message(
                    title="ComfyUI Force Kill",
                    message=message,
                    message_type=unreal.AppMsgType.OK
                )
            except:
                pass
                
            return True
            
        else:  # Mac/Linux
            import subprocess
            
            # Use lsof to find processes on port 8188
            try:
                lsof_output = subprocess.check_output(
                    "lsof -i :8188 -t", 
                    shell=True
                ).decode('utf-8')
                
                for pid in lsof_output.strip().split('\n'):
                    if pid:
                        unreal.log(f"Killing process on port 8188 with PID: {pid}")
                        subprocess.call(f"kill -9 {pid}", shell=True)
            except:
                pass
                
            # Use pkill to kill Python processes with main.py in command line
            try:
                unreal.log("Killing all Python processes running main.py...")
                subprocess.call("pkill -9 -f 'python.*main.py'", shell=True)
            except:
                pass
                
            # Display success message
            message = "Force kill command executed. Any ComfyUI processes should be terminated."
            unreal.log(message)
            
            try:
                import unreal
                unreal.EditorDialog.show_message(
                    title="ComfyUI Force Kill",
                    message=message,
                    message_type=unreal.AppMsgType.OK
                )
            except:
                pass
                
            return True
    
    except Exception as e:
        unreal.log_error(f"Force kill failed: {str(e)}")
        
        try:
            import unreal
            unreal.EditorDialog.show_message(
                title="ComfyUI Force Kill Error",
                message=f"Force kill operation encountered errors: {str(e)}",
                message_type=unreal.AppMsgType.OK
            )
        except:
            pass
            
        return False

# Print instructions when this module is imported directly
unreal.log("=== Dreamwave Commands ===")
unreal.log("- Type dreamwave_command.run_dreamwave() to open the Texture Generator UI")
unreal.log("- Type dreamwave_command.check_comfyui() to check the ComfyUI server status")
unreal.log("- Type dreamwave_command.launch_comfyui() to launch the ComfyUI server")
unreal.log("- Type dreamwave_command.shutdown_comfyui() to shut down the ComfyUI server")
unreal.log("- Type dreamwave_command.force_kill_comfyui() to forcefully terminate any ComfyUI processes")

# For direct imports
if __name__ == "__main__":
    run_dreamwave() 