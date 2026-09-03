import json
import sys
import tempfile
from pathlib import Path

import win32com.client


ROOT = Path(__file__).resolve().parent.parent
MATLAB_DIR = ROOT / "matlab"
OUTPUT = Path(tempfile.mkdtemp(prefix="phy_all_nodes_"))
CONFIG = OUTPUT / "config.json"
CONFIG.write_text(
    json.dumps(
        {
            "sourceMode": "Random bits",
            "text": "PHY",
            "numBits": 4000,
            "modulation": "16-QAM",
            "ebnoDb": 10.0,
            "seed": 7,
        }
    ),
    encoding="utf-8",
)


def q(path):
    return str(path).replace("'", "''")


matlab = win32com.client.Dispatch("Matlab.Desktop.Application")
matlab.Execute(f"addpath('{q(MATLAB_DIR)}')")
matlab.Execute(f"phy_level0_run('{q(CONFIG)}','{q(OUTPUT)}')")
for node in ("source", "group", "mapper", "channel", "detector", "sink"):
    image = OUTPUT / f"{node}.png"
    transcript = matlab.Execute(
        f"phy_render_trace('{q(OUTPUT / 'trace.mat')}','{node}','{q(image)}',false)"
    )
    if not image.exists():
        print(transcript, file=sys.stderr)
        raise SystemExit(f"Missing figure for {node}")
print(f"Rendered 6/6 MATLAB node figures in {OUTPUT}")
