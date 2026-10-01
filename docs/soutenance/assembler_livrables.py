"""Assemble le dépôt plateforme et le kit sans données volumineuses ni secrets."""
from pathlib import Path
import zipfile

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"
PREFIX = "Concevez_et_deployez_un_systeme_RAG_Gaube_Hugo/"
LINK = "https://github.com/hgbe-GH/Projet7\n"
LINK_NAME = "Gaube_Hugo_1_liengithub_072026.txt"
SUPPORTS = [
    "AVANT-14H.md", "LIRE-MOI-SOUTENANCE.txt", "presentation-soutenance-openagenda-rag.html",
    "guide-soutenance-openagenda-rag.html", "demo-soutenance.html",
    "architecture-autoevaluation-soutenance.html", "architecture-uml.svg",
    "presentation-soutenance-openagenda-rag.pdf", "guide-soutenance-openagenda-rag.pdf",
    "script-oral-soutenance.pdf", "architecture-autoevaluation-soutenance.pdf",
    "openagenda-rag-soutenance.pptx", "rapport-technique-openagenda-rag.pdf",
    "rapport-technique-openagenda-rag.docx", "contenu-soutenance.json",
    "etat-preparation-2026-10-01.json", "demo/demo_api_2026-10-01.json",
    "demo/demo_api_timing.json", "evaluation/ragas_results.json",
    "evaluation/latest_results.json", "evaluation/latest_summary.json",
]


def verify(archive: Path) -> None:
    config = dotenv_values(ROOT / ".env")
    secrets = [value.encode() for key, value in config.items()
               if key in ("MISTRAL_API_KEY", "MISTRALAI_API_KEY", "API_REBUILD_TOKEN") and value]
    with zipfile.ZipFile(archive) as package:
        if package.testzip() is not None:
            raise RuntimeError("Archive corrompue")
        for name in package.namelist():
            if Path(name).name in (".env", ".env.local"):
                raise RuntimeError("Fichier de secrets interdit")
            body = package.read(name)
            if any(secret in body for secret in secrets):
                raise RuntimeError("Secret détecté : ne pas publier l’archive")


def main() -> None:
    official = OUT / "Concevez_et_deployez_un_systeme_RAG_Gaube_Hugo.zip"
    with zipfile.ZipFile(official, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr(PREFIX + LINK_NAME, LINK)
        for source, target in [
            ("openagenda-rag-soutenance.pptx", "Gaube_Hugo_2_presentation_072026.pptx"),
            ("rapport-technique-openagenda-rag.pdf", "Gaube_Hugo_3_rapport_072026.pdf"),
            ("architecture-autoevaluation-soutenance.pdf", "Gaube_Hugo_4_autoevaluation_072026.pdf"),
        ]:
            package.write(OUT / source, PREFIX + target)
    verify(official)

    files = [OUT / name for name in SUPPORTS]
    for folder in ("src", "scripts", "tests", "docs/soutenance", "docs/templates"):
        files.extend(path for path in (ROOT / folder).rglob("*") if path.is_file()
                     and not any(part in ("node_modules", "__pycache__") for part in path.parts)
                     and path.suffix not in (".pyc", ".pyo"))
    files.extend(ROOT / name for name in (
        "README.md", "Dockerfile", "docker-compose.yml", "requirements.txt", "environment.yml",
        ".env.example", ".gitignore", ".dockerignore",
        "seed-data/index/index_manifest.json", "seed-data/processed/fetch_manifest.json",
    ))
    kit = OUT / "kit-soutenance-Gaube-Hugo-2026-10-01.zip"
    with zipfile.ZipFile(kit, "w", zipfile.ZIP_DEFLATED) as package:
        for path in sorted(set(files)):
            package.write(path, PREFIX + str(path.relative_to(ROOT)))
        package.writestr(PREFIX + LINK_NAME, LINK)
        package.writestr(PREFIX + "LIRE-MOI-KIT.txt",
            "Commencer par outputs/AVANT-14H.md. Supports HTML, PDF et PowerPoint dans outputs/.\n"
            "Code et sources inclus sans clé API. Le Parquet et FAISS sont dans seed-data/ du dépôt GitHub ; "
            "ils ne sont pas dupliqués dans ce kit. Leurs manifestes sont inclus.\n"
            "Pour la démo du jour, configurer MISTRAL_API_KEY et RAG_CHAT_MODEL=ministral-8b-2512 "
            "dans un .env personnel. Les évaluations de juillet concernent mistral-small-latest.\n")
    verify(kit)
    print("ZIP plateforme et kit vérifiés ; aucune clé API incluse.")


if __name__ == "__main__":
    main()
