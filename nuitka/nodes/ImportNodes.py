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
""" Nodes related to importing modules or names.

Normally imports are mostly relatively static, but Nuitka also attempts to
cover the uses of "__import__" built-in and other import techniques, that
allow dynamic values.

If other optimizations make it possible to predict these, the compiler can go
deeper that what it normally could. The import expression node can recurse.
"""

import os
import sys

from nuitka.__past__ import long, unicode, xrange
from nuitka.codegen.Reports import onMissingTrust
from nuitka.importing.IgnoreListing import getModuleIgnoreList
from nuitka.importing.Importing import (
    findModule,
    getModuleNameAndKindFromFilename,
)
from nuitka.importing.ImportResolving import resolveModuleName
from nuitka.importing.Recursion import decideRecursion, recurseTo
from nuitka.importing.StandardLibrary import isStandardLibraryPath
from nuitka.ModuleRegistry import getUncompiledModule
from nuitka.Options import isStandaloneMode, shallWarnUnusualCode
from nuitka.PythonVersions import (
    getFutureModuleKeys,
    getImportlibSubPackages,
    python_version,
)
from nuitka.specs.BuiltinParameterSpecs import (
    BuiltinParameterSpec,
    extractBuiltinArgs,
)
from nuitka.Tracing import inclusion_logger, unusual_logger
from nuitka.utils.FileOperations import relpath
from nuitka.utils.ModuleNames import ModuleName

from .ConstantRefNodes import (
    ExpressionConstantSysVersionInfoRef,
    makeConstantRefNode,
)
from .ExpressionBases import (
    ExpressionBase,
    ExpressionChildHavingBase,
    ExpressionChildrenHavingBase,
)
from .LocalsScopes import GlobalsDictHandle
from .NodeBases import StatementChildHavingBase
from .NodeMakingHelpers import makeRaiseExceptionReplacementExpression
from .shapes.BuiltinTypeShapes import tshape_module, tshape_module_builtin

# These module are supported in code generation to be imported the hard way.
hard_modules = frozenset(
    (
        "os",
        "sys",
        "types",
        "typing",
        "__future__",
        "site",
        "importlib",
        "_frozen_importlib",
        "_frozen_importlib_external",
        "pkgutil",
        "functools",
    )
)

hard_modules_version = {
    "typing": 0x350,
    "_frozen_importlib": 0x300,
    "_frozen_importlib_external": 0x350,
}

trust_undefined = 0
trust_constant = 1
trust_exist = 2
trust_future = trust_exist
trust_importable = 3
trust_node = 4
trust_may_exist = 5
trust_not_exist = 6

trust_node_factory = {}

module_importlib_trust = dict(
    (key, trust_importable) for key in getImportlibSubPackages()
)

module_sys_trust = {
    "version": trust_constant,
    "stdout": trust_exist,
    "stderr": trust_exist,
}

if python_version < 0x270:
    module_sys_trust["version_info"] = trust_constant
else:
    module_sys_trust["version_info"] = trust_node
    trust_node_factory[("sys", "version_info")] = ExpressionConstantSysVersionInfoRef

if python_version < 0x300:
    module_sys_trust["exc_type"] = trust_may_exist
    module_sys_trust["exc_value"] = trust_may_exist
    module_sys_trust["exc_traceback"] = trust_may_exist
else:
    module_sys_trust["exc_type"] = trust_not_exist
    module_sys_trust["exc_value"] = trust_not_exist
    module_sys_trust["exc_traceback"] = trust_not_exist

module_typing_trust = {
    "TYPE_CHECKING": trust_constant,
}

hard_modules_trust = {
    "os": {},
    "sys": module_sys_trust,
    "types": {},
    "typing": module_typing_trust,
    "__future__": dict((key, trust_future) for key in getFutureModuleKeys()),
    "site": {},
    "importlib": module_importlib_trust,
    "_frozen_importlib": {},
    "_frozen_importlib_external": {},
    "pkgutil": {"get_data": trust_exist},
    "functools": {"partial": trust_exist},
}


def isHardModuleWithoutSideEffect(module_name):
    return module_name in hard_modules and module_name != "site"


def makeExpressionAbsoluteImportNode(module_name, source_ref):
    return ExpressionBuiltinImport(
        name=makeConstantRefNode(module_name, source_ref, True),
        globals_arg=None,
        locals_arg=None,
        fromlist=None,
        level=makeConstantRefNode(0, source_ref, True),
        source_ref=source_ref,
    )


