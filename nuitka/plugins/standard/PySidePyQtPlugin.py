#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Standard plug-in to make PyQt and PySide work well in standalone mode.

To run properly, these need the Qt plug-ins copied along, which have their
own dependencies.
"""

import os
from abc import abstractmethod

from nuitka.containers.oset import OrderedSet
from nuitka.freezer.IncludedDataFiles import makeIncludedDataFile
from nuitka.freezer.IncludedEntryPoints import makeDllEntryPoint
from nuitka.Options import isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.plugins.Plugins import getActiveQtPlugin
from nuitka.PythonVersions import python_version
from nuitka.utils.FileOperations import getFileList, listDir
from nuitka.utils.ModuleNames import ModuleName
from nuitka.utils.SharedLibraries import locateDLL
from nuitka.utils.Utils import isWin32Windows

# Use to detect the Qt plugin that is active and check for conflicts.
_qt_binding_names = ("PySide", "PySide2", "PySide6", "PyQt4", "PyQt5", "PyQt6")

# Detect usage of "wx" and warn/exclude that as well. Add more here as
# necessary.
_other_gui_binding_names = ("wx",)


def getQtPluginNames():
    return tuple(qt_binding_name.lower() for qt_binding_name in _qt_binding_names)


class NuitkaPluginQtBindingsPluginBase(NuitkaPluginBase):
    # For overload in the derived bindings plugin.
    binding_name = None

    def __init__(self, qt_plugins, no_qt_translations):
        self.qt_plugins = OrderedSet(x.strip().lower() for x in qt_plugins.split(","))
        self.no_qt_translations = no_qt_translations

        self.webengine_done_binaries = False
        self.webengine_done_data = False
        self.qt_plugins_dirs = None

        self.binding_package_name = ModuleName(self.binding_name)

        # Allow to specify none.
        if self.qt_plugins == set(["none"]):
            self.qt_plugins = set()

        # Prevent the list of binding names from being incomplete, it's used for conflicts.
        assert self.binding_name in _qt_binding_names, self.binding_name

        # Also lets have consistency in naming.
        assert self.plugin_name in getQtPluginNames()

        active_qt_plugin_name = getActiveQtPlugin()

        if active_qt_plugin_name is not None:
            self.sysexit(
                "Error, confliciting plugin '%s', you can only have one enabled."
                % active_qt_plugin_name
            )

        self.warned_about = set()

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--include-qt-plugins",
            action="store",
            dest="qt_plugins",
            default="sensible",
            help="""\
Which Qt plugins to include. These can be big with dependencies, so
by default only the sensible ones are included, but you can also put
"all" or list them individually. If you specify something that does
not exist, a list of all available will be given.""",
        )

        group.add_option(
            "--noinclude-qt-translations",
            action="store",
            dest="no_qt_translations",
            default=False,
            help="""\
Include Qt translations with QtWebEngine if used. These can be a lot
of files that you may not want to be included.""",
        )

    @abstractmethod
    def _getQmlTargetDir(self):
        """Where does the Qt bindings package expect the QML files."""

    @abstractmethod
    def _getResourcesTargetDir(self):
        """Where does the Qt bindings package expect the resources files."""

    def _getTranslationsTargetDir(self, filename_relative):
        """Where does the Qt bindings package expect the translation files."""
        if "PySide" in self.binding_name:
            os.path.join(
                self.binding_name,
                "translations",
            )
        else:
            if "qtwebengine_locales" in filename_relative:
                return "qtwebengine_locales"
            else:
                return "translations"

    def getQtWebEngineProcessDir(self, package_dir):
        """Where to find the QtWebEngineProcess executable."""
        if isWin32Windows():
            if "PySide" in self.binding_name:
                return package_dir
            elif self.binding_name == "PyQt5":
                return os.path.join(package_dir, "Qt5", "bin")
            elif self.binding_name == "PyQt6":
                # TODO: PyQt6 is maybe the same?
                return os.path.join(package_dir, "Qt6", "bin")
            else:
                assert False
        else:
            # TODO verify this for non-Windows, esp. macOS
            return os.path.join(package_dir, "libexec")

    def getQtPluginsSelected(self):
        # Resolve "sensible on first use"
        if "sensible" in self.qt_plugins:
            # Most used ones with low dependencies.
            self.qt_plugins.update(
                tuple(
                    family
                    for family in (
                        "imageformats",
                        "iconengines",
                        "mediaservice",
                        "printsupport",
                        "platforms",
                        "platformthemes",
                        "styles",
                    )
                    if self.hasPluginFamily(family)
                )
            )

            # OpenGL rendering, maybe should be something separate.
            if self.hasPluginFamily("xcbglintegrations"):
                self.qt_plugins.add("xcbglintegrations")

            self.qt_plugins.remove("sensible")

            # Make sure the above didn't detect nothing, which would be
            # indicating the check to be bad.
            assert self.qt_plugins

        return self.qt_plugins

    def hasQtPluginSelected(self, plugin_name):
        selected = self.getQtPluginsSelected()

        return "all" in selected or plugin_name in selected

    def _getQtInformation(self):
        # This is generic, and therefore needs to apply this to a lot of strings.
        def applyBindingName(template):
            return template % {"binding_name": self.binding_name}

        setup_codes = applyBindingName(
            r"""
