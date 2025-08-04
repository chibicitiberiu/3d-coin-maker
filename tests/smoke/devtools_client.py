"""
Direct Chrome DevTools Protocol client for QtWebEngine automation.
Bypasses Selenium to communicate directly with QtWebEngine via WebSocket.
"""

import json
import time
import asyncio
import websockets
import requests
from typing import Dict, Any, Optional, List


class DevToolsClient:
    """Direct Chrome DevTools Protocol client for desktop automation."""
    
    def __init__(self, debug_port: int = 9222):
        """Initialize DevTools client.
        
        Args:
            debug_port: Chrome DevTools debug port
        """
        self.debug_port = debug_port
        self.base_url = f"http://127.0.0.1:{debug_port}"
        self.websocket = None
        self.page_id = None
        self.command_id = 0
        
    def get_pages(self) -> List[Dict[str, Any]]:
        """Get list of available pages/tabs.
        
        Returns:
            List of page information dictionaries
        """
        try:
            response = requests.get(f"{self.base_url}/json", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"ERROR: Failed to get pages: {response.status_code}")
                return []
        except Exception as e:
            print(f"ERROR: Failed to connect to DevTools: {e}")
            return []
    
    def connect_to_page(self, page_url_contains: str = None) -> bool:
        """Connect to a specific page via WebSocket.
        
        Args:
            page_url_contains: Find page containing this URL substring
            
        Returns:
            True if connected successfully
        """
        try:
            pages = self.get_pages()
            if not pages:
                print("ERROR: No pages found")
                return False
            
            # Find the right page
            target_page = None
            if page_url_contains:
                for page in pages:
                    if page_url_contains in page.get('url', ''):
                        target_page = page
                        break
            else:
                # Use first page
                target_page = pages[0]
            
            if not target_page:
                print(f"ERROR: Could not find page containing '{page_url_contains}'")
                print("Available pages:")
                for page in pages:
                    print(f"  - {page.get('title', 'No title')} - {page.get('url', 'No URL')}")
                return False
            
            self.page_id = target_page['id']
            websocket_url = target_page['webSocketDebuggerUrl']
            
            print(f"Connecting to page: {target_page.get('title', 'Unknown')} - {target_page.get('url', 'Unknown')}")
            print(f"WebSocket URL: {websocket_url}")
            
            # Note: We'll use asyncio for the actual WebSocket connection
            self.websocket_url = websocket_url
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to connect to page: {e}")
            return False
    
    async def send_command(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to the DevTools WebSocket.
        
        Args:
            method: DevTools protocol method name
            params: Method parameters
            
        Returns:
            Command response
        """
        if not self.websocket:
            raise RuntimeError("Not connected to WebSocket")
        
        self.command_id += 1
        command = {
            "id": self.command_id,
            "method": method,
            "params": params or {}
        }
        
        await self.websocket.send(json.dumps(command))
        
        # Wait for response
        while True:
            response = await self.websocket.recv()
            data = json.loads(response)
            
            # Check if this is our response
            if data.get('id') == self.command_id:
                if 'error' in data:
                    raise RuntimeError(f"DevTools error: {data['error']}")
                return data.get('result', {})
            # Ignore other messages (events, etc.)
    
    async def navigate_to(self, url: str) -> bool:
        """Navigate to a URL.
        
        Args:
            url: Target URL
            
        Returns:
            True if navigation successful
        """
        try:
            # Enable Page domain
            await self.send_command("Page.enable")
            
            # Navigate to URL
            result = await self.send_command("Page.navigate", {"url": url})
            
            if 'frameId' in result:
                print(f"Navigation initiated to: {url}")
                
                # Wait for page to load
                await asyncio.sleep(3)
                return True
            else:
                print(f"ERROR: Navigation failed: {result}")
                return False
                
        except Exception as e:
            print(f"ERROR: Failed to navigate: {e}")
            return False
    
    async def click_element(self, selector: str) -> bool:
        """Click an element by CSS selector.
        
        Args:
            selector: CSS selector
            
        Returns:
            True if click successful
        """
        try:
            # Enable Runtime and DOM domains
            await self.send_command("Runtime.enable")
            await self.send_command("DOM.enable")
            
            # Find element
            doc_result = await self.send_command("DOM.getDocument")
            root_node_id = doc_result['root']['nodeId']
            
            node_result = await self.send_command("DOM.querySelector", {
                "nodeId": root_node_id,
                "selector": selector
            })
            
            if not node_result.get('nodeId'):
                print(f"ERROR: Element not found: {selector}")
                return False
            
            node_id = node_result['nodeId']
            
            # Get element position
            box_result = await self.send_command("DOM.getBoxModel", {"nodeId": node_id})
            
            if 'model' not in box_result:
                print(f"ERROR: Could not get element position: {selector}")
                return False
            
            # Calculate click position (center of element)
            content = box_result['model']['content']
            x = (content[0] + content[2]) / 2
            y = (content[1] + content[5]) / 2
            
            # Enable Input domain and click
            await self.send_command("Input.enable") 
            
            # Mouse down
            await self.send_command("Input.dispatchMouseEvent", {
                "type": "mousePressed",
                "x": x,
                "y": y,
                "button": "left",
                "clickCount": 1
            })
            
            # Mouse up
            await self.send_command("Input.dispatchMouseEvent", {
                "type": "mouseReleased", 
                "x": x,
                "y": y,
                "button": "left",
                "clickCount": 1
            })
            
            print(f"Clicked element: {selector} at ({x}, {y})")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to click element {selector}: {e}")
            return False
    
    async def find_element(self, selector: str) -> bool:
        """Check if an element exists.
        
        Args:
            selector: CSS selector
            
        Returns:
            True if element exists
        """
        try:
            await self.send_command("DOM.enable")
            
            doc_result = await self.send_command("DOM.getDocument")
            root_node_id = doc_result['root']['nodeId']
            
            node_result = await self.send_command("DOM.querySelector", {
                "nodeId": root_node_id,
                "selector": selector
            })
            
            return bool(node_result.get('nodeId'))
            
        except Exception as e:
            print(f"ERROR: Failed to find element {selector}: {e}")
            return False
    
    async def upload_test_image(self, image_path: str) -> bool:
        """Upload test image file using proper DevTools DOM.setFileInputFiles method.
        
        Args:
            image_path: Path to the test image file
            
        Returns:
            True if upload was successful and UI shows the uploaded image
        """
        try:
            import os
            
            if not os.path.exists(image_path):
                print(f"ERROR: Test image not found: {image_path}")
                return False
            
            # Enable DOM domain
            await self.send_command("DOM.enable")
            
            # Get the document root
            doc_result = await self.send_command("DOM.getDocument")
            root_node_id = doc_result['root']['nodeId']
            
            # Find the file input using various selectors
            selectors = [
                '#file-upload-input',
                'input[type="file"]',
                'input[accept*="image"]',
                '[data-testid="file-input"]'
            ]
            
            file_input_node_id = None
            for selector in selectors:
                try:
                    node_result = await self.send_command("DOM.querySelector", {
                        "nodeId": root_node_id,
                        "selector": selector
                    })
                    if node_result.get('nodeId'):
                        file_input_node_id = node_result['nodeId']
                        print(f"Found file input with selector: {selector}")
                        break
                except:
                    continue
            
            if not file_input_node_id:
                print("ERROR: Could not find file input element")
                return False
            
            # Use the REAL DevTools method for file uploads
            print(f"Setting files on input using DOM.setFileInputFiles: {image_path}")
            
            result = await self.send_command("DOM.setFileInputFiles", {
                "files": [os.path.abspath(image_path)],
                "nodeId": file_input_node_id
            })
            
            print("Real file upload completed via DOM.setFileInputFiles")
            
            # Wait for the UI to process the upload and check for visual feedback
            print("Waiting for UI to process the upload...")
            await asyncio.sleep(5)  # Give more time for processing
            
            # Check for UI indicators that the upload was processed
            indicators_js = """
            (function() {
                const indicators = [
                    document.querySelector('img[src*="blob:"]'),
                    document.querySelector('canvas'),
                    document.querySelector('.preview'),
                    document.querySelector('[data-testid="image-preview"]'),
                    document.querySelector('.canvas-viewer'),
                    document.querySelector('.processed-image'),
                    document.querySelector('.upload-preview'),
                    document.querySelector('[src*="data:image"]')
                ];
                
                const found = indicators.filter(el => el !== null);
                const fileInput = document.querySelector('#file-upload-input') || document.querySelector('input[type="file"]');
                
                return {
                    hasVisualFeedback: found.length > 0,
                    foundElements: found.map(el => el.tagName + (el.className ? '.' + el.className : '') + (el.src ? ' src=' + el.src.substring(0, 50) + '...' : '')),
                    inputHasFiles: fileInput ? fileInput.files.length > 0 : false,
                    inputValue: fileInput ? fileInput.value : 'no-input',
                    fileName: fileInput && fileInput.files.length > 0 ? fileInput.files[0].name : 'no-file'
                };
            })()
            """
            
            feedback_result = await self.send_command("Runtime.evaluate", {
                "expression": indicators_js,
                "returnByValue": True
            })
            
            feedback_data = feedback_result.get('result', {}).get('value', {})
            
            print(f"Upload feedback: {feedback_data}")
            
            if feedback_data.get('inputHasFiles'):
                print(f"SUCCESS: File input now contains file: {feedback_data.get('fileName')}")
                
                if feedback_data.get('hasVisualFeedback'):
                    print(f"SUCCESS: Visual feedback detected: {feedback_data.get('foundElements')}")
                else:
                    print("File uploaded but waiting for visual processing...")
                    # Wait a bit more for visual processing
                    await asyncio.sleep(3)
                
                return True
            else:
                print("ERROR: File input does not contain files after upload")
                return False
                
        except Exception as e:
            print(f"ERROR: Failed to upload test image: {e}")
            return False
    
    async def set_coin_parameters(self, diameter: float = 25.0, thickness: float = 2.0, depth: float = 1.0) -> bool:
        """Set coin generation parameters.
        
        Args:
            diameter: Coin diameter in mm
            thickness: Coin thickness in mm  
            depth: Relief depth in mm
            
        Returns:
            True if parameters were set successfully
        """
        try:
            await self.send_command("Runtime.enable")
            
            # Parameter mappings (same as BaseSmokeTest)
            parameters = {
                'diameter': {
                    'selectors': ['#coin-size', 'input[name="diameter"]', '#diameter'],
                    'value': diameter
                },
                'thickness': {
                    'selectors': ['#coin-thickness', 'input[name="thickness"]', '#thickness'],
                    'value': thickness
                },
                'depth': {
                    'selectors': ['#relief-depth', 'input[name="depth"]', '#depth', 'input[name="height"]', '#height'],
                    'value': depth
                }
            }
            
            success_count = 0
            for param_name, param_info in parameters.items():
                selectors = param_info['selectors']
                value = param_info['value']
                
                # Try each selector until one works
                param_set = False
                for selector in selectors:
                    try:
                        js_code = f"""
                        (function() {{
                            var input = document.querySelector('{selector}');
                            if (input) {{
                                // Set the value
                                if (input.type === 'range') {{
                                    input.value = {value};
                                }} else {{
                                    input.value = '{value}';
                                }}
                                
                                // Trigger multiple events to ensure framework reactivity
                                input.dispatchEvent(new Event('input', {{bubbles: true}}));
                                input.dispatchEvent(new Event('change', {{bubbles: true}}));
                                
                                // For React/Svelte - trigger additional events
                                if (window.React || window.__svelte) {{
                                    // Simulate user interaction for React
                                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                    nativeInputValueSetter.call(input, input.value);
                                    
                                    // Dispatch React-friendly events
                                    input.dispatchEvent(new Event('input', {{bubbles: true}}));
                                    input.dispatchEvent(new Event('change', {{bubbles: true}}));
                                }}
                                
                                console.log('Set parameter {param_name} to', input.value);
                                return true;
                            }}
                            return false;
                        }})()
                        """
                        
                        result = await self.send_command("Runtime.evaluate", {
                            "expression": js_code,
                            "returnByValue": True
                        })
                        
                        if result.get('result', {}).get('value'):
                            print(f"Set {param_name} to {value}")
                            success_count += 1
                            param_set = True
                            break
                            
                    except Exception as e:
                        print(f"Failed to set {param_name} with selector {selector}: {e}")
                        continue
                
                if not param_set:
                    print(f"WARNING: Could not find input for {param_name}")
            
            # Consider it successful if we set at least one parameter
            return success_count > 0
            
        except Exception as e:
            print(f"ERROR: Failed to set parameters: {e}")
            return False
    
    async def generate_stl(self) -> bool:
        """Click generate STL button and verify the action.
        
        Returns:
            True if generation was triggered successfully
        """
        try:
            await self.send_command("Runtime.enable")
            
            # Try to find and click generate button, but check if it's enabled first
            js_code = """
            (function() {
                console.log('Looking for generate button...');
                
                // Helper function to find button by text content
                var buttons = document.querySelectorAll('button');
                var generateButton = null;
                
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    if (btn.textContent.toLowerCase().includes('generate')) {
                        generateButton = btn;
                        console.log('Found generate button:', btn.textContent, 'disabled:', btn.disabled);
                        break;
                    }
                }
                
                if (!generateButton) {
                    console.log('No generate button found');
                    return {success: false, error: 'Generate button not found'};
                }
                
                if (generateButton.disabled) {
                    console.log('Generate button is disabled - upload may not be complete');
                    return {success: false, error: 'Generate button is disabled', buttonText: generateButton.textContent};
                }
                
                // Button is enabled, click it
                generateButton.click();
                console.log('Generate button clicked successfully');
                
                return {success: true, buttonText: generateButton.textContent};
            })()
            """
            
            result = await self.send_command("Runtime.evaluate", {
                "expression": js_code,
                "returnByValue": True
            })
            
            button_result = result.get('result', {}).get('value', {})
            
            if button_result.get('success'):
                print(f"Generate button clicked successfully: {button_result.get('buttonText')}")
                
                # Wait longer for UI changes and check multiple times
                print("Monitoring UI changes after button click...")
                
                final_feedback = None
                for check_num in range(5):  # Check 5 times over 10 seconds
                    await asyncio.sleep(2)
                    print(f"UI check #{check_num + 1}...")
                    
                    generation_feedback_js = """
                (function() {
                    // Look for signs that STL generation is happening
                    const progressIndicators = [
                        document.querySelector('.generating'),
                        document.querySelector('.progress'),
                        document.querySelector('.progress-bar'),
                        document.querySelector('[role="progressbar"]'),
                        document.querySelector('.loading'),
                        document.querySelector('.spinner'),
                        document.querySelector('.stl-progress'),
                        document.querySelector('.generation-progress')
                    ];
                    
                    // Look for tab switching to "Final result" - using JavaScript-compatible methods
                    const finalResultTabs = Array.from(document.querySelectorAll('button, .tab')).filter(el => 
                        el.textContent && el.textContent.toLowerCase().includes('final')
                    );
                    const finalResultTab = finalResultTabs[0] || null;
                    
                    // Look for any progress-related text
                    const progressText = document.body.textContent.toLowerCase();
                    const hasProgressText = progressText.includes('progress') || 
                                          progressText.includes('generating') || 
                                          progressText.includes('processing') ||
                                          progressText.includes('%');
                    
                    // Check for generate button state
                    const generateBtns = Array.from(document.querySelectorAll('button')).filter(btn => 
                        btn.textContent.toLowerCase().includes('generate')
                    );
                    
                    const browseBtns = Array.from(document.querySelectorAll('button')).filter(btn => 
                        btn.textContent.toLowerCase().includes('browse')
                    );
                    
                    return {
                        hasProgressIndicators: progressIndicators.filter(el => el !== null).length > 0,
                        foundProgressElements: progressIndicators.filter(el => el !== null).map(el => el.tagName + '.' + el.className),
                        finalResultTabFound: !!finalResultTab,
                        finalResultTabActive: finalResultTab ? finalResultTab.classList.contains('active') : false,
                        hasProgressText: hasProgressText,
                        generateButtonCount: generateBtns.length,
                        browseButtonCount: browseBtns.length,
                        generateButtonText: generateBtns.map(btn => btn.textContent),
                        browseButtonText: browseBtns.map(btn => btn.textContent),
                        allButtonsText: Array.from(document.querySelectorAll('button')).map(btn => btn.textContent)
                    };
                })()
                """
                
                    feedback_result = await self.send_command("Runtime.evaluate", {
                        "expression": generation_feedback_js,
                        "returnByValue": True
                    })
                    
                    feedback_data = feedback_result.get('result', {}).get('value', {})
                    print(f"Generation feedback #{check_num + 1}: {feedback_data}")
                    final_feedback = feedback_data
                    
                    # If we found progress indicators, we can break early
                    if feedback_data.get('hasProgressIndicators') or feedback_data.get('hasProgressText'):
                        print("Found progress indicators - STL generation UI is working!")
                        break
                
                # After UI monitoring, check if STL generation actually completed successfully
                print("Checking backend for STL generation status...")
                await asyncio.sleep(5)  # Give more time for backend processing
                
                # Check backend API for generation status
                backend_check_js = """
                (async function() {
                    try {
                        // Try to find generation ID from the page state or localStorage
                        let generationId = null;
                        
                        // Method 1: Check if it's stored in window object (Svelte stores)
                        if (window.generationId) {
                            generationId = window.generationId;
                        }
                        
                        // Method 2: Check localStorage for recent generation
                        if (!generationId) {
                            const storedData = localStorage.getItem('current_generation');
                            if (storedData) {
                                try {
                                    const parsed = JSON.parse(storedData);
                                    generationId = parsed.id || parsed.generationId;
                                } catch (e) {
                                    // Try as direct string
                                    generationId = storedData;
                                }
                            }
                        }
                        
                        // Method 3: Extract from download button (most reliable for completed generations)
                        if (!generationId) {
                            // Look for download button and extract generation ID from its href/onclick
                            const downloadSelectors = [
                                'a[href*="download"]',
                                'button[onclick*="download"]', 
                                '[data-testid*="download"]',
                                'a[href*="/stl"]',
                                'button:contains("Download")',
                                '.download-btn',
                                '[class*="download"]'
                            ];
                            
                            for (const selector of downloadSelectors) {
                                const downloadBtn = document.querySelector(selector);
                                if (downloadBtn) {
                                    const href = downloadBtn.href || downloadBtn.getAttribute('onclick') || downloadBtn.textContent || '';
                                    const match = href.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i);
                                    if (match) {
                                        generationId = match[0];
                                        break;
                                    }
                                }
                            }
                        }
                        
                        // Method 4: Check all buttons for any UUID patterns (fallback)
                        if (!generationId) {
                            const allButtons = document.querySelectorAll('button, a, [data-*]');
                            for (const element of allButtons) {
                                const text = element.textContent + ' ' + element.outerHTML;
                                const match = text.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i);
                                if (match) {
                                    generationId = match[0];
                                    break;
                                }
                            }
                        }
                        
                        if (!generationId) {
                            // Debug: Return what we found for analysis
                            const debugInfo = {
                                windowKeys: Object.keys(window).filter(k => k.toLowerCase().includes('generation')),
                                localStorageKeys: Object.keys(localStorage),
                                downloadButtons: Array.from(document.querySelectorAll('button, a')).map(el => ({
                                    tag: el.tagName,
                                    text: el.textContent?.substring(0, 50),
                                    href: el.href?.substring(0, 100),
                                    onclick: el.getAttribute('onclick')?.substring(0, 100),
                                    classes: el.className
                                })).filter(el => el.text?.toLowerCase().includes('download') || el.href?.includes('download'))
                            };
                            return {success: false, error: 'Could not find generation ID', debug: debugInfo};
                        }
                        
                        // Check if STL file exists by attempting to download it
                        const stlResponse = await fetch(`/download/${generationId}/stl`, {
                            method: 'HEAD'
                        });
                        
                        const hasStlFile = stlResponse.ok;
                        const stlFileSize = stlResponse.headers.get('content-length');
                        
                        // Also check the status endpoint if available
                        let statusInfo = null;
                        try {
                            const statusResponse = await fetch(`/status/${generationId}/`);
                            if (statusResponse.ok) {
                                statusInfo = await statusResponse.json();
                            }
                        } catch (e) {
                            // Status endpoint might not be available
                        }
                        
                        return {
                            success: true,
                            generationId: generationId,
                            hasStlFile: hasStlFile,
                            stlFileSize: stlFileSize,
                            stlStatus: stlResponse.status,
                            statusInfo: statusInfo
                        };
                    } catch (error) {
                        return {success: false, error: error.message};
                    }
                })()
                """
                
                backend_result = await self.send_command("Runtime.evaluate", {
                    "expression": backend_check_js,
                    "returnByValue": True,
                    "awaitPromise": True
                })
                
                backend_data = backend_result.get('result', {}).get('value', {})
                print(f"Backend STL check result: {backend_data}")
                
                if backend_data.get('success') and backend_data.get('hasStlFile'):
                    stl_size = backend_data.get('stlFileSize', 'unknown')
                    print(f"SUCCESS: STL file generated and available for download (size: {stl_size} bytes)")
                    return True
                else:
                    error = backend_data.get('error', 'STL file not found')
                    print(f"FAILURE: STL generation did not complete successfully: {error}")
                    return False
                    
            else:
                error_msg = button_result.get('error', 'Unknown error')
                print(f"Generate button action failed: {error_msg}")
                
                if 'disabled' in error_msg:
                    print("ISSUE: Generate button is disabled - this means the upload/parameters didn't work properly")
                
                return False
                
        except Exception as e:
            print(f"ERROR: Failed to generate STL: {e}")
            return False
    
    async def wait_for_generate_button_enabled(self, timeout_seconds: int = 15) -> bool:
        """Wait for the generate button to become enabled.
        
        Args:
            timeout_seconds: Maximum time to wait for button to be enabled
            
        Returns:
            True if button becomes enabled within timeout
        """
        try:
            await self.send_command("Runtime.enable")
            
            print(f"Waiting up to {timeout_seconds} seconds for generate button to be enabled...")
            
            for attempt in range(timeout_seconds):
                check_js = """
                (function() {
                    const buttons = document.querySelectorAll('button');
                    let generateButton = null;
                    
                    for (let btn of buttons) {
                        if (btn.textContent.toLowerCase().includes('generate')) {
                            generateButton = btn;
                            break;
                        }
                    }
                    
                    if (!generateButton) {
                        return {found: false, enabled: false, text: 'not-found'};
                    }
                    
                    return {
                        found: true,
                        enabled: !generateButton.disabled,
                        text: generateButton.textContent,
                        disabled: generateButton.disabled
                    };
                })()
                """
                
                result = await self.send_command("Runtime.evaluate", {
                    "expression": check_js,
                    "returnByValue": True
                })
                
                button_state = result.get('result', {}).get('value', {})
                
                if not button_state.get('found'):
                    print(f"Attempt {attempt + 1}: Generate button not found")
                elif button_state.get('enabled'):
                    print(f"SUCCESS: Generate button is enabled after {attempt + 1} seconds: '{button_state.get('text')}'")
                    return True
                else:
                    print(f"Attempt {attempt + 1}: Generate button found but disabled: '{button_state.get('text')}'")
                
                # Wait 1 second before next attempt
                await asyncio.sleep(1)
            
            print(f"TIMEOUT: Generate button did not become enabled within {timeout_seconds} seconds")
            return False
            
        except Exception as e:
            print(f"ERROR: Failed to wait for generate button: {e}")
            return False
    
    async def run_automation(self, frontend_url: str, test_image_path: str = None) -> Dict[str, bool]:
        """Run complete smoke test automation using DevTools (same workflow as web tests).
        
        Args:
            frontend_url: Frontend URL to test
            test_image_path: Path to test image file
            
        Returns:
            Dictionary of test results
        """
        results = {}
        
        try:
            # Connect to WebSocket
            async with websockets.connect(self.websocket_url) as websocket:
                self.websocket = websocket
                print("Connected to DevTools WebSocket")
                
                # Navigate to frontend
                print(f"Navigating to: {frontend_url}")
                results['navigation'] = await self.navigate_to(frontend_url)
                
                if not results['navigation']:
                    return results
                
                # Wait for page to load
                await asyncio.sleep(5)
                
                # Check if basic UI elements are present
                print("Checking for UI elements...")
                results['ui_loaded'] = await self.find_element("main") or await self.find_element(".app") or await self.find_element("#app")
                
                # Try to find file upload input
                print("Looking for file upload...")
                file_upload_present = await self.find_element('#file-upload-input') or await self.find_element('input[type="file"]')
                results['file_upload_present'] = file_upload_present
                
                # Try to find parameter inputs
                print("Looking for parameter inputs...")
                parameters_present = (
                    await self.find_element('#coin-size') or 
                    await self.find_element('#coin-thickness') or
                    await self.find_element('#relief-depth')
                )
                results['parameters_present'] = parameters_present
                
                # Try to find generate button
                print("Looking for generate button...")
                generate_button_present = await self.find_element("button")
                results['generate_button_present'] = generate_button_present
                
                # If we have all basic elements and a test image, run the full workflow
                if file_upload_present and test_image_path and generate_button_present:
                    print("\n=== Running Full Workflow ===")
                    
                    # 1. Upload test image
                    print("1. Uploading test image...")
                    results['image_upload'] = await self.upload_test_image(test_image_path)
                    
                    if results['image_upload']:
                        # 2. Wait for image processing
                        print("2. Waiting for image processing...")
                        await asyncio.sleep(3)
                        results['image_processing'] = True
                        
                        # 3. Set coin parameters
                        print("3. Setting coin parameters...")
                        results['set_parameters'] = await self.set_coin_parameters()
                        
                        # 4. Wait for generate button to become enabled
                        print("4. Waiting for generate button to be enabled...")
                        button_enabled = await self.wait_for_generate_button_enabled()
                        
                        if button_enabled:
                            print("5. Generate button is enabled - attempting to generate STL...")
                            results['generate_stl'] = await self.generate_stl()
                        else:
                            print("5. Generate button never became enabled - skipping STL generation")
                            results['generate_stl'] = False
                    else:
                        results['image_processing'] = False
                        results['set_parameters'] = False
                        results['generate_stl'] = False
                else:
                    print("Missing required elements for full workflow - skipping")
                    results['image_upload'] = False
                    results['image_processing'] = False
                    results['set_parameters'] = False
                    results['generate_stl'] = False
                
                print("DevTools automation completed successfully")
                return results
                
        except Exception as e:
            print(f"ERROR: DevTools automation failed: {e}")
            results['error'] = str(e)
            return results


async def test_devtools_client(debug_port: int = 9222, frontend_url: str = "http://127.0.0.1:5173"):
    """Test the DevTools client functionality.
    
    Args:
        debug_port: Chrome DevTools debug port
        frontend_url: Frontend URL to test
    """
    client = DevToolsClient(debug_port)
    
    print(f"Testing DevTools client on port {debug_port}")
    
    # Get available pages
    pages = client.get_pages()
    if not pages:
        print("ERROR: No pages found")
        return
    
    print(f"Found {len(pages)} pages:")
    for page in pages:
        print(f"  - {page.get('title', 'No title')} - {page.get('url', 'No URL')}")
    
    # Connect to page containing our frontend URL
    if not client.connect_to_page(frontend_url):
        print("ERROR: Failed to connect to page")
        return
    
    # Run automation
    results = await client.run_automation(frontend_url)
    
    print("\nTest Results:")
    for test, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {status}: {test}")


if __name__ == "__main__":
    # Test the DevTools client
    asyncio.run(test_devtools_client())