class ExpressionImportModuleFixed(ExpressionBase):
    """Hard coded import names, that we know to exist."

    These created as result of builtin imports and importlib.import_module calls
    that were compile time resolved, and for known module names.
    """

    kind = "EXPRESSION_IMPORT_MODULE_FIXED"

    __slots__ = (
        "module_name",
        "recurse_attempted",
        "finding",
        "imported_module_desc",
        "package_modules_desc",
    )

    def __init__(self, module_name, source_ref):
        ExpressionBase.__init__(self, source_ref=source_ref)

        self.module_name = resolveModuleName(module_name)

        self.recurse_attempted = False
        self.finding = None

        # The module actually referenced in that import.
        self.imported_module_desc = None

        # For "package.sub_package.module" we also need to import the package,
        # because the imported_module not be found, as it's not a module, e.g.
        # in the case of "os.path" or "six.moves".
        self.package_modules_desc = None

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {"module_name": self.module_name}

    def getModuleName(self):
        return self.module_name

    @staticmethod
    def mayHaveSideEffects():
        # TODO: For included modules, we might be able to tell, not not done now.
        return True

    @staticmethod
    def mayRaiseException(exception_type):
        # TODO: For included modules, we might be able to tell, not not done now.
        return True

    def getTypeShape(self):
        if self.module_name in sys.builtin_module_names:
            return tshape_module_builtin
        else:
            return tshape_module

    def _attemptRecursion(self, trace_collection):
        module_package, module_filename, self.finding = findModule(
            importing=self,
            module_name=self.module_name,
            parent_package=None,
            level=0,
            warn=True,
        )

        if module_filename is not None:
            imported_module = _considerImport(
                trace_collection=trace_collection,
                module_filename=module_filename,
                module_package=module_package,
            )

            if imported_module is not None:
                self.imported_module_desc = (
                    imported_module.getFullName(),
                    imported_module.getFilename(),
                )

        else:
            while True:
                module_name = self.module_name.getPackageName()

                if module_name is None:
                    break

                module_package, module_filename, _finding = findModule(
                    importing=self,
                    module_name=module_name,
                    parent_package=None,
                    level=0,
                    warn=True,
                )

                if module_filename is not None:
                    package_module = self._consider(
                        trace_collection=trace_collection,
                        module_filename=module_filename,
                        module_package=module_package,
                    )

                    if package_module is not None:
                        if self.package_modules_desc is None:
                            self.package_modules_desc = []

                        self.package_modules_desc.append(
                            (package_module.getFullName(), package_module.getFilename())
                        )

    def computeExpressionRaw(self, trace_collection):
        # Attempt to recurse if not already done.
        if not self.recurse_attempted:
            self._attemptRecursion(trace_collection)
            self.recurse_attempted = True

        if self.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        if self.imported_module_desc is not None:
            trace_collection.onUsedModule(
                module_name=self.imported_module_desc[0],
                module_relpath=self.imported_module_desc[1],
            )

        # These are added in any case.
        if self.package_modules_desc is not None:
            for package_module_desc in self.package_modules_desc:
                trace_collection.onUsedModule(
                    module_name=package_module_desc[0],
                    module_relpath=package_module_desc[1],
                )

        # Nothing to do about it.
        return self, None, None

    def computeExpressionImportName(self, import_node, import_name, trace_collection):
        # TODO: For include modules, something might be possible here.
        return self.computeExpressionAttribute(
            lookup_node=import_node,
            attribute_name=import_name,
            trace_collection=trace_collection,
        )


class ExpressionImportHardBase(ExpressionBase):
    # Base classes can be abstract, pylint: disable=abstract-method
    #
    __slots__ = ("module_name", "finding", "module_filename")

    def __init__(self, module_name, source_ref):
        self.module_name = ModuleName(module_name)

        self.finding = None
        self.module_filename = None

        ExpressionBase.__init__(self, source_ref=source_ref)

    def _attemptRecursion(self, trace_collection):
        module_package, self.module_filename, self.finding = findModule(
            importing=self,
            module_name=self.module_name,
            parent_package=None,
            level=0,
            warn=True,
        )

        # Expect to find them.
        assert self.finding != "not-found"

        if self.module_filename is not None:
            imported_module = _considerImport(
                trace_collection=trace_collection,
                module_filename=self.module_filename,
                module_package=module_package,
            )

            if imported_module is None:
                self.module_filename = None