import os
import %(binding_name)s.QtCore
"""
        )

        info = self.queryRuntimeInformationMultiple(
            info_name=applyBindingName("%(binding_name)s_info"),
            setup_codes=setup_codes,
            values=(
                (
                    "library_paths",
                    applyBindingName(
                        "%(binding_name)s.QtCore.QCoreApplication.libraryPaths()"
                    ),
                ),
                (
                    "guess_path1",
                    applyBindingName(
                        "os.path.join(os.path.dirname(%(binding_name)s.__file__), 'plugins')"
                    ),
                ),
                (
                    "guess_path2",
                    applyBindingName(
                        "os.path.join(os.path.dirname(%(binding_name)s.__file__), '..', '..', '..', 'Library', 'plugins')"
                    ),
                ),
                (
                    "version",
                    applyBindingName(
                        "%(binding_name)s.__version_info__"
                        if "PySide" in self.binding_name
                        else "%(binding_name)s.QtCore.PYQT_VERSION_STR"
                    ),
                ),
                (
                    "nuitka_patch_level",
                    applyBindingName(
                        "getattr(%(binding_name)s, '_nuitka_patch_level', 0)"
                    ),
                ),
                (
                    "translations_path",
                    applyBindingName(
                        """\
%(binding_name)s.QtCore.QLibraryInfo.location(%(binding_name)s.QtCore.QLibraryInfo.TranslationsPath)"""
                    ),
                ),
            ),
        )

        if info is None:
            self.sysexit("Error, it seems '%s' is not installed." % self.binding_name)

        return info

    def _getBindingVersion(self):
        """Get the version of the binding in tuple digit form, e.g. (6,0,3)"""
        return self._getQtInformation().version

    def _getNuitkaPatchLevel(self):
        """Does it include the Nuitka patch, i.e. is a self-built one with it applied."""
        return self._getQtInformation().nuitka_patch_level

    def _getTranslationsPath(self):
        """Get the path to the Qt translations."""
        return self._getQtInformation().translations_path

    def getQtPluginDirs(self):
        if self.qt_plugins_dirs is not None:
            return self.qt_plugins_dirs

        qt_info = self._getQtInformation()

        self.qt_plugins_dirs = qt_info.library_paths

        if not self.qt_plugins_dirs and os.path.exists(qt_info.guess_path1):
            self.qt_plugins_dirs.append(qt_info.guess_path1)

        if not self.qt_plugins_dirs and os.path.exists(qt_info.guess_path2):
            self.qt_plugins_dirs.append(qt_info.guess_path2)

        # Avoid duplicates.
        self.qt_plugins_dirs = [
            os.path.normpath(dirname) for dirname in self.qt_plugins_dirs
        ]
        self.qt_plugins_dirs = tuple(sorted(set(self.qt_plugins_dirs)))

        if not self.qt_plugins_dirs:
            self.warning("Couldn't detect Qt plugin directories.")

        return self.qt_plugins_dirs

    def _getQtBinDirs(self):
        for plugin_dir in self.getQtPluginDirs():
            qt_bin_dir = os.path.normpath(os.path.join(plugin_dir, "..", "bin"))

            if os.path.isdir(qt_bin_dir):
                yield qt_bin_dir

    def hasPluginFamily(self, family):
        for plugin_dir in self.getQtPluginDirs():
            if os.path.isdir(os.path.join(plugin_dir, family)):
                return True

        # TODO: Special case "xml".
        return False

    def _getQmlDirectory(self):
        for plugin_dir in self.getQtPluginDirs():
            qml_plugin_dir = os.path.normpath(os.path.join(plugin_dir, "..", "qml"))

            if os.path.exists(qml_plugin_dir):
                return qml_plugin_dir

        self.sysexit("Error, no such Qt plugin family: qml")

    def _getQmlFileList(self, dlls):
        qml_plugin_dir = self._getQmlDirectory()

        # List all file types of the QML plugin folder that are datafiles and not DLLs.
        datafile_suffixes = (
            ".qml",
            ".qmlc",
            ".qmltypes",
            ".js",
            ".jsc",
            ".png",
            ".ttf",
            ".metainfo",
            ".mesh",
            ".frag",
            "qmldir",
        )

        if dlls:
            ignore_suffixes = datafile_suffixes
            only_suffixes = ()
        else:
            ignore_suffixes = ()
            only_suffixes = datafile_suffixes

        return getFileList(
            qml_plugin_dir,
            ignore_suffixes=ignore_suffixes,
            only_suffixes=only_suffixes,
        )

    def _findQtPluginDLLs(self):
        for qt_plugin_name in self.getQtPluginsSelected():
            # TODO: Don't have it as a plugin name.
            if qt_plugin_name == "qml":
                continue

            for qt_plugins_dir in self.getQtPluginDirs():
                qt_plugin_dir = os.path.join(qt_plugins_dir, qt_plugin_name)

                if not os.path.exists(qt_plugin_dir):
                    continue

                for filename in getFileList(qt_plugin_dir):
                    filename_relative = os.path.relpath(filename, qt_plugin_dir)

                    yield makeDllEntryPoint(
                        source_path=filename,
                        dest_path=os.path.join(
                            self.binding_name,
                            "qt-plugins",
                            qt_plugin_name,
                            filename_relative,
                        ),
                        package_name=self.binding_package_name,
                    )

    def _getChildNamed(self, *child_names):
        for child_name in child_names:
            return ModuleName(self.binding_name).getChildNamed(child_name)

    def getImplicitImports(self, module):
        # Way too many indeed, pylint: disable=too-many-branches

        full_name = module.getFullName()
        top_level_package_name, child_name = full_name.splitPackageName()

        if top_level_package_name != self.binding_name:
            return

        # These are alternatives depending on PyQt5 version
        if child_name == "QtCore" and "PyQt" in self.binding_name:
            if python_version < 0x300:
                yield "atexit"

            yield "sip"
            yield self._getChildNamed("sip")

        if child_name in (
            "QtGui",
            "QtAssistant",
            "QtDBus",
            "QtDeclarative",
            "QtSql",
            "QtDesigner",
            "QtHelp",
            "QtNetwork",
            "QtScript",
            "QtQml",
            "QtGui",
            "QtScriptTools",
            "QtSvg",
            "QtTest",
            "QtWebKit",
            "QtOpenGL",
            "QtXml",
            "QtXmlPatterns",
            "QtPrintSupport",
            "QtNfc",
            "QtWebKitWidgets",
            "QtBluetooth",
            "QtMultimediaWidgets",
            "QtQuick",
            "QtWebChannel",
            "QtWebSockets",
            "QtX11Extras",
            "_QOpenGLFunctions_2_0",
            "_QOpenGLFunctions_2_1",
            "_QOpenGLFunctions_4_1_Core",
        ):
            yield self._getChildNamed("QtCore")

        if child_name in (
            "QtDeclarative",
            "QtWebKit",
            "QtXmlPatterns",
            "QtQml",
            "QtPrintSupport",
            "QtWebKitWidgets",
            "QtMultimedia",
            "QtMultimediaWidgets",
            "QtQuick",
            "QtQuickWidgets",
            "QtWebSockets",
            "QtWebEngineWidgets",
        ):
            yield self._getChildNamed("QtNetwork")

        if child_name == "QtWebEngineWidgets":
            yield self._getChildNamed("QtWebEngineCore")
            yield self._getChildNamed("QtWebChannel")
            yield self._getChildNamed("QtPrintSupport")
        elif child_name == "QtScriptTools":
            yield self._getChildNamed("QtScript")
        elif child_name in (
            "QtWidgets",
            "QtDeclarative",
            "QtDesigner",
            "QtHelp",
            "QtScriptTools",
            "QtSvg",
            "QtTest",
            "QtWebKit",
            "QtPrintSupport",
            "QtWebKitWidgets",
            "QtMultimedia",
            "QtMultimediaWidgets",
            "QtOpenGL",
            "QtQuick",
            "QtQuickWidgets",
            "QtSql",
            "_QOpenGLFunctions_2_0",
            "_QOpenGLFunctions_2_1",
            "_QOpenGLFunctions_4_1_Core",
        ):
            yield self._getChildNamed("QtGui")

        if child_name in (
            "QtDesigner",
            "QtHelp",
            "QtTest",
            "QtPrintSupport",
            "QtSvg",
            "QtOpenGL",
            "QtWebKitWidgets",
            "QtMultimediaWidgets",
            "QtQuickWidgets",
            "QtSql",
        ):
            yield self._getChildNamed("QtWidgets")

        if child_name in ("QtPrintSupport",):
            yield self._getChildNamed("QtSvg")

        if child_name in ("QtWebKitWidgets",):
            yield self._getChildNamed("QtWebKit")
            yield self._getChildNamed("QtPrintSupport")

        if child_name in ("QtMultimediaWidgets",):
            yield self._getChildNamed("QtMultimedia")

        if child_name in ("QtQuick", "QtQuickWidgets"):
            yield self._getChildNamed("QtQml")

        if child_name in ("QtQuickWidgets", "QtQml"):
            yield self._getChildNamed("QtQuick")

        if child_name == "Qt":
            yield self._getChildNamed("QtCore")
            yield self._getChildNamed("QtDBus")
            yield self._getChildNamed("QtGui")
            yield self._getChildNamed("QtNetwork")
            yield self._getChildNamed("QtNetworkAuth")
            yield self._getChildNamed("QtSensors")
            yield self._getChildNamed("QtSerialPort")
            yield self._getChildNamed("QtMultimedia")
            yield self._getChildNamed("QtQml")
            yield self._getChildNamed("QtWidgets")

        # TODO: Questionable if this still exists in newer PySide.
        if child_name == "QtUiTools":
            yield self._getChildNamed("QtGui")
            yield self._getChildNamed("QtXml")

        # TODO: Questionable if this still exists in newer PySide.
        if full_name == "phonon":
            yield self._getChildNamed("QtGui")

    def createPostModuleLoadCode(self, module):
        """Create code to load after a module was successfully imported.

        For Qt we need to set the library path to the distribution folder
        we are running from. The code is immediately run after the code
        and therefore makes sure it's updated properly.
        """

        # Only in standalone mode, this will be needed.
        if not isStandaloneMode():
            return

        full_name = module.getFullName()

        if full_name == "%s.QtCore" % self.binding_name:
            code = """\
