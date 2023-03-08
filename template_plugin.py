import tempfile
import sd

temp_directory = tempfile.TemporaryDirectory()

def template_plugin():
	app = sd.getContext().getSDApplication()
	ui_mrg = app.getQtForPythonUIMgr()