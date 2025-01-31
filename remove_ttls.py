import glob
import os

files = glob.glob("./*.ttl")
for x in files:
    print(f"removing {x}")
    os.unlink(x)

print(f"done removing {len(files)} files")