from __future__ import absolute_import

from %(package_name)s import QCoreApplication
import os

QCoreApplication.setLibraryPaths(
    [
        os.path.join(
           os.path.dirname(__file__),
           "qt-plugins"
        )
    ]
)

os.environ["QML2_IMPORT_PATH"] = os.path.join(
    os.path.dirname(__file__),
    "qml"
)

""" % {
                "package_name": full_name
            }

            return (
                code,
                """\
Setting Qt library path to distribution folder. We need to avoid loading target
system Qt plug-ins, which may be from another Qt version.""",
            )

    def createPreModuleLoadCode(self, module):
        """Method called when a module is being imported.

        Notes:
            If full name equals to the binding we insert code to include the dist
            folder in the 'PATH' environment variable (on Windows only).

        Args:
            module: the module object
        Returns:
            Code to insert and descriptive text (tuple), or (None, None).
        """

        # This isonly relevant on standalone mode for Windows
        if not isWin32Windows() or not isStandaloneMode():
            return None

        full_name = module.getFullName()

        if full_name == self.binding_name:
            code = """import os
path = os.environ.get("PATH", "")
if not path.startswith(__nuitka_binary_dir):
    os.environ["PATH"] = __nuitka_binary_dir + ";" + path
"""
            return (
                code,
                "Adding binary folder to runtime 'PATH' environment variable for proper loading.",
            )

    def considerDataFiles(self, module):
        full_name = module.getFullName()

        if full_name == self.binding_name and (
            "qml" in self.getQtPluginsSelected() or "all" in self.getQtPluginsSelected()
        ):
            qml_plugin_dir = self._getQmlDirectory()
            qml_target_dir = self._getQmlTargetDir()

            self.info("Including Qt plug-ins 'qml' below '%s'." % qml_target_dir)

            for filename in self._getQmlFileList(dlls=False):
                filename_relative = os.path.relpath(filename, qml_plugin_dir)

                yield makeIncludedDataFile(
                    source_path=filename,
                    dest_path=os.path.join(
                        qml_target_dir,
                        filename_relative,
                    ),
                    reason="Qt QML datafile",
                )
        elif (
            full_name
            in (
                self.binding_name + ".QtWebEngine",
                self.binding_name + ".QtWebEngineCore",
                self.binding_name + ".QtWebEngineWidgets",
            )
            and not self.webengine_done_data
        ):
            self.webengine_done_data = True

            for qt_plugin_dir in self.getQtPluginDirs():
                plugin_parent = os.path.dirname(qt_plugin_dir)

                resources_dir = os.path.join(plugin_parent, "resources")

                if os.path.exists(resources_dir):
                    for filename, filename_relative in listDir(resources_dir):
                        yield makeIncludedDataFile(
                            source_path=filename,
                            dest_path=os.path.join(
                                self._getResourcesTargetDir(), filename_relative
                            ),
                            reason="Qt resources",
                        )

            if not self.no_qt_translations:
                translations_path = self._getTranslationsPath()

                for filename in getFileList(translations_path):
                    filename_relative = os.path.relpath(filename, translations_path)
                    dest_path = self._getTranslationsTargetDir(filename_relative)

                    yield makeIncludedDataFile(
                        source_path=filename,
                        dest_path=os.path.join(dest_path, filename_relative),
                        reason="Qt translation",
                    )

    def getExtraDlls(self, module):
        # pylint: disable=too-many-branches
        full_name = module.getFullName()

        if full_name == self.binding_name:
            if not self.getQtPluginDirs():
                self.sysexit(
                    "Error, failed to detect '%s' plugin directories."
                    % self.binding_name
                )

            target_plugin_dir = os.path.join(full_name.asPath(), "qt-plugins")

            self.info(
                "Including Qt plug-ins '%s' below '%s'."
                % (
                    ",".join(
                        sorted(x for x in self.getQtPluginsSelected() if x != "xml")
                    ),
                    target_plugin_dir,
                )
            )

            # Yielding a generator might become OK too.
            for r in self._findQtPluginDLLs():
                yield r

            if isWin32Windows():
                # Those 2 vars will be used later, just saving some resources
                # by caching the files list
                qt_bin_files = sum(
                    (getFileList(qt_bin_dir) for qt_bin_dir in self._getQtBinDirs()),
                    [],
                )

                self.info("Including OpenSSL DLLs.")

                for filename in qt_bin_files:
                    basename = os.path.basename(filename).lower()
                    if basename in ("libeay32.dll", "ssleay32.dll"):
                        yield makeDllEntryPoint(
                            source_path=filename,
                            dest_path=basename,
                            package_name=full_name,
                        )

            if (
                "qml" in self.getQtPluginsSelected()
                or "all" in self.getQtPluginsSelected()
            ):
                qml_plugin_dir = self._getQmlDirectory()
                qml_target_dir = self._getQmlTargetDir()

                for filename in self._getQmlFileList(dlls=True):
                    filename_relative = os.path.relpath(filename, qml_plugin_dir)

                    yield makeDllEntryPoint(
                        source_path=filename,
                        dest_path=os.path.join(
                            qml_target_dir,
                            filename_relative,
                        ),
                        package_name=full_name
                        # reason="Qt QML plugin DLL",
                    )

                # Also copy required OpenGL DLLs on Windows
                if isWin32Windows():
                    opengl_dlls = ("libegl.dll", "libglesv2.dll", "opengl32sw.dll")

                    self.info("Including OpenGL DLLs.")

                    for filename in qt_bin_files:
                        basename = os.path.basename(filename).lower()

                        if basename in opengl_dlls or basename.startswith(
                            "d3dcompiler_"
                        ):
                            yield makeDllEntryPoint(
                                source_path=filename,
                                dest_path=basename,
                                package_name=full_name,
                            )

        elif full_name == self.binding_name + ".QtNetwork":
            if not isWin32Windows():
                dll_path = locateDLL("crypto")
                if dll_path is not None:
                    yield makeDllEntryPoint(
                        source_path=dll_path,
                        dest_path=os.path.basename(dll_path),
                        package_name=full_name,
                    )

                dll_path = locateDLL("ssl")
                if dll_path is not None:
                    yield makeDllEntryPoint(
                        source_path=dll_path,
                        dest_path=os.path.basename(dll_path),
                        package_name=full_name,
                    )
        elif (
            full_name
            in (
                self.binding_name + ".QtWebEngine",
                self.binding_name + ".QtWebEngineCore",
                self.binding_name + ".QtWebEngineWidgets",
            )
            and not self.webengine_done_binaries
        ):
            self.webengine_done_binaries = True  # prevent multiple copies
            self.info("Copying QtWebEngine binaries.")

            qt_web_engine_dir = self.getQtWebEngineProcessDir(
                module.getCompileTimeDirectory()
            )

            for filename, filename_relative in listDir(qt_web_engine_dir):
                if filename_relative.startswith("QtWebEngineProcess"):
                    yield makeDllEntryPoint(
                        source_path=filename,
                        dest_path=filename_relative,
                        package_name=full_name,
                    )

                    break
            else:
                self.sysexit(
                    "Error, cannot locate QtWebEngineProcess executable at '%s'."
                    % qt_web_engine_dir
                )

    def removeDllDependencies(self, dll_filename, dll_filenames):
        for value in self.getQtPluginDirs():
            # TODO: That is not a proper check if a file is below that.
            if dll_filename.startswith(value):
                for sub_dll_filename in dll_filenames:
                    for badword in (
                        "libKF5",
                        "libkfontinst",
                        "libkorganizer",
                        "libplasma",
                        "libakregator",
                        "libdolphin",
                        "libnoteshared",
                        "libknotes",
                        "libsystemsettings",
                        "libkerfuffle",
                        "libkaddressbook",
                        "libkworkspace",
                        "libkmail",
                        "libmilou",
                        "libtaskmanager",
                        "libkonsole",
                        "libgwenview",
                        "libweather_ion",
                    ):
                        if os.path.basename(sub_dll_filename).startswith(badword):
                            yield sub_dll_filename

    def onModuleEncounter(self, module_filename, module_name, module_kind):
        top_package_name = module_name.getTopLevelPackageName()

        if isStandaloneMode():
            if (
                top_package_name in _qt_binding_names
                and top_package_name != self.binding_name
            ):
                if top_package_name not in self.warned_about:
                    self.info(
                        """\