class ExpressionImportModuleHard(ExpressionImportHardBase):
    """Hard coded import names, e.g. of "__future__"

    These are directly created for some Python mechanics, but also due to
    compile time optimization for imports of statically known modules.
    """

    kind = "EXPRESSION_IMPORT_MODULE_HARD"

    __slots__ = ("module",)

    def __init__(self, module_name, source_ref):
        ExpressionImportHardBase.__init__(
            self, module_name=module_name, source_ref=source_ref
        )

        if isHardModuleWithoutSideEffect(self.module_name):
            self.module = __import__(self.module_name)
        else:
            self.module = None

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {"module_name": self.module_name}

    def getModuleName(self):
        return self.module_name

    def mayHaveSideEffects(self):
        return self.module is None

    def mayRaiseException(self, exception_type):
        return self.mayHaveSideEffects()

    def getTypeShape(self):
        if self.module_name in sys.builtin_module_names:
            return tshape_module_builtin
        else:
            return tshape_module

    def computeExpressionRaw(self, trace_collection):
        if self.finding is None:
            self._attemptRecursion(trace_collection)

        # Recursion for stdlib can be enabled, and some of
        # these are even outside of that.
        if self.module_filename is not None:
            trace_collection.onUsedModule(
                module_name=self.module_name, module_relpath=self.module_filename
            )

        if self.mayRaiseException(BaseException):
            trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    def computeExpressionImportName(self, import_node, import_name, trace_collection):
        return self.computeExpressionAttribute(
            lookup_node=import_node,
            attribute_name=import_name,
            trace_collection=trace_collection,
        )

    @staticmethod
    def _getImportNameErrorString(module, module_name, name):
        if python_version < 0x340:
            return "cannot import name %s" % name
        if python_version < 0x370:
            return "cannot import name %r" % name
        elif isStandaloneMode():
            return "cannot import name %r from %r" % (name, module_name)
        else:
            return "cannot import name %r from %r (%s)" % (
                name,
                module_name,
                module.__file__ if hasattr(module, "__file__") else "unknown location",
            )

    def computeExpressionAttribute(self, lookup_node, attribute_name, trace_collection):
        # By default, an attribute lookup may change everything about the lookup
        # source.

        if self.module is not None:
            trust = hard_modules_trust[self.module_name].get(
                attribute_name, trust_undefined
            )

            if trust is trust_importable:
                # TODO: Change this is a hard module import itself, currently these are not all trusted
                # themselves yet. We do not have to indicate exception, but it makes no sense to annotate
                # that here at this point.
                trace_collection.onExceptionRaiseExit(BaseException)
            elif trust is trust_may_exist:
                trace_collection.onExceptionRaiseExit(BaseException)
            elif (
                not hasattr(self.module, attribute_name)
                and trust is not trust_undefined
            ):
                # TODO: Unify with below branches.
                trace_collection.onExceptionRaiseExit(ImportError)

                new_node = makeRaiseExceptionReplacementExpression(
                    expression=lookup_node,
                    exception_type="AttributeError",
                    exception_value=self._getImportNameErrorString(
                        self.module, self.module_name, attribute_name
                    ),
                )

                return (
                    new_node,
                    "new_raise",
                    "Hard module %r attribute missing %r pre-computed."
                    % (self.module_name, attribute_name),
                )
            else:
                if trust is trust_undefined:
                    trace_collection.onExceptionRaiseExit(ImportError)

                    onMissingTrust(
                        "Hard module %r attribute %r missing trust config for existing value.",
                        lookup_node.getSourceReference(),
                        self.module_name,
                        attribute_name,
                    )
                elif trust is trust_constant:
                    # Make sure it's actually there, and not becoming the getattr default by accident.
                    assert hasattr(self.module, attribute_name), self

                    return (
                        makeConstantRefNode(
                            constant=getattr(self.module, attribute_name),
                            source_ref=lookup_node.getSourceReference(),
                            user_provided=True,
                        ),
                        "new_constant",
                        "Hard module %r imported %r pre-computed to constant value."
                        % (self.module_name, attribute_name),
                    )
                elif trust is trust_node:
                    result = trust_node_factory[self.module_name, attribute_name](
                        source_ref=lookup_node.source_ref
                    )

                    return (
                        result,
                        "new_expression",
                        "Attribute lookup %r of hard module %r becomes node %r."
                        % (self.module_name, attribute_name, result.kind),
                    )
                else:
                    result = ExpressionImportModuleNameHard(
                        module_name=self.module_name,
                        import_name=attribute_name,
                        source_ref=lookup_node.getSourceReference(),
                    )

                    return (
                        result,
                        "new_expression",
                        "Attribute lookup %r of hard module %r becomes hard module name import."
                        % (self.module_name, attribute_name),
                    )

        else:
            # Nothing can be known, but lets not do control flow escape, that is just
            # too unlikely.
            trace_collection.onExceptionRaiseExit(BaseException)

        return lookup_node, None, None


