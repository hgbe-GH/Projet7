"""Lance Docker et garde les supports disponibles après fermeture du terminal."""
from pathlib import Path
import subprocess
import sys
import tempfile
from time import sleep
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
GUIDE = "http://127.0.0.1:8765/guide-soutenance-openagenda-rag.html"


def pages_available() -> bool:
    try:
        with urlopen(GUIDE, timeout=2) as response:
            return response.status == 200 and b"Guide personnel" in response.read(1000)
    except (URLError, TimeoutError):
        return False


def main() -> None:
    subprocess.run(["docker", "compose", "up", "-d", "--no-build"], cwd=ROOT, check=True)
    if not pages_available():
        log_path = Path(tempfile.gettempdir()) / "projet7-soutenance-http.log"
        with log_path.open("a") as log:
            subprocess.Popen(
                [sys.executable, str(ROOT / "docs/soutenance/serve_soutenance.py")],
                cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        for _ in range(20):
            if pages_available():
                break
            sleep(0.25)
        else:
            raise RuntimeError(f"Les pages ne répondent pas ; consulter {log_path}.")
    print("Pages disponibles en arrière-plan :")
    print(GUIDE)
    print("http://127.0.0.1:8765/presentation-soutenance-openagenda-rag.html")
    print("http://127.0.0.1:8765/demo-soutenance.html")


if __name__ == "__main__":
    main()
