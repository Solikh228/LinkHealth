import sys
from pathlib import Path

# Add observability/oncall-agent directory to sys.path so 'import app...' works seamlessly
agent_root = Path(__file__).resolve().parent.parent
if str(agent_root) not in sys.path:
    sys.path.insert(0, str(agent_root))
