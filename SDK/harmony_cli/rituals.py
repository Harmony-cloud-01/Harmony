# SDK/harmony_cli/rituals.py

import os
import yaml
from datetime import datetime
from .utils import log_event


# === CORE RITUALS ===

def restore_resonance():
    print("🌀 Harmonia: Resonance restored with Fractal Prime.")
    log_event("Restore resonance ritual invoked.")


# === RAG UTILITIES ===

def search_rag():
    try:
        from txtai.embeddings import Embeddings
        log_event("RAG search ritual invoked.")
        embeddings = Embeddings({"method": "transformers", "path": "sentence-transformers/all-MiniLM-L6-v2"})
        data = ["This is Harmony.", "Fractal Prime is the steward.", "Ollama runs local models."]
        embeddings.index([(uid, text, None) for uid, text in enumerate(data)])
        results = embeddings.search("Who is the steward?", 1)
        print(f"Top RAG result: {results}")
        log_event(f"RAG result: {results}")
    except Exception as e:
        print("Error running RAG search:", e)
        log_event(f"Error in search_rag: {e}")


# === CHRONICLE ===

def chronicle_entry():
    entry = input("Enter your Chronicle entry: ")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {entry}\n"
    path = "logs/chronicle.log"
    try:
        with open(path, "a") as f:
            f.write(line)
        print("✅ Chronicle entry added.")
        log_event(f"Chronicle entry: {entry}")
    except Exception as e:
        print("❌ Failed to write to Chronicle:", e)
        log_event(f"Chronicle write failure: {e}")


def read_chronicle(n=5):
    path = "logs/chronicle.log"
    try:
        with open(path, "r") as f:
            lines = f.readlines()
        print(f"\n=== Last {n} Chronicle Entries ===")
        for line in lines[-n:]:
            print(line.strip())
        log_event(f"Displayed last {n} Chronicle entries.")
    except Exception as e:
        print("Could not read Chronicle:", e)
        log_event(f"Error reading Chronicle: {e}")


def rag_chronicle():
    try:
        from txtai.embeddings import Embeddings
        log_event("RAG Chronicle search ritual invoked.")
        path = "logs/chronicle.log"
        with open(path, "r") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        if not lines:
            print("Chronicle is empty.")
            return
        query = input("Ask Harmony: ")
        embeddings = Embeddings({"method": "transformers", "path": "sentence-transformers/all-MiniLM-L6-v2"})
        embeddings.index([(uid, text, None) for uid, text in enumerate(lines)])
        results = embeddings.search(query, 3)
        print("\n=== Harmony Chronicle RAG Results ===")
        for idx, (uid, score) in enumerate(results, 1):
            print(f"{idx}. {lines[uid]}  (score: {score:.2f})")
        log_event(f"RAG Chronicle search: '{query}'")
    except Exception as e:
        print("Error running RAG Chronicle search:", e)
        log_event(f"Error in rag_chronicle: {e}")


# === MESH + SP REBINDING ===

def rebind_mesh(mesh_name):
    path = os.path.join("Codex", "Meshes", mesh_name)
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        title = data.get("title", mesh_name)
        print(f"✅ Rebound mesh: {title}")
        log_event(f"Rebound mesh: {title}")
    except Exception as e:
        print(f"❌ Error rebinding mesh {mesh_name}: {e}")
        log_event(f"Error rebinding mesh {mesh_name}: {e}")


def rebind_all_meshes():
    meshes_dir = os.path.join("Codex", "Meshes")
    try:
        for fname in os.listdir(meshes_dir):
            if fname.endswith(".yaml"):
                rebind_mesh(fname)
    except Exception as e:
        print(f"❌ Error rebinding all meshes: {e}")
        log_event(f"Error in rebind_all_meshes: {e}")


def rebind_sp(sp_file):
    path = os.path.join("Codex", "SPs", sp_file)
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        name = data.get("name", sp_file)
        print(f"✅ Rebound SP: {name}")
        log_event(f"Rebound SP: {name}")
    except Exception as e:
        print(f"❌ Error rebinding SP {sp_file}: {e}")
        log_event(f"Error rebinding SP {sp_file}: {e}")


def rebind_all_sps():
    sps_dir = os.path.join("Codex", "SPs")
    try:
        for fname in os.listdir(sps_dir):
            if fname.endswith(".yaml"):
                rebind_sp(fname)
    except Exception as e:
        print(f"❌ Error rebinding SPs: {e}")
        log_event(f"Error in rebind_all_sps: {e}")


# === LINK VALIDATION ===

import os
import yaml

def validate_links():
    print("\n🔍 Validating agent links in meshes...\n")
    mesh_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Codex", "Meshes")
    sp_dir = os.path.join(os.path.dirname(__file__), "..", "..", "Codex", "SPs")

    # Normalize known SP names from filenames
    known_agents = set()
    for sp_file in os.listdir(sp_dir):
        if sp_file.endswith(".yaml"):
            name = os.path.splitext(sp_file)[0]
            name_normalized = name.replace("-", " ").lower()
            known_agents.add(name_normalized)

    errors = 0
    for filename in os.listdir(mesh_dir):
        if not filename.endswith(".yaml"):
            continue
        path = os.path.join(mesh_dir, filename)
        with open(path, "r") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"❌ Error parsing {filename}: {e}")
                errors += 1
                continue
            if not isinstance(data, dict):
                print(f"⚠️ Skipping non-dict YAML: {filename}")
                continue

        mesh_agents = data.get("agents", [])
        for raw_agent in mesh_agents:
            # Extract just the name (before any parentheses)
            name_part = raw_agent.split("(")[0].strip()
            normalized = name_part.replace("-", " ").lower()
            if normalized not in known_agents:
                print(f"❌ {filename} references unknown agent: {raw_agent}")
                errors += 1

    if errors == 0:
        print("\n✅ All mesh agent references valid.")
    else:
        print(f"\n⚠️ {errors} invalid agent references found.")
