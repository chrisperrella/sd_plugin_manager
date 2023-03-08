import winreg, os
import pathlib as Path
import xml.etree.ElementTree as ET

def get_registry_value( keyname ):
	keyname_value = None
	designer_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Adobe Substance 3D Designer.exe'
	registry_connection = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
	try:
		with winreg.OpenKey(registry_connection, designer_key, winreg.KEY_READ) as key:
			keyname_value = winreg.QueryValueEx(key, keyname)[0]
	except FileNotFoundError:
		pass
	return keyname_value


def append_sbsprj_configuration( sbsprj_name ):
	configuration_path = Path( os.getenv('LOCALAPPDATA'), 'Adobe/Adobe Substance 3D Designer', 'default_configuration.sbscfg')
	configuration_tree = ET.parse(configuration_path)	
	projectfiles_index = configuration_tree.find('*/projectfiles').find('size').text
	if projectfiles_index == 0:
		configuration_tree.find('*/projectfiles').find('size').text = 1
		index = ET.SubElement(configuration_tree.find('*/projectfiles'), '_1', prefix='_')
		path = ET.SubElement(index, 'path')
		path.text = Path(Path(__file__).parents[2], sbsprj_name)
		configuration_tree.write(configuration_path)