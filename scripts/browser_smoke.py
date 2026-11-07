"""Read-only app regression: run generated-fixture playback tests."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("bundled_smoke.py")),run_name="__main__")
