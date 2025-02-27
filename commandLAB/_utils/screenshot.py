import os
import base64
import io
import datetime
from typing import Union, Literal, Optional, Any

try:
    from PIL import Image
except ImportError:
    Image = None  # PIL is optional

from commandLAB._utils.config import APPDIR
from commandLAB.types import ScreenshotObservation


def process_screenshot(
    screenshot_data: Any,
    output_format: Literal['base64', 'PIL', 'path'] = 'PIL',
    input_format: Literal['bytes', 'PIL', 'path', 'base64'] = None,
    computer_name: str = "computer",
    cleanup_temp_file: bool = True
) -> ScreenshotObservation:
    """Process a screenshot into the requested format.
    
    Args:
        screenshot_data: The screenshot data to process
        output_format: Format to return the screenshot in. Options are:
            - 'base64': Return the screenshot as a base64 encoded string
            - 'PIL': Return the screenshot as a PIL Image object
            - 'path': Save the screenshot to a file and return the path
        input_format: Format of the input data. If None, will be auto-detected. Options are:
            - 'bytes': Raw image data as bytes
            - 'PIL': A PIL Image object
            - 'path': Path to an image file
            - 'base64': Base64 encoded string
        computer_name: Name of the computer implementation (used in filename)
        cleanup_temp_file: Whether to delete the temporary file if screenshot_data is a path
        
    Returns:
        ScreenshotObservation with the screenshot in the requested format
    """
    # Auto-detect input format if not specified
    if input_format is None:
        if isinstance(screenshot_data, bytes):
            input_format = 'bytes'
        elif Image and isinstance(screenshot_data, Image.Image):
            input_format = 'PIL'
        elif isinstance(screenshot_data, str):
            # Check if it's a base64 string or a file path
            if os.path.exists(screenshot_data):
                input_format = 'path'
            else:
                try:
                    base64.b64decode(screenshot_data)
                    input_format = 'base64'
                except:
                    # Default to path if we can't determine
                    input_format = 'path'
        else:
            raise ValueError(f"Unsupported screenshot data type: {type(screenshot_data)}")
    
    # First convert input to a common intermediate format (PIL Image)
    img = None
    temp_file = None
    
    match input_format:
        case 'bytes':
            if output_format == 'base64':
                # Direct conversion without PIL
                b64_screenshot = base64.b64encode(screenshot_data).decode("utf-8")
                return ScreenshotObservation(screenshot=b64_screenshot)
            elif Image is not None:
                img = Image.open(io.BytesIO(screenshot_data))
            else:
                # If PIL is not available, we need to save to a temp file first
                temp_file = os.path.join(APPDIR, "temp", f"{computer_name}_temp_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png")
                os.makedirs(os.path.dirname(temp_file), exist_ok=True)
                with open(temp_file, 'wb') as f:
                    f.write(screenshot_data)
        
        case 'PIL':
            if Image is None:
                raise ImportError("PIL is required for PIL format input")
            img = screenshot_data
        
        case 'path':
            temp_file = screenshot_data
            if output_format == 'path' and os.path.dirname(screenshot_data) == os.path.join(APPDIR, "screenshots"):
                # Already in the right location
                return ScreenshotObservation(screenshot=screenshot_data)
            elif Image is not None and output_format != 'path':
                img = Image.open(screenshot_data)
        
        case 'base64':
            if output_format == 'base64':
                # Already in the right format
                return ScreenshotObservation(screenshot=screenshot_data)
            
            # Decode base64 to bytes
            img_data = base64.b64decode(screenshot_data)
            
            if output_format == 'path':
                # Save directly to file
                screenshots_dir = os.path.join(APPDIR, "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filepath = os.path.join(screenshots_dir, f"{computer_name}_screenshot_{timestamp}.png")
                
                with open(filepath, 'wb') as f:
                    f.write(img_data)
                
                return ScreenshotObservation(screenshot=filepath)
            elif Image is not None:
                img = Image.open(io.BytesIO(img_data))
            else:
                # If PIL is not available, we need to save to a temp file first
                temp_file = os.path.join(APPDIR, "temp", f"{computer_name}_temp_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png")
                os.makedirs(os.path.dirname(temp_file), exist_ok=True)
                with open(temp_file, 'wb') as f:
                    f.write(img_data)
    
    # Now convert to the output format
    match output_format:
        case 'base64':
            if img is not None:
                # Convert PIL Image to base64
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                b64_screenshot = base64.b64encode(buffer.getvalue()).decode("utf-8")
                return ScreenshotObservation(screenshot=b64_screenshot)
            elif temp_file is not None:
                # Read file and convert to base64
                with open(temp_file, 'rb') as f:
                    file_data = f.read()
                
                b64_screenshot = base64.b64encode(file_data).decode("utf-8")
                
                # Clean up temporary file if requested
                if cleanup_temp_file and input_format == 'path':
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                
                return ScreenshotObservation(screenshot=b64_screenshot)
        
        case 'PIL':
            if img is not None:
                return ScreenshotObservation(screenshot=img)
            elif temp_file is not None and Image is not None:
                # Read file into PIL Image
                img = Image.open(temp_file)
                
                # Clean up temporary file if requested
                if cleanup_temp_file and input_format == 'path':
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                
                return ScreenshotObservation(screenshot=img)
            else:
                raise ImportError("PIL is required for PIL format output")
        
        case 'path':
            screenshots_dir = os.path.join(APPDIR, "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filepath = os.path.join(screenshots_dir, f"{computer_name}_screenshot_{timestamp}.png")
            
            if img is not None:
                # Save PIL Image to file
                img.save(filepath, format="PNG")
                return ScreenshotObservation(screenshot=filepath)
            elif temp_file is not None:
                # Move/copy the file to the screenshots directory
                if Image is not None:
                    # Use PIL to read and save (handles format conversion if needed)
                    img = Image.open(temp_file)
                    img.save(filepath)
                else:
                    # Simple file copy
                    with open(temp_file, 'rb') as src, open(filepath, 'wb') as dst:
                        dst.write(src.read())
                
                # Clean up temporary file if requested
                if cleanup_temp_file and input_format == 'path':
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                
                return ScreenshotObservation(screenshot=filepath)
    
    # If we get here, we couldn't process the screenshot
    raise ValueError(f"Failed to process screenshot from {input_format} to {output_format}")


def base64_to_image(b64_data: str) -> Optional[Image.Image]:
    """Convert a base64 string to a PIL Image.
    
    Args:
        b64_data: Base64 encoded image data
        
    Returns:
        PIL Image object or None if PIL is not available
    """
    if Image is None:
        return None
        
    try:
        img_data = base64.b64decode(b64_data)
        return Image.open(io.BytesIO(img_data))
    except Exception:
        return None 