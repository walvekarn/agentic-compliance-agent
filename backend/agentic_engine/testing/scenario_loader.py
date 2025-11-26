"""
Scenario Loader
===============
Loads curated test scenarios from JSON files.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def load_scenarios_from_directory(scenarios_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load all test scenarios from JSON files in the scenarios directory.
    
    Args:
        scenarios_dir: Optional path to scenarios directory (defaults to test_scenarios/)
        
    Returns:
        List of scenario dictionaries
    """
    if scenarios_dir is None:
        # Default to test_scenarios/ in project root
        project_root = Path(__file__).parent.parent.parent.parent
        scenarios_dir = project_root / "test_scenarios"
    
    scenarios = []
    
    if not scenarios_dir.exists():
        logger.warning(f"Scenarios directory not found: {scenarios_dir}")
        return scenarios
    
    # Load all JSON files
    for json_file in scenarios_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                scenario = json.load(f)
                
                # Validate required fields
                required_fields = ["input", "expected_decision", "expected_risk_level", "expected_min_confidence"]
                missing_fields = [field for field in required_fields if field not in scenario]
                
                if missing_fields:
                    logger.warning(f"Scenario {json_file.name} missing required fields: {missing_fields}")
                    continue
                
                # Add filename for reference
                scenario["_filename"] = json_file.name
                scenarios.append(scenario)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {json_file.name}: {e}")
        except Exception as e:
            logger.error(f"Error loading {json_file.name}: {e}")
    
    logger.info(f"Loaded {len(scenarios)} test scenarios from {scenarios_dir}")
    return scenarios

