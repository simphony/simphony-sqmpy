"""
    sqmpy.core
    ~~~~~~~~~~

    Provides some of core functions for the application, such
    as component registration.
"""
__author__ = 'Mehdi Sadeghi'


class SQMException(Exception):
    """
    Generic exception class
    """


class SQMComponent(object):
    """
    Represents a base class for all components in the system.
    """

    def __init__(self, name):
        self._name = name

    def get_name(self):
        return self._name


class CoreManager(SQMComponent):
    """
    Core services
    """

    def __init__(self):
        super(CoreManager, self).__init__('CORE_MANAGER')
        self._components = {}

    def register(self, component):
        """
        Register a new component
        @component: instance of component class
        """
        assert isinstance(component, SQMComponent)
        if component.get_name() not in self._components:
            self._components[component.get_name()] = component

    def get_component(self, name):
        """
        Get a component
        @name: component name
        """
        if name in self._components:
            return self._components[name]
        else:
            raise SQMException("Component %s not found." % name)

    def load_components(self):
        """
        Tries to load all available components in directory tree.
        """
        #logging.debug("Loading components")

core_services = CoreManager()