import os, subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from . import utilities
from PySide2 import QtWidgets


def simple_dialog(text):
	dialog = QtWidgets.QMessageBox()
	dialog.setText(text)
	dialog.setIcon(QtWidgets.QMessageBox.Warning)
	dialog.setStandardButtons(QtWidgets.QMessageBox.Yes)
	dialog.exec_()


def xml_create_element( parent, tag, text= ' ', attrib={} ):
	new_element = ET.SubElement(parent, tag, attrib)
	new_element.text = text
	return new_element


def get_perforce_info():
	try:
		client = subprocess.check_output('p4 -Ztag -F %clientName% info').decode("utf-8").strip()
		root = Path(subprocess.check_output('p4 -Ztag -F %clientRoot% info').decode("utf-8").strip()).as_posix()
		if client == '*unknown*':
			simple_dialog('Perforce client or root not found. \nPlease check your Perforce connection.')
			return (None, None)
		return(client, str(root))
	except subprocess.CalledProcessError:
		simple_dialog('Perforce client or root not found. \nPlease check your Perforce connection.')
		return (None, None)


def create_workspace_tree(user_project, user_project_tree, user_workspace, client, root, perforce_actions, python_path):
	for child in list(user_workspace):
		user_workspace.remove(child)	
	
	xml_create_element( user_workspace, 'size', text='1' )
	workspace_index = xml_create_element( user_workspace, '_1', attrib={'prefix':'_'})
	workspace = xml_create_element( workspace_index, 'worskspace')
	xml_create_element( workspace, 'path', text=root)
	xml_create_element( workspace, 'name', text=client)
	xml_create_element( workspace_index, 'is_enabled', text='true')
	workspace_interpreter = xml_create_element( workspace_index, 'interpreters')
	xml_create_element( workspace_interpreter, 'size', text='1')
	workspace_interpreter_index = xml_create_element( workspace_interpreter, '_1', attrib={'prefix':'_'})
	xml_create_element( workspace_interpreter_index, 'path',  text=str( python_path ))
	xml_create_element( workspace_interpreter_index, 'ext',  text='py')
	user_actions = xml_create_element( workspace_index, 'actions')
	xml_create_element( user_actions, 'size', text=str(len(perforce_actions)))
	for index, (label, id) in enumerate(perforce_actions.items(), start=1):
		user_action_index = xml_create_element( user_actions, f'_{index}', attrib={'prefix':'_'})
		xml_create_element( user_action_index, 'script_path', text= str( Path(Path(__file__).parents[2], 'version_control/perforce.py' )))
		xml_create_element( user_action_index, 'label', text=label)
		xml_create_element( user_action_index, 'id', text=id)

	user_project_tree.write(user_project)
	widgets.simple_dialog('Perforce workspace created. Please restart Substance Designer.')


def set_perforce():
	client, root = get_perforce_info()
	
	if client is None or root is None:
		return

	python_path = Path( str(utilities.get_registry_value('Path')).replace('"', ''), 'plugins/pythonsdk/python.exe' )
	perforce_actions = { 'Get Status' : 'get_status', 
						 'Get Last Version' : 'get_last_version', 
						 'Revert' : 'revert', 
						 'Submit' : 'submit', 
						 'Checkout' : 'checkout', 
						 'Add' : 'add' }
	
	user_project = Path( os.getenv('LOCALAPPDATA'), 'Adobe/Adobe Substance 3D Designer', 'user_project.sbsprj')
	user_project_tree = ET.parse(user_project)
	user_workspace = user_project_tree.find('preferences').find('versioncontrol').find('workspaces')	

	try:
		if user_workspace.find('_1').find('is_enabled').text == 'false':
			create_workspace_tree(user_project, user_project_tree, user_workspace, client, root, perforce_actions, python_path)
	except AttributeError:
		create_workspace_tree(user_project, user_project_tree, user_workspace, client, root, perforce_actions, python_path)