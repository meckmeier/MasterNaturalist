import re
from pathlib import Path

bootstrap_prefixes = (
    "container", "row", "col",
    "m", "p", "d", "justify", "align",
    "btn", "card", "nav", "text", "bg", "w", "h"
)

def is_bootstrap(cls):
    return (
        cls.startswith(bootstrap_prefixes)
        or "-" in cls and any(cls.startswith(x) for x in ["m", "p"])
    )
classes = set()

pattern = re.compile(r'class\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)

for file in Path('.').rglob('*.html'):
    content = file.read_text(encoding='utf-8', errors='ignore')
    
    matches = pattern.findall(content)
    
    for match in matches:
        for cls in match.split():
            cls = cls.strip()
            
            # skip template variables
            if "{{" in cls or "}}" in cls:
                continue
            
            classes.add(cls)

for cls in sorted(classes):
    if is_bootstrap(cls):
        print(f"BOOTSTRAP: {cls}")
    else:
        print(f"CUSTOM: {cls}")
        