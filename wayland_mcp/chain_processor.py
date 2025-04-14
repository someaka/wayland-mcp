"""Action chaining processor for MCP server commands."""
import logging
from typing import Dict

# Global handler registry populated when module loads
ACTION_HANDLERS = {}

class ChainProcessor:
    """Processes and executes sequences of MCP actions."""

    def __init__(self, chain_str: str):
        """Initialize with action chain string.

        Args:
            chain_str: Semicolon-separated action sequence
        """
        self.raw_chain = chain_str
        self.actions = []
        self.results = []
        self.max_chain_length = 10  # Security limit
        self.current_context = {}

    def parse(self) -> bool:
        """Validate and split chain into executable actions.

        Returns:
            bool: True if chain is valid and parsed successfully
        """
        if not self.raw_chain:
            logging.error("Empty action chain")
            return False

        steps = self.raw_chain.split(';')
        if len(steps) > self.max_chain_length:
            logging.error("Chain exceeds max length %d", self.max_chain_length)
            return False

        for step in steps:
            step = step.strip()
            if not step:
                continue

            # Handle both "action" and "action:param" formats
            if ':' in step:
                prefix = step.split(':', 1)[0] + ':'
            else:
                prefix = step

            if prefix not in ACTION_HANDLERS:
                # Try with colon if bare action didn't match
                if ':' not in step and (step + ':') in ACTION_HANDLERS:
                    prefix = step + ':'
                else:
                    logging.error("Unsupported action in '%s'", step)
                    return False

            self.actions.append(step)

        return bool(self.actions)

    def execute(self) -> Dict:
        """Execute validated action chain.

        Returns:
            Dict: Execution results including:
                - success: Overall status
                - steps: Total steps
                - executed: Steps completed
                - results: Detailed step outcomes
        """
        if not self.parse():
            return {
                "success": False,
                "error": "Invalid chain format",
                "steps": 0,
                "executed": 0,
                "results": []
            }

        for idx, action in enumerate(self.actions):
            try:
                result = self._execute_single(action)
                self.results.append({
                    "step": idx + 1,
                    "action": action,
                    "success": result.get("success", False),
                    "output": result.get("output", ""),
                    "error": result.get("error", "")
                })

                if not result["success"] and self._critical_action(action):
                    break

            except (RuntimeError, ValueError) as e:
                logging.error("Chain failed at step %d: %s", idx + 1, str(e))
                self.results.append({
                    "step": idx + 1,
                    "action": action,
                    "success": False,
                    "error": f"Unexpected error: {str(e)}"
                })
                break

        return {
            "success": all(r["success"] for r in self.results),
            "steps": len(self.actions),
            "executed": len(self.results),
            "results": self.results
        }

    def _execute_single(self, action: str) -> Dict:
        """Execute individual action using registered handlers.

        Args:
            action: Full action string with prefix

        Returns:
            Dict: Execution result with success status
        """
        for prefix, handler in ACTION_HANDLERS.items():
            if action.startswith(prefix):
                return {
                    "success": handler(action),
                    "output": f"Executed {prefix[:-1]} action"
                }
        return {
            "success": False,
            "error": "No handler found for action"
        }

    def _critical_action(self, action: str) -> bool:
        """Determine if failure should break the chain.
        
        Args:
            action: The action being evaluated
            
        Returns:
            bool: True if action is critical (default)
        """
        # Currently all actions are considered critical
        del action  # Explicitly mark unused parameter
        return True

def register_handler(prefix: str, handler):
    """Register an action handler for the processor.

    Args:
        prefix: Action prefix including colon (e.g. "click:")
        handler: Callable that takes the full action string
    """
    ACTION_HANDLERS[prefix] = handler
