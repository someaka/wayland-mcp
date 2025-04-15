"""ScreenController for capturing and analyzing screenshots using VLM."""
import logging
import os

from wayland_mcp.app import (
    capture_screenshot as capture_func,
    VLMAgent,
)
from wayland_mcp.add_rulers import add_rulers

class ScreenController:
    """Handles screen capture, comparison and analysis using VLM."""

    def __init__(self, vlm_agent: VLMAgent):
        """
        Initialize with a VLMAgent instance.
        """
        self.vlm_agent = vlm_agent

    def capture(self, filename: str = "screenshot.png", include_mouse: bool = True) -> dict:
        """Capture screenshot with measurement rulers.

        Args:
            filename: Output filename for the screenshot
            include_mouse: Whether to include mouse cursor (default: True)

        Returns:
            dict: {
                'success': bool,
                'filename': str (if successful),
                'error': str (if failed)
            }
        """
        try:
            result = capture_func(filename, include_mouse=include_mouse)
            if not isinstance(result, dict) or not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Capture failed")
                }

            try:
                return {
                    "success": True,
                    "filename": add_rulers(filename)
                }
            except (OSError, IOError) as e:
                logging.error("Failed to add rulers: %s", e)
                return result
        except (OSError, RuntimeError) as e:
            logging.error("Capture failed: %s", e)
            return {
                "success": False,
                "error": f"Capture failed: {str(e)}"
            }

    def compare(self, img1_path: str, img2_path: str) -> dict:
        """Compare two images using VLM.

        Args:
            img1_path: Path to first image
            img2_path: Path to second image

        Returns:
            dict: {
                'success': bool,
                'equal': bool (if successful),
                'error': str (if failed)
            }
        """
        try:
            abs_img1 = os.path.abspath(img1_path)
            abs_img2 = os.path.abspath(img2_path)

            if not all(os.path.exists(p) for p in (abs_img1, abs_img2)):
                return {
                    "success": False,
                    "error": "Image(s) not found"
                }

            return {
                "success": True,
                "equal": self.vlm_agent.compare_images(abs_img1, abs_img2)
            }
        except (OSError, RuntimeError) as e:
            logging.error("Image comparison failed: %s", e)
            return {
                "success": False,
                "error": f"Comparison failed: {str(e)}"
            }

    def analyze(self, image_path: str, prompt: str) -> dict:
        """Analyze screenshot using VLM.

        Args:
            image_path: Path to image to analyze
            prompt: Analysis prompt/question

        Returns:
            dict: {
                'success': bool,
                'analysis': str (if successful),
                'error': str (if failed)
            }
        """
        try:
            analysis = self.vlm_agent.analyze_image(image_path, prompt) or ""
            return {
                "success": True,
                "analysis": analysis
            }
        except (RuntimeError, ValueError) as e:
            logging.error("Image analysis failed: %s", e)
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }

    def capture_and_analyze(self, prompt: str, include_mouse: bool = True) -> dict:
        """Capture and analyze screenshot in one operation.

        Args:
            prompt: Analysis prompt/question
            include_mouse: Whether to include mouse cursor (default: True)

        Returns:
            dict: {
                'success': bool,
                'filename': str (if successful),
                'analysis': str (if successful),
                'filesize': int (if successful),
                'error': str (if failed)
            }
        """
        try:
            result = self.capture(include_mouse=include_mouse)
            if not result.get("success"):
                return result

            filename = result["filename"]
            if not os.path.exists(filename):
                return {
                    "success": False,
                    "error": "File not found"
                }

            analysis = self.analyze(filename, prompt)
            if not analysis.get("success"):
                return analysis

            return {
                "success": True,
                "filename": filename,
                "analysis": analysis["analysis"],
                "filesize": os.path.getsize(filename)
            }
        except (OSError, RuntimeError, ValueError) as e:
            logging.error("Capture and analyze failed: %s", e)
            return {
                "success": False,
                "error": f"Operation failed: {str(e)}"
            }