Unwanted import of '%(unwanted)s' that conflicts with '%(binding_name)s' encountered, preventing
its use. As a result an "ImportError" might be given at run time. Uninstall it for full compatible
behaviour with the uncompiled code to debug it."""
                        % {
                            "unwanted": top_package_name,
                            "binding_name": self.binding_name,
                        }
                    )

                    self.warned_about.add(top_package_name)

                return (
                    False,
                    "Not included due to potentially conflicting Qt versions with selected Qt binding '%s'."
                    % self.binding_name,
                )

    def onModuleCompleteSet(self, module_set):
        for module in module_set:
            module_name = module.getFullName()

            if module_name in _qt_binding_names and module_name != self.binding_name:
                self.warning(
                    """\
Unwanted import of '%(unwanted)s' that conflicts with '%(binding_name)s' encountered. Use \
'--nofollow-import-to=%(unwanted)s' or uninstall it."""
                    % {"unwanted": module_name, "binding_name": self.binding_name}
                )

            if module_name in _other_gui_binding_names:
                self.warning(
                    """\
Unwanted import of '%(unwanted)s' that conflicts with '%(binding_name)s' encountered. Use \
'--nofollow-import-to=%(unwanted)s' or uninstall it."""
                    % {"unwanted": module_name, "binding_name": self.binding_name}
                )

    def onModuleSourceCode(self, module_name, source_code):
        """Third party packages that make binding selections."""
        if module_name.hasNamespace("pyqtgraph"):
            # TODO: Add a mechanism to force all variable references of a name to something
            # during tree building, that would cover all uses in a nicer way.
            source_code = source_code.replace(
                "{QT_LIB.lower()}", self.binding_name.lower()
            )
            source_code = source_code.replace(
                "QT_LIB.lower()", repr(self.binding_name.lower())
            )

        return source_code


class NuitkaPluginPyQt5QtPluginsPlugin(NuitkaPluginQtBindingsPluginBase):
    """This is for plugins of PyQt5.

    When loads an image, it may use a plug-in, which in turn used DLLs,
    which for standalone mode, can cause issues of not having it.
    """

    plugin_name = "pyqt5"
    plugin_desc = "Required by the PyQt5 package."

    binding_name = "PyQt5"

    def __init__(self, qt_plugins, no_qt_translations):
        NuitkaPluginQtBindingsPluginBase.__init__(
            self, qt_plugins=qt_plugins, no_qt_translations=no_qt_translations
        )

    @classmethod
    def isRelevant(cls):
        return isStandaloneMode()

    def _getQmlTargetDir(self):
        return os.path.join(self.binding_name, "qml")

    def _getResourcesTargetDir(self):
        # TODO: Probably needs to be different for macOS.
        return "."


class NuitkaPluginDetectorPyQt5QtPluginsPlugin(NuitkaPluginBase):
    detector_for = NuitkaPluginPyQt5QtPluginsPlugin

    @classmethod
    def isRelevant(cls):
        return isStandaloneMode()

    def onModuleDiscovered(self, module):
        full_name = module.getFullName()

        if full_name == NuitkaPluginPyQt5QtPluginsPlugin.binding_name + ".QtCore":
            self.warnUnusedPlugin("Inclusion of Qt plugins.")
        elif full_name == "PyQt4.QtCore":
            self.warning(
                "Support for PyQt4 has been dropped. Please contact Nuitka commercial if you need it."
            )


class NuitkaPluginPySide2Plugins(NuitkaPluginQtBindingsPluginBase):
    """This is for plugins of PySide2.

    When Qt loads an image, it may use a plug-in, which in turn used DLLs,
    which for standalone mode, can cause issues of not having it.
    """

    plugin_name = "pyside2"
    plugin_desc = "Required by the PySide2 package."

    binding_name = "PySide2"

    def __init__(self, qt_plugins, no_qt_translations):
        if self._getNuitkaPatchLevel() < 1:
            self.warning(
                """\
