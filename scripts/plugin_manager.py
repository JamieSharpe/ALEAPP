import inspect
import os
import pkgutil
from scripts.plugin_base import ArtefactPlugin
from typing import List


class PluginManager:
    """
    Upon creation, this class will read the plugins package for modules
    that contain a class definition that is inheriting from the Plugin class
    """

    def __init__(self, plugin_package: str, plugin_base: ArtefactPlugin = ArtefactPlugin):
        """
        Constructor that initiates the reading of all available plugins
        when an instance of the PluginCollection object is created

        :param plugin_package: Python package to look into for plugins.
        :param plugin_base: What base class to search for to detect a plugin.
        """

        self.plugin_package = plugin_package
        self.plugin_base = plugin_base
        self.plugins: List[ArtefactPlugin] = []
        self.seen_paths = []
        print(f'Loading plugins under package {self.plugin_package}')
        self.load_plugins(self.plugin_package)

    def load_plugins(self, package_name):
        """
            Recursively walk the supplied package to retrieve all plugins.

        :param package_name:
        :return:
        """

        imported_package = __import__(package_name, fromlist=[''])

        for _, pluginname, ispkg in pkgutil.iter_modules(imported_package.__path__, imported_package.__name__ + '.'):
            if not ispkg:
                try:
                    plugin_module = __import__(pluginname, fromlist=[''])
                    class_members = inspect.getmembers(plugin_module, inspect.isclass)
                    for (_, c) in class_members:
                        # Only add classes that inherit plugin_base, but NOT the plugin_base itself
                        if issubclass(c, self.plugin_base) & (c is not self.plugin_base):
                            plugin = c()
                            print(f'\tLoaded plugin: {plugin.name} [{plugin.__class__.__module__}.{plugin.__class__.__name__}]')
                            self.plugins.append(plugin)

                except Exception as ex:
                    # print(f'Failed to import module: {pluginname}')
                    # print(f'\t{ex}')
                    pass

        # Now that we have looked at all the modules in the current package, start looking
        # recursively for additional modules in sub packages
        all_current_paths = []
        if isinstance(imported_package.__path__, str):
            all_current_paths.append(imported_package.__path__)
        else:
            all_current_paths.extend([x for x in imported_package.__path__])

        for package_path in all_current_paths:
            if package_path not in self.seen_paths:
                self.seen_paths.append(package_path)

                # Get all sub directory of the current package path directory
                child_packages = [p for p in os.listdir(package_path) if os.path.isdir(os.path.join(package_path, p))]

                # For each sub directory, apply the walk_package method recursively
                for child_package in child_packages:
                    self.load_plugins(f'{package_name}.{child_package}')
