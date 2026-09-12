import json
from backend.generation.response_normalizer import normalize
r = normalize({" blocks\: [{\text\: \It can be really tough\}]})
print(r.type)
print(repr(r.content))
print([b.model_dump() for b in r.blocks])
