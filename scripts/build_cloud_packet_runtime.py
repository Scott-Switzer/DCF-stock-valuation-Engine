"""Small generated Python runtime; no data, package install, or local financial computation."""
from pathlib import Path
import shutil
import hashlib
root=Path(__file__).resolve().parents[1]
out=root/'cloud_packet_runtime';out.mkdir(exist_ok=True)
for name in ['dcf_code.py','dcf_loader.py','storage.py','ppe_packets.py','sec_first.py','tax_policy.py','accounting_policy.py','sec_enrichment.py']:
 shutil.copyfile(root/name,out/name)
shutil.copyfile(root/'deploy/valuation-completion/packet_worker.py',out/'worker.py')
digest=hashlib.sha256()
for path in sorted(out.glob('*.py')):
 if path.name!='runtime_manifest.py':
  digest.update(path.name.encode());digest.update(path.read_bytes())
(out/'runtime_manifest.py').write_text('VERSION='+repr(digest.hexdigest())+'\n')

# Wrangler resolves vendored packages relative to the config directory.
modules=root/'deploy/valuation-completion/python_modules'
if not modules.exists():
 if not (root/'python_modules').exists():
  raise RuntimeError('Install the root locked Python Worker dependencies before deployment')
 modules.symlink_to('../../python_modules', target_is_directory=True)