class ExpressionImportModuleNameHard(ExpressionImportHardBase):
    """Hard coded import names, e.g. of "os.path.dirname"

    These are directly created for some Python mechanics.
    """

    kind = "EXPRESSION_IMPORT_MODULE_NAME_HARD"

    __slots__ = ("import_name", "trust", "finding", "module_filename")

    def __init__(self, module_name, import_name, source_ref):
        ExpressionImportHardBase.__init__(
            self, module_name=module_name, source_ref=source_ref
        )

        self.import_name = import_name

        self.trust = hard_modules_trust[self.module_name].get(self.import_name)

    def finalize(self):
        del self.parent

    def getDetails(self):
        return {"module_name": self.module_name, "import_name": self.import_name}

    def getModuleName(self):
        return self.module_name

    def getImportName(self):
        return self.import_name

    def computeExpressionRaw(self, trace_collection):
        if self.finding is None:
            self._attemptRecursion(trace_collection)

        # Recursion for stdlib can be enabled, and some of
        # these are even outside of that.
        if self.module_filename is not None:
            trace_collection.onUsedModule(
                module_name=self.module_name, module_relpath=self.module_filename
            )

        # As good as it gets, will exist, otherwise we do not get created.
        if self.mayHaveSideEffects():
            trace_collection.onExceptionRaiseExit(AttributeError)

        return self, None, None

    def mayHaveSideEffects(self):
        return self.trust is None

    def mayRaiseException(self, exception_type):
        return self.trust is None


importlib_import_module_spec = BuiltinParameterSpec(
    "importlib.import_module", ("name", "package"), default_count=1
)


class ExpressionImportlibImportModuleRef(ExpressionImportModuleNameHard):
    kind = "EXPRESSION_IMPORTLIB_IMPORT_MODULE_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHard.__init__(
            self,
            module_name="importlib",
            import_name="import_module",
            source_ref=source_ref,
        )

    @staticmethod
    def getDetails():
        return {}

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionImportlibImportModuleCall,
            builtin_spec=importlib_import_module_spec,
        )

        return result, "new_expression", "Call of 'importlib.import_module' recognized."


def _getImportNameAsStr(value):
    if value is None:
        result = None
    else:
        result = value.getCompileTimeConstant()

    if type(result) in (str, unicode):
        # TODO: This is not handling decoding errors all that well.
        if str is not unicode and type(result) is unicode:
            result = str(result)

    return result


class ExpressionImportlibImportModuleCall(ExpressionChildrenHavingBase):
    """Call to "importlib.import_module" """

    kind = "EXPRESSION_IMPORTLIB_IMPORT_MODULE_CALL"

    named_children = "name", "package"

    def __init__(self, name, package, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self, values={"name": name, "package": package}, source_ref=source_ref
        )

    @staticmethod
    def _resolveImportLibArgs(module_name, package_name):
        # Relative imports need to be resolved by package name.
        if module_name.startswith("."):
            if not package_name:
                return None

                # TODO: Static exception should be created and warned about, Python2/Python3 differ
                # raise TypeError("relative imports require the 'package' argument")
                # msg = ("the 'package' argument is required to perform a relative import for {!r}")
                # raise TypeError(msg.format(name))

            level = 0
            for character in module_name:
                if character != ".":
                    break
                level += 1
            module_name = module_name[level:]

            dot = len(package_name)
            for _i in xrange(level, 1, -1):
                try:
                    dot = package_name.rindex(".", 0, dot)
                except ValueError:
                    return None
                    # TODO: Static exception should be created and warned about.
                    # raise ValueError("attempted relative import beyond top-level package")
            return "%s.%s" % (package_name[:dot], module_name)

        if package_name:
            return "%s.%s" % (package_name, module_name)
        else:
            return module_name

    def computeExpression(self, trace_collection):
        module_name = self.subnode_name
        package_name = self.subnode_package

        if (
            package_name is None or package_name.isCompileTimeConstant()
        ) and module_name.isCompileTimeConstant():
            imported_module_name = _getImportNameAsStr(module_name)
            imported_package_name = _getImportNameAsStr(package_name)

            if (
                imported_package_name is None or type(imported_package_name) is str
            ) and type(imported_module_name) is str:
                resolved_module_name = self._resolveImportLibArgs(
                    imported_module_name, imported_package_name
                )

                if resolved_module_name is not None:
                    result = ExpressionImportModuleFixed(
                        module_name=resolved_module_name, source_ref=self.source_ref
                    )

                    return (
                        result,
                        "new_expression",
                        "Resolved importlib.import_module call to import of '%s'."
                        % resolved_module_name,
                    )

        # Any code could be run, note that.
        trace_collection.onControlFlowEscape(self)

        # Importing may raise an exception obviously, unless we know it will
        # not.
        trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: May return a module or module variable reference of some sort in
        # the future with embedded modules.
        return self, None, None


