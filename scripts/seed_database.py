"""Non-destructive successor to the legacy seed script.
The old skip-if-any-rows logic left a stale 6000-row database after Gold changed.
This entry point now builds a separate reconciled store and refuses overwrites.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.build_analytics_database import build_database
if __name__=='__main__':
    import json
    print(json.dumps(build_database(ROOT/'data/clearroute_analytics.db'),indent=2))
