import sd
import weakref
from functools import partial
from PySide2 import QtCore, QtWidgets

module_data = {'plugins': {}, 'toolbars': {}}

class CustomPluginBase(QtCore.QObject):
    __CALLBACK_TESTING = False
    __MENU_ID = "CustomTools.menu"
    __MENU_TITLE = "Custom"
    __TOOLBAR_ID = "CustomTools.toolbar"
    __TOOLBAR_NAME = "Custom Shelf"

    def __init__(self, plugin_id, parent=None):
        super().__init__(parent)
        self.__current_graph_view_id = None
        self.__graph_created_callback_id = None
        self.__menu_actions = []
        self.__plugin_id = plugin_id
        self.__toolbar_actions = []
        self.__application = sd.getContext().getSDApplication()
        self.__ui_manager = sd.getContext().getSDApplication().getQtForPythonUIMgr()   
        self.__application_callbacks = []     
        self.destroyed.connect(partial(self.__on_destroyed))
        if self.__ui_manager:
            self.__graph_created_callback_id = self.__ui_manager.registerGraphViewCreatedCallback(partial(self.__on_graph_created, ui_mrg=self.__ui_manager))
            self._create_menu()
            self._register_callbacks()

    def __on_destroyed(self):
        for graph_view_id in module_data['toolbars']:
            toolbar = module_data['toolbars'][graph_view_id]()
            if toolbar:
                for action in self.__toolbar_actions:
                    if action in toolbar.actions():
                        toolbar.removeAction(action)
                if len(toolbar.actions()) <= 0:
                    toolbar.deleteLater()
        menu = self.__ui_manager.findMenuFromObjectName(self.__MENU_ID)
        if menu:
            for action in self.__menu_actions:
                if action in menu.actions():
                    menu.removeAction(action)
            if len(menu.actions()) <= 0:
                self.__ui_manager.deleteMenu(self.__MENU_ID)
        if self.__application_callbacks:
            for callback in self.__application_callbacks:
                self.__application.unregisterCallback(callback)            
        if self.__graph_created_callback_id:
            self.__ui_manager.unregisterCallback(self.__graph_created_callback_id)
        self.__current_graph_view_id = None
        self.__graph_created_callback_id = None
        self.__menu_actions = []
        self.__plugin_id = None
        self.__toolbar_actions = []
        self.__application = None
        self.__ui_manager = None

    def __on_graph_created(self, graph_view_id, ui_mrg):
        self.__current_graph_view_id = graph_view_id
        self._create_toolbar()
        self.__current_graph_view_id = None

    def __on_toolbar_destroyed(self, graph_view_id):
        del module_data['toolbars'][graph_view_id]

    def __test_callback(self, text):
        debug_text = text
        if self.__current_graph_view_id:
            debug_text = f'{text} ({self.__current_graph_view_id})' 
        def callback():
            print(f'Custom Plugin: "{debug_text}" Callback')
        return callback

    def __toolbar_for_current_graph(self):
        toolbar = None
        if self.__current_graph_view_id:
            if not self.__current_graph_view_id in module_data['toolbars']:
                new_toolbar = QtWidgets.QToolBar(self.__ui_manager.getMainWindow())
                new_toolbar.setObjectName(f'{self.__TOOLBAR_ID}.{self.__current_graph_view_id}')
                new_toolbar.setToolTip(self.__TOOLBAR_NAME)
                new_toolbar.destroyed.connect(partial(self.__on_toolbar_destroyed, self.__current_graph_view_id))
                module_data['toolbars'][self.__current_graph_view_id] = weakref.ref(new_toolbar)
                self.__ui_manager.addToolbarToGraphView(self.__current_graph_view_id, new_toolbar, tooltip=new_toolbar.toolTip())
            if self.__current_graph_view_id in module_data['toolbars']:
                toolbar = module_data['toolbars'][self.__current_graph_view_id]()
        return toolbar
    
    def _add_menu_action(self, action_label, action_icon=None, action_callback=None):
        action = None
        if action_label:
            menu = self.__ui_manager.findMenuFromObjectName(self.__MENU_ID)
            if not menu:
                menu = self.__ui_manager.newMenu(menuTitle=self.__MENU_TITLE, objectName=self.__MENU_ID)
            if menu:
                action = QtWidgets.QAction(self)
                action.setText(action_label)
                menu.addAction(action)
                if self.__CALLBACK_TESTING:
                    action.triggered.connect(self.__test_callback(action_label))
                elif action_callback:
                    action.triggered.connect(action_callback)
                if action_icon:
                    action.setIcon(action_icon)
        if action:
            self.__menu_actions.append(action)
        return action

    def _add_toolbar_action(self, action_label, action_icon=None, action_callback=None, action_tooltip=None):
        action = None
        if action_label:
            toolbar = self.__toolbar_for_current_graph()
            if toolbar:
                action = QtWidgets.QAction(self)
                action.setText(action_label)
                toolbar.addAction(action)
                if self.__CALLBACK_TESTING:
                    action.triggered.connect(self.__test_callback(action_label))
                elif action_callback:
                    action.triggered.connect(action_callback)
                if action_icon:
                    action.setIcon(action_icon)
                if action_tooltip is not None:
                    action.setToolTip(action_tooltip)
                else:
                    action.setToolTip(action_label)
        if action:
            self.__toolbar_actions.append(action)
        return action

    def _create_menu(self):
        pass

    def _create_toolbar(self):
        pass

    def _register_callbacks(self):
        pass
    
    def _ui_manager(self):
        return self.__ui_manager

    def _application(self):
        return self.__application

def create(plugin_class):
    plugin_id = str(plugin_class)
    if not plugin_id in module_data['plugins']:
        module_data['plugins'][plugin_id] = plugin_class(plugin_id)

def destroy(plugin_class):
    plugin_id = str(plugin_class)
    if plugin_id in module_data['plugins']:
        module_data['plugins'][plugin_id].deleteLater()
        del module_data['plugins'][plugin_id]