module_importlib_trust["import_module"] = trust_node
trust_node_factory[("importlib", "import_module")] = ExpressionImportlibImportModuleRef

_warned_about = set()


def _considerImport(trace_collection, module_filename, module_package):
    assert module_package is None or (
        type(module_package) is ModuleName and module_package != ""
    ), repr(module_package)

    module_filename = os.path.normpath(module_filename)

    module_name, module_kind = getModuleNameAndKindFromFilename(module_filename)

    if module_kind is not None:
        module_fullpath = ModuleName.makeModuleNameInPackage(
            module_name, module_package
        )

        decision, reason = decideRecursion(
            module_filename=module_filename,
            module_name=module_fullpath,
            module_kind=module_kind,
        )

        if decision:
            module_relpath = relpath(module_filename)

            imported_module = recurseTo(
                signal_change=trace_collection.signalChange,
                module_package=module_package,
                module_filename=module_filename,
                module_relpath=module_relpath,
                module_kind=module_kind,
                reason=reason,
            )

            return imported_module
        elif decision is False and module_kind == "py":
            uncompiled_module = getUncompiledModule(module_fullpath, module_filename)

            if uncompiled_module is not None:
                return uncompiled_module
        elif decision is None and module_kind == "py":
            if (
                module_filename not in _warned_about
                and module_fullpath not in getModuleIgnoreList()
            ):
                _warned_about.add(module_filename)

                inclusion_logger.warning(
                    """\
Not following import to '%(full_path)s' (%(filename)s), please specify \
--nofollow-imports (do not follow any imports), \
--follow-imports (follow all generally), \
--nofollow-import-to=%(full_path)s (do not follow it), \
--follow-import-to=%(full_path)s (follow import it) to change."""
                    % {"full_path": module_fullpath, "filename": module_filename}
                )


