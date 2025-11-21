import sys
import os

# Add parent dir to path so we can import the package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'prabhupada_os')))

import prabhupada

print("🕉️  Initializing Prabhupada Library...\n")

# 1. Simple Usage (Default Dummy Provider)
query = "intelligence devotion"
print(f"❓ Asking: '{query}'\n")

response = prabhupada.ask(query)

print(f"🧠 Smriti ({response.meta['provider']}):")
print(f"   {response.smriti}\n")

print(f"📖 Sruti ({len(response.sruti)} verses):")
for verse in response.sruti:
    print(f"   [{verse['id']}] {verse['translation'][:60]}...")

print("\n✨ Done! Pure Python. No APIs. Plug and Play.")
