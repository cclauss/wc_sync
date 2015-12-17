import ui
import editor
import os
import console
import webbrowser as wb
import urllib
import base64
import keychain

def is_ipad():
	''' Helper method to determine if we are on an 
			iPad or an iPhone
	'''
	width, height = ui.get_screen_size()
	if width >= 768:
		return True
	else:
		return False
		
def close_view(sender):
	''' Helper method to put a close (X) button in 
			the pyui view
	'''
	sender.superview.close()

class WorkingCopySync():
	
	def __init__(self):
		self.key = self._get_key()
		self.install_path = self._find_install_path()
		self.view = ui.load_view('Working_Copy_Sync')
		self.repo, self.path = self._get_repo_info()
		
	def _get_key(self):
		''' Retrieve the working copy key or prompt for a new one. 
		'''
		key = keychain.get_password('wcSync', 'xcallback')
		if not key:
			key = console.password_alert('Working Copy Key')
			keychain.set_password('wcSync', 'xcallback', key)
		return key
	
	def _find_install_path(self):
		''' Dynamically find the installation path for the script
		'''
		app_dir = os.path.realpath(os.path.abspath(os.path.dirname(__file__)))
		home_dir = os.path.join(os.environ['HOME'], 'Documents')
		return os.path.relpath(app_dir, home_dir)
	
	def _get_repo_info(self):
		documentsDir = os.path.expanduser('~/Documents')
		info = editor.get_path()
		fullPath = info[len(documentsDir)+1:] # get the relative path and remove the leading /
		path = fullPath.split('/',1)[1]
		repo = fullPath.split('/',1)[0]
		return repo, path			
		
	def _send_to_working_copy(self, action, payload, x_callback_enabled=True):
		payload['key'] = self.key
		if x_callback_enabled:
			url = 'working-copy://x-callback-url/{action}/?{payload}'
		else:
			url = 'working-copy://{action}/?{payload}'
		urlencoded_payload = urllib.urlencode(payload).replace('+', '%20')
		url = url.format(action=action, payload=urlencoded_payload)
		wb.open(url)

	def copy_repo_from_wc(self, sender):
		''' copy a repo to the local filesystem 
		'''
		repo_name = console.input_alert('Repo name')
		if not repo_name:
			console.alert('Invalid repo name')
		else:
			action = 'zip'
			payload = {
				'repo': repo_name,
				'x-success': 'pythonista://{install_path}/rxZip.py?action=run&argv={repo_name}&argv='.format(install_path=self.install_path, repo_name=repo_name)
			}
			self._send_to_working_copy(action, payload)
		sender.superview.close()		
		
	def _push_file_to_wc(self, path, contents):
		action = 'write'
		payload = {
			'repo': self.repo,
			'path': path,
			'text': contents,
			'x-success': 'pythonista://{repo}/{path}?'.format(repo=self.repo, path=path)
		}
		self._send_to_working_copy(action, payload)
			
	def push_current_file_to_wc(self, sender):
		self._push_file_to_wc(self.path, editor.get_text())
		sender.superview.close()
		
	def push_pyui_to_wc(self, sender):
		pyui_path, pyui_contents = self._get_pyui_contents_for_file()
		if not pyui_contents:
			console.alert('No PYUI file associated. Now say you\'re sorry.' ,button1='I\'m sorry.', hide_cancel_button=True)
		else:
			self._push_file_to_wc(pyui_path, pyui_contents)
			sender.superview.close()
		
	def _get_pyui_contents_for_file(self):
		rel_pyui_path = self.path + 'ui'
		full_pyui_path = os.path.join(os.path.expanduser('~/Documents'), os.path.join(self.repo, rel_pyui_path))
		try:
			with open(full_pyui_path) as f:
				return rel_pyui_path, f.read()
		except IOError:
			return None, None
			
	def overwrite_with_wc_copy(self, sender):
		action = 'read'
		payload = {
			'repo': self.repo,
			'path': self.path,
			'base64': '1',
			'x-success': 'pythonista://{install_path}/rxFile.py?action=run&argv={full_path}&argv='.format(install_path=self.install_path, full_path=os.path.join(self.repo, self.path))
		}
		self._send_to_working_copy(action, payload)
		sender.superview.close()		
		
	def open_repo_in_wc(self, sender):
		action = 'open'
		payload = {
			'repo': self.repo
		}
		self._send_to_working_copy(action, payload)
		sender.superview.close()

	def present(self):
		try:
			if is_ipad():
				self.view.present('sheet', hide_title_bar=True)
			else:
				self.view.present(hide_title_bar=True)
		except KeyboardInterrupt:
			pass		
			

def main():
	wc = WorkingCopySync()
	wc.present()

if __name__ == "__main__":
	main()