class ExpressionBuiltinImport(ExpressionChildrenHavingBase):
    # Very detail rich node, pylint: disable=too-many-instance-attributes

    __slots__ = (
        "recurse_attempted",
        "imported_module_desc",
        "import_list_modules_desc",
        "package_modules_desc",
        "finding",
        "type_shape",
        "builtin_module",
        "module_filename",
    )

    kind = "EXPRESSION_BUILTIN_IMPORT"

    named_children = ("name", "globals_arg", "locals_arg", "fromlist", "level")

    def __init__(self, name, globals_arg, locals_arg, fromlist, level, source_ref):
        ExpressionChildrenHavingBase.__init__(
            self,
            values={
                "name": name,
                "globals_arg": globals_arg,
                "locals_arg": locals_arg,
                "fromlist": fromlist,
                "level": level,
            },
            source_ref=source_ref,
        )

        self.recurse_attempted = False

        # The module actually referenced in that import.
        self.imported_module_desc = None

        # The fromlist imported modules if any.
        self.import_list_modules_desc = []

        # For "package.sub_package.module" we also need to import the package,
        # because the imported_module not be found, as it's not a module, e.g.
        # in the case of "os.path" or "six.moves".
        self.package_modules_desc = None

        self.finding = None

        self.type_shape = tshape_module

        self.builtin_module = None

        # If found, filename of the imported module.
        self.module_filename = None

    def _attemptRecursion(self, trace_collection, module_name):
        # Complex stuff, pylint: disable=too-many-branches

        parent_module = self.getParentModule()

        parent_package = parent_module.getFullName()
        if not parent_module.isCompiledPythonPackage():
            parent_package = parent_package.getPackageName()

        level = self.subnode_level

        if level is None:
            level = 0 if parent_module.getFutureSpec().isAbsoluteImport() else -1
        elif not level.isCompileTimeConstant():
            return
        else:
            level = level.getCompileTimeConstant()

        # TODO: Catch this as a static error maybe.
        if type(level) not in (int, long):
            return

        module_package, self.module_filename, self.finding = findModule(
            importing=self,
            module_name=ModuleName(module_name),
            parent_package=parent_package,
            level=level,
            warn=True,
        )

        if self.module_filename is not None:
            imported_module = _considerImport(
                trace_collection=trace_collection,
                module_filename=self.module_filename,
                module_package=module_package,
            )

            if imported_module is not None:
                self.imported_module_desc = (
                    imported_module.getFullName(),
                    imported_module.getFilename(),
                )

                import_list = self.subnode_fromlist

                if import_list is not None:
                    if import_list.isCompileTimeConstant():
                        import_list = import_list.getCompileTimeConstant()

                    if type(import_list) not in (tuple, list):
                        import_list = None

                if import_list and imported_module.isCompiledPythonPackage():
                    for import_item in import_list:
                        if import_item == "*":
                            continue

                        module_package, module_filename, _finding = findModule(
                            importing=self,
                            module_name=ModuleName(import_item),
                            parent_package=imported_module.getFullName(),
                            level=-1,  # Relative import, so child is used.
                            warn=False,
                        )

                        if module_filename is not None:
                            sub_imported_module = _considerImport(
                                trace_collection=trace_collection,
                                module_filename=module_filename,
                                module_package=module_package,
                            )

                            if sub_imported_module is not None:
                                self.import_list_modules_desc.append(
                                    (
                                        sub_imported_module.getFullName(),
                                        sub_imported_module.getFilename(),
                                    )
                                )
        else:
            module_name = resolveModuleName(module_name)

            while True:
                module_name = module_name.getPackageName()

                if module_name is None:
                    break

                module_package, module_filename, _finding = findModule(
                    importing=self,
                    module_name=module_name,
                    parent_package=parent_package,
                    level=level,
                    warn=True,
                )

                if module_filename is not None:
                    package_module = _considerImport(
                        trace_collection=trace_collection,
                        module_filename=module_filename,
                        module_package=module_package,
                    )

                    if package_module is not None:
                        if self.package_modules_desc is None:
                            self.package_modules_desc = []

                        self.package_modules_desc.append(
                            (package_module.getFullName(), package_module.getFilename())
                        )

    def _addUsedModules(self, trace_collection):
        if self.finding != "not-found":
            if self.imported_module_desc is not None:
                trace_collection.onUsedModule(
                    module_name=self.imported_module_desc[0],
                    module_relpath=self.imported_module_desc[1],
                )

            for import_list_module_desc in self.import_list_modules_desc:
                trace_collection.onUsedModule(
                    module_name=import_list_module_desc[0],
                    module_relpath=import_list_module_desc[1],
                )

        # These are added in any case.
        if self.package_modules_desc is not None:
            for package_module_desc in self.package_modules_desc:
                trace_collection.onUsedModule(
                    module_name=package_module_desc[0],
                    module_relpath=package_module_desc[1],
                )

    def computeExpression(self, trace_collection):
        # TODO: In fact, if the module is not a package, we don't have to insist
        # on the "fromlist" that much, but normally it's not used for anything
        # but packages, so it will be rare.
        self._addUsedModules(trace_collection)

        # Attempt to recurse if not already done.
        if self.recurse_attempted:
            if self.finding == "not-found":
                # Importing and not finding, may raise an exception obviously.
                trace_collection.onExceptionRaiseExit(BaseException)
            else:
                # If we know it exists, only RuntimeError shall occur.
                trace_collection.onExceptionRaiseExit(RuntimeError)

            # We stay here.
            return self, None, None

        module_name = self.subnode_name

        if module_name.isCompileTimeConstant():
            imported_module_name = module_name.getCompileTimeConstant()

            if type(imported_module_name) in (str, unicode):
                imported_module_name = resolveModuleName(imported_module_name)

                self._attemptRecursion(
                    trace_collection=trace_collection, module_name=imported_module_name
                )

                self.recurse_attempted = True

                if self.finding == "absolute" and imported_module_name in hard_modules:
                    if isStandardLibraryPath(self.module_filename):
                        result = ExpressionImportModuleHard(
                            module_name=imported_module_name, source_ref=self.source_ref
                        )

                        return (
                            result,
                            "new_expression",
                            "Lowered import of standard library module %r to hard import."
                            % imported_module_name,
                        )
                    elif shallWarnUnusualCode():
                        unusual_logger.warning(
                            "%s Standard library module %r used from outside path %r."
                            % (
                                self.source_ref.getAsString(),
                                imported_module_name,
                                self.module_filename,
                            )
                        )

                if self.finding == "built-in":
                    if imported_module_name in hard_modules:
                        result = ExpressionImportModuleHard(
                            module_name=imported_module_name, source_ref=self.source_ref
                        )

                        return (
                            result,
                            "new_expression",
                            "Lowered import of built-in module %r to hard import."
                            % imported_module_name,
                        )

                    self.type_shape = tshape_module_builtin
                    self.builtin_module = __import__(imported_module_name)

                self._addUsedModules(trace_collection)
            else:
                # TODO: This doesn't preserve side effects.

                # Non-strings is going to raise an error.
                (
                    new_node,
                    change_tags,
                    message,
                ) = trace_collection.getCompileTimeComputationResult(
                    node=self,
                    computation=lambda: __import__(
                        module_name.getCompileTimeConstant()
                    ),
                    description="Replaced '__import__' call with non-string module name argument.",
                )

                # Must fail, must not go on when it doesn't.
                assert change_tags == "new_raise", module_name

                return new_node, change_tags, message

        # Importing may raise an exception obviously, unless we know it will
        # not.
        if self.finding != "built-in":
            trace_collection.onExceptionRaiseExit(BaseException)

        # TODO: May return a module or module variable reference of some sort in
        # the future with embedded modules.
        return self, None, None

    # TODO: Add computeExpressionImportName

    def mayRaiseException(self, exception_type):
        return self.finding != "built-in"

    def mayRaiseExceptionImportName(self, exception_type, import_name):
        if self.finding == "built-in":
            return not hasattr(self.builtin_module, import_name)
        else:
            return True

    def getTypeShape(self):
        return self.type_shape


