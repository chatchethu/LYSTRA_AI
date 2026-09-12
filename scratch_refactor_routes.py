import os
import re

api_dir = r"backend\api"

for filename in os.listdir(api_dir):
    if filename.endswith(".py"):
        filepath = os.path.join(api_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Update prefix in APIRouter
        content = re.sub(r'prefix="/api/([^/"]+)"', r'prefix="/api/v1/\1"', content)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

print("Updated prefixes.")
