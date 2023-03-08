import subprocess
from pathlib import Path

from . import p4, callbacks, template_plugin, utilities, plugin

svg_path = Path(Path(__file__), 'ui')

class CustomPlugin(plugin.CustomPluginBase):
	def __init__(self, plugin_id):
		super().__init__(plugin_id)

		p4.set_perforce()

	def _create_menu(self):
		self._add_menu_action("Template Plugin Menu Item")

	def _create_toolbar(self):
		self._add_toolbar_action("Template Plugin",
								  template_plugin.template_plugin)

	def _register_callbacks(self):
		beforeFileLoadedCallbackID = self._application().registerBeforeFileLoadedCallback(callbacks.onBeforeFileLoadedCallback)
		afterFileLoadedCallbackID = self._application().registerAfterFileLoadedCallback(callbacks.onAfterFileLoadedCallback)
		beforeFileSavedCallbackID = self._application().registerBeforeFileSavedCallback(callbacks.onBeforeFileSavedCallback)
		afterFileSavedCallbackID = self._application().registerAfterFileSavedCallback(callbacks.onAfterFileSavedCallback)
		self.__application_callbacks = [beforeFileLoadedCallbackID, afterFileLoadedCallbackID, beforeFileSavedCallbackID, afterFileSavedCallbackID]

def initializeSDPlugin():
	python_path = Path( str(utilities.get_registry_value('Path')).replace('"', ''), 'plugins/pythonsdk/python.exe' )
	subprocess.Popen(f"'{python_path}' -m pip install -r '{Path(__file__).parent}/requirements.txt'", shell=True)
	plugin.create(CustomPlugin)

def uninitializeSDPlugin():
	plugin.destroy(CustomPlugin)