class StatementImportStar(StatementChildHavingBase):
    kind = "STATEMENT_IMPORT_STAR"

    named_child = "module"

    __slots__ = ("target_scope",)

    def __init__(self, target_scope, module_import, source_ref):
        StatementChildHavingBase.__init__(
            self, value=module_import, source_ref=source_ref
        )

        self.target_scope = target_scope

        # TODO: Abstract these things.
        if type(self.target_scope) is GlobalsDictHandle:
            self.target_scope.markAsEscaped()

    def getTargetDictScope(self):
        return self.target_scope

    def computeStatement(self, trace_collection):
        trace_collection.onExpression(self.subnode_module)

        trace_collection.onLocalsDictEscaped(self.target_scope)

        # Need to invalidate everything, and everything could be assigned to
        # something else now.
        trace_collection.removeAllKnowledge()

        # We could always encounter that __all__ is a strange beast and causes
        # the exception.
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None

    @staticmethod
    def mayRaiseException(exception_type):
        # Not done. TODO: Later we can try and check for "__all__" if it
        # really can be that way.
        return True

    @staticmethod
    def getStatementNiceName():
        return "star import statement"


class ExpressionImportName(ExpressionChildHavingBase):
    kind = "EXPRESSION_IMPORT_NAME"

    named_child = "module"

    __slots__ = ("import_name", "level")

    def __init__(self, module, import_name, level, source_ref):
        ExpressionChildHavingBase.__init__(self, value=module, source_ref=source_ref)

        self.import_name = import_name
        self.level = level

        # Not allowed.
        assert level is not None

        assert module is not None

    def getImportName(self):
        return self.import_name

    def getImportLevel(self):
        return self.level

    def getDetails(self):
        return {"import_name": self.import_name, "level": self.level}

    def computeExpression(self, trace_collection):
        return self.subnode_module.computeExpressionImportName(
            import_node=self,
            import_name=self.import_name,
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_module.mayRaiseExceptionImportName(
            exception_type=exception_type, import_name=self.import_name
        )