This PySide2 version only partially supported through workarounds, full support: https://nuitka.net/pages/pyside2.html"""
            )

            if python_version < 0x360:
                self.sysexit(
                    "Error, unpatched PySide2 is not supported before CPython <3.6."
                )

        NuitkaPluginQtBindingsPluginBase.__init__(
            self, qt_plugins=qt_plugins, no_qt_translations=no_qt_translations
        )

    def _getQmlTargetDir(self):
        return os.path.join(self.binding_name, "qml")

    @staticmethod
    def _getResourcesTargetDir():
        # TODO: Probably needs to be different for macOS.
        return "."

    def onModuleEncounter(self, module_filename, module_name, module_kind):
        # Enforce recursion in to multiprocessing for accelerated mode, which
        # would normally avoid this.
        if module_name == self.binding_name and self._getNuitkaPatchLevel() < 1:
            return True, "Need to monkey patch PySide2 for abstract methods."

        return NuitkaPluginQtBindingsPluginBase.onModuleEncounter(
            self,
            module_filename=module_filename,
            module_name=module_name,
            module_kind=module_kind,
        )

    def createPostModuleLoadCode(self, module):
        """Create code to load after a module was successfully imported.

        For Qt we need to set the library path to the distribution folder
        we are running from. The code is immediately run after the code
        and therefore makes sure it's updated properly.
        """

        result = NuitkaPluginQtBindingsPluginBase.createPostModuleLoadCode(self, module)
        if result:
            yield result

        if (
            self._getNuitkaPatchLevel() < 1
            and module.getFullName() == self.binding_name
        ):
            code = r"""\
# Make them unique and count them.
wrapper_count = 0
import functools
import inspect

def nuitka_wrap(cls):
    global wrapper_count

    for attr in cls.__dict__:
        if attr.startswith("__") and attr.endswith("__"):
            continue

        value = getattr(cls, attr)

        if type(value).__name__ == "compiled_function":
            # Only work on overloaded attributes.
            for base in cls.__bases__:
                base_value = getattr(base, attr, None)

                if base_value:
                    module = inspect.getmodule(base_value)

                    # PySide C stuff does this, and we only need to cover that.
                    if module is None:
                        break
            else:
                continue

            wrapper_count += 1
            wrapper_name = "_wrapped_function_%s_%d" % (attr, wrapper_count)

            signature = inspect.signature(value)

            # Remove annotations junk that cannot be executed.
            signature = signature.replace(
                return_annotation = inspect.Signature.empty,
                parameters=[
                    parameter.replace(default=inspect.Signature.empty,annotation=inspect.Signature.empty)
                    for parameter in
                    signature.parameters.values()
                ]
            )

            v = r'''
def %(wrapper_name)s%(signature)s:
    return %(wrapper_name)s.func(%(parameters)s)
            ''' % {
                    "signature": signature,
                    "parameters": ",".join(signature.parameters),
                    "wrapper_name": wrapper_name
                }

            # TODO: Nuitka does not currently statically optimize this, might change!
            exec(
                v,
                globals(),
            )

            wrapper = globals()[wrapper_name]
            wrapper.func = value
            wrapper.__defaults__ = value.__defaults__

            setattr(cls, attr, wrapper)

    return cls

@classmethod
def my_init_subclass(cls, *args):
    return nuitka_wrap(cls)

import PySide2.QtCore
PySide2.QtCore.QAbstractItemModel.__init_subclass__ = my_init_subclass
PySide2.QtCore.QObject.__init_subclass__ = my_init_subclass
"""
            yield (
                code,
                """\
Monkey patching classes derived from PySide2 base classes to pass PySide2 checks.""",
            )


class NuitkaPluginDetectorPySide2Plugins(NuitkaPluginBase):
    detector_for = NuitkaPluginPySide2Plugins

    def onModuleDiscovered(self, module):
        if module.getFullName() == NuitkaPluginPySide2Plugins.binding_name + ".QtCore":
            self.warnUnusedPlugin("Making callbacks work and include Qt plugins.")


class NuitkaPluginPySide6Plugins(NuitkaPluginQtBindingsPluginBase):
    """This is for plugins of PySide6.

    When Qt loads an image, it may use a plug-in, which in turn used DLLs,
    which for standalone mode, can cause issues of not having it.
    """

    plugin_name = "pyside6"
    plugin_desc = "Required by the PySide6 package for standalone mode."

    binding_name = "PySide6"

    def __init__(self, qt_plugins, no_qt_translations):
        NuitkaPluginQtBindingsPluginBase.__init__(
            self, qt_plugins=qt_plugins, no_qt_translations=no_qt_translations
        )

        if self._getBindingVersion() < (6, 1, 2):
            self.warning(
                """\
Only PySide 6.1.2 or higher (or dev branch compiled), otherwise callbacks won't work."""
            )

    def _getQmlTargetDir(self):
        return os.path.join(self.binding_name, "qml")

    @staticmethod
    def _getResourcesTargetDir():
        # TODO: Probably needs to be different for macOS.
        return "."


class NuitkaPluginDetectorPySide6Plugins(NuitkaPluginBase):
    detector_for = NuitkaPluginPySide6Plugins

    def onModuleDiscovered(self, module):
        if module.getFullName() == NuitkaPluginPySide6Plugins.binding_name + ".QtCore":
            self.warnUnusedPlugin("Standalone mode support and Qt plugins.")
