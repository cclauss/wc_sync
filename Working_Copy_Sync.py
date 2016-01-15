#        1         2         3         4         5         6         7
# 34567890123456789012345678901234567890123456789012345678901234567890123456789

import base64
import console
import dialogs
import editor
import errno
import json
import keychain
import os
import shutil
import sys
import urllib
import webbrowser
import zipfile
from collections import OrderedDict

DOCS_DIR = os.path.expanduser('~/Documents')
INSTALL_PATH = os.path.relpath(os.path.dirname(__file__), DOCS_DIR)

def get_key_from_keychain(service='wcSync', account='xcallback'):
	''' Retrieve the working copy key or prompt for a new one. '''
	key = keychain.get_password(service, account)
	if not key:
		key = console.password_alert('Working Copy Key')
		keychain.set_password(service, account, key)
	return key

class WorkingCopySync():
	def __init__(self):
		self.repo, self.path = self._get_repo_info()

	@property
	def full_path(self):
		return os.path.join(self.repo, self.path)

	def _get_repo_info(self):
		''' Get the relative path and remove the leading / '''
		fullPath = editor.get_path()[len(DOCS_DIR)+1:]
		assert '/' in fullPath, '{} must be in a directory.'.format(fullPath)
		repo, path = fullPath.split('/', 1)
		return repo, path

	def _send_to_working_copy(self, action, payload, x_callback_enabled=True):
		x_callback = 'x-callback-url/' if x_callback_enabled else ''
		payload['key'] = get_key_from_keychain('wcSync', 'xcallback')
		payload = urllib.urlencode(payload).replace('+', '%20')
		fmt = 'working-copy://{x_callback}{action}/?{payload}'
		url = fmt.format(x_callback=x_callback, action=action, payload=payload)
		webbrowser.open(url)

	def _get_repo_list(self):
		console.hud_alert('This may take a few seconds.', 'error')
		action = 'repos'
		fmt = 'pythonista://{}/Working_Copy_Sync.py?action=run&argv=repo_list&argv='
		payload = {
			'x-success': fmt.format(INSTALL_PATH)
		}
		self._send_to_working_copy(action, payload)

	def copy_repo_from_wc(self, repo_list=None):
		''' copy a repo to the local filesystem
		'''
		if not repo_list:
			self._get_repo_list()
		else:
			repo_name = dialogs.list_dialog(title='Select repo', items=repo_list)
			if repo_name:
				action = 'zip'
				fmt = 'pythonista://{}/Working_Copy_Sync.py?action=run&argv=copy_repo&argv={}&argv='
				payload = {
					'repo': repo_name,
					'x-success': fmt.format(INSTALL_PATH, repo_name)
				}
				self._send_to_working_copy(action, payload)

	def _push_file_to_wc(self, path, contents):
		action = 'write'
		payload = {
			'repo': self.repo,
			'path': path,
			'text': contents,
			'x-success': 'pythonista://{}/{}?'.format(self.repo, path)
		}
		self._send_to_working_copy(action, payload)

	def push_current_file_to_wc(self):
		self._push_file_to_wc(self.path, editor.get_text())

	def push_pyui_to_wc(self):
		pyui_path, pyui_contents = self._get_pyui_contents_for_file()
		if not pyui_contents:
			msg = "No PYUI file associated. Now say you're sorry."
			console.alert(msg, button1="I'm sorry.", hide_cancel_button=True)
		else:
			self._push_file_to_wc(pyui_path, pyui_contents)

	def _get_pyui_contents_for_file(self):
		rel_pyui_path = self.path + 'ui'
		full_pyui_path = os.path.join(DOCS_DIR, self.repo, rel_pyui_path)
		try:
			with open(full_pyui_path) as f:
				return rel_pyui_path, f.read()
		except IOError:
			return None, None

	def overwrite_with_wc_copy(self):
		action = 'read'
		fmt = 'pythonista://{}/Working_Copy_Sync.py?action=run&argv=overwrite_file&argv={}&argv='
		payload = {
			'repo': self.repo,
			'path': self.path,
			'base64': '1',
			'x-success': fmt.format(INSTALL_PATH, self.full_path)
		}
		self._send_to_working_copy(action, payload)

	def open_repo_in_wc(self):
		action = 'open'
		payload = {
			'repo': self.repo
		}
		self._send_to_working_copy(action, payload)

	def present(self):
		actions = OrderedDict()
		actions['CLONE 	- Copy repo from Working Copy'] = self.copy_repo_from_wc
		actions['FETCH 	- Overwrite file with WC version'] = self.overwrite_with_wc_copy
		actions['PUSH 		- Send file to WC'] = self.push_current_file_to_wc
		actions['PUSH UI 	- Send associated PYUI to WC'] = self.push_pyui_to_wc
		actions['OPEN 		- Open repo in WC'] = self.open_repo_in_wc
		action = dialogs.list_dialog(title='Choose action', items=actions.keys())
		if action:
			actions[action]()

	def urlscheme_copy_repo_from_wc(self, path, b64_contents):
		dest = os.path.join(DOCS_DIR, path)
		try:
			os.makedirs(dest)
		except OSError as e:
			if e.errno != errno.EEXIST:
				raise e
			console.alert('Overwriting existing directory', button1='Continue')
			shutil.rmtree(dest)
		tmp_zip_location = INSTALL_PATH + 'repo.zip'
		zip_file_location = os.path.join(DOCS_DIR, tmp_zip_location)
		with open(zip_file_location, 'w') as out_file:
			out_file.write(base64.b64decode(b64_contents))
		with zipfile.ZipFile(zip_file_location) as in_file:
			in_file.extractall(dest)
		os.remove(zip_file_location)
		console.hud_alert(path + ' Downloaded.')

	def urlscheme_overwrite_file_with_wc_copy(self, path, b64_contents):
		full_file_path = os.path.join(DOCS_DIR, path)
		try:
			os.makedirs(full_file_path)
		except OSError as e:
			if e.errno != errno.EEXIST:
				raise e
		with open(full_file_path, 'w') as f:
			f.write(base64.b64decode(b64_contents))
		editor.open_file(path)
		console.hud_alert(path +' Updated.')


def main(url_action=None, url_args=None):
	wc = WorkingCopySync()
	if not url_action:
		wc.present()
	elif url_action == 'copy_repo':
		wc.urlscheme_copy_repo_from_wc(url_args[0], url_args[1])
	elif url_action == 'overwrite_file':
		wc.urlscheme_overwrite_file_with_wc_copy(url_args[0], url_args[1])
	elif url_action == 'repo_list':
		repo_list = [repo['name'] for repo in json.loads(url_args[0])]
		wc.copy_repo_from_wc(repo_list)
	else:
		msg = "Not a valid URL scheme action. Now say you're sorry."
		console.alert(msg, button1="I'm sorry.", hide_cancel_button=True)

if __name__ == "__main__":
	url_action, url_args = None, None
	if len(sys.argv) > 1:
		url_action = sys.argv[1]
		url_args = sys.argv[2:]
	main(url_action, url_args)
