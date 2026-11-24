"""Exercise the installed G1 package without adding the repository to sys.path.

Run from the repository root after `python -m pip install .`.
"""

import hashlib
import json
from pathlib import Path
import tempfile

import emotionet
from emotionet import Emotionet


def main():
    source = Path(__file__).resolve().parents[1] / "data/local/seed-synsets-v2"
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with Emotionet.open(root / "snapshot.sqlite", mode="research") as net:
            counts = net.import_jsonl(source)
            assert counts["concepts"] == 66 and counts["senses"] == 82
            hit = net.lookup("  KHÓ   CHỊU ")
            assert hit[0]["senses"][0]["sense"]["emotion_labels"] == ["annoyance"]
            assert sum(len(e["senses"]) for e in net.lookup("ghét")) >= 2
            exported = net.export_jsonl(root / "exported")
            hashes = lambda directory: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()}
            assert hashes(source) == hashes(exported)
        print(json.dumps({"version": emotionet.__version__, "package": str(Path(emotionet.__file__).resolve()),
                          "counts": counts, "roundtrip": "byte_exact", "status": "passed"}, indent=2))


if __name__ == "__main__":
    main()
