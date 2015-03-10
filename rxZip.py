import zipfile
import base64
import os
import console
import sys
import errno

try:
    _, path, data = sys.argv
except ValueError:
    fmt = 'Missing commandline parameters: {} path data'
    sys.exit(fmt.format(__file__.rpartition('/')[2].rstrip('.py')))

ZIP_FILE = 'wc_sync/repo.zip'

try:
	os.makedirs(os.path.join(os.path.expanduser('~/Documents'), path))
except OSError, e:
	if e.errno != errno.EEXIST:
		raise e
	console.alert('Overwriting existing directory',button1='Continue')

zipF = os.path.join(os.path.expanduser('~/Documents'), ZIP_FILE)
with open(zipF, 'w') as zip:
	zip.write(base64.b64decode(data))
	
z = zipfile.ZipFile(zipF)	
z.extractall(os.path.join(os.path.expanduser('~/Documents'), path))
os.remove(zipF)
console.hud_alert(path + ' Downloaded')
