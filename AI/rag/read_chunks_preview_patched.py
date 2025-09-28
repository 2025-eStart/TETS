import json, re

def decode_slashC_encoding(s: str) -> str:
    return re.sub(r"/C(\d{1,3})", lambda m: chr(int(m.group(1))), s)

def main():
    path = "chunks.jsonl"
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i < 3:
                data = json.loads(line)
                raw = data.get("content", "")
                fixed = decode_slashC_encoding(raw)
                print(f"Chunk {i}:", fixed[:200], "...")

if __name__ == "__main__":
    main()
