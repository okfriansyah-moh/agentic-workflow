#!/usr/bin/env python3
"""Validate the adapted Humanizer skill bundle (not upstream plugin packaging)."""
from pathlib import Path
import re
import yaml
root=Path(__file__).resolve().parent.parent
text=(root/'SKILL.md').read_text()
m=re.match(r'^---\n(.*?)\n---\n',text,re.S)
assert m, 'Missing frontmatter'
meta=yaml.safe_load(m[1])
assert meta['name']=='humanizer'
assert len(meta['description'])<=1024
assert re.fullmatch(r'\d+\.\d+\.\d+',meta['metadata']['version'])
assert len(text.split())<=5500, 'Core exceeds upstream word budget'
numbers=[int(n) for n in re.findall(r'^### (\d+)\.',text,re.M)]
assert numbers==list(range(1,len(numbers)+1)) and numbers, 'Pattern numbering has gaps'
assert all(1<=int(n)<=len(numbers) for n in re.findall(r'§(\d+)',text)), 'Dangling pattern reference'
for target in re.findall(r'\]\(([^)]+)\)',text):
 if not target.startswith(('http:','https:','#')):assert (root/target).is_file(),target
assert (root/'LICENSE').is_file()
config=yaml.safe_load((root/'agents/openai.yaml').read_text())
assert '$humanizer' in config['interface']['default_prompt']
print('Adapted Humanizer bundle is valid: '+str(len(numbers))+' patterns, references and metadata verified')
