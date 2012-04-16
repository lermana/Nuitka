#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Nodes concern with exec and eval builtins.

These are the dynamic codes, and as such rather difficult. We would like
to eliminate or limit their impact as much as possible, but it's difficult
to do.
"""

from .NodeBases import (
    CPythonExpressionChildrenHavingBase,
    CPythonChildrenHaving,
    CPythonNodeBase,
    CPythonClosureTaker,
    CPythonClosureGiverNodeBase
)

from .NodeMakingHelpers import convertNoneConstantToNone

from nuitka import Variables, Utils

class CPythonExpressionBuiltinEval( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_EVAL"

    named_children = ( "source", "globals", "locals" )

    def __init__( self, source_code, globals_arg, locals_arg, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values     = {
                "source"  : source_code,
                "globals" : globals_arg,
                "locals"  : locals_arg,
            },
            source_ref = source_ref
        )

    getSourceCode = CPythonExpressionChildrenHavingBase.childGetter( "source" )
    getGlobals = CPythonExpressionChildrenHavingBase.childGetter( "globals" )
    getLocals = CPythonExpressionChildrenHavingBase.childGetter( "locals" )

    def computeNode( self ):
        # TODO: Attempt for constant values to do it.
        return self, None, None


# Note: Python3 only so far.
if Utils.getPythonVersion() >= 300:
    class CPythonExpressionBuiltinExec( CPythonExpressionBuiltinEval ):
        kind = "EXPRESSION_BUILTIN_EXEC"

        def needsLocalsDict( self ):
            return True

# Note: Python2 only
if Utils.getPythonVersion() < 300:
    class CPythonExpressionBuiltinExecfile( CPythonExpressionBuiltinEval ):
        kind = "EXPRESSION_BUILTIN_EXECFILE"

        named_children = ( "source", "globals", "locals" )

        def __init__( self, source_code, globals_arg, locals_arg, source_ref ):
            CPythonExpressionBuiltinEval.__init__( self, source_code, globals_arg, locals_arg, source_ref )

        def needsLocalsDict( self ):
            return True


# TODO: Find a place for this. Potentially as an attribute of nodes themselves.
def _couldBeNone( node ):
    if node is None:
        return True
    elif node.isExpressionMakeDict():
        return False
    elif node.isExpressionBuiltinGlobals() or node.isExpressionBuiltinLocals() or \
           node.isExpressionBuiltinDir0() or node.isExpressionBuiltinVars():
        return False
    else:
        # assert False, node
        return True

class CPythonStatementExec( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "STATEMENT_EXEC"

    named_children = ( "source", "globals", "locals" )

    def __init__( self, source_code, globals_arg, locals_arg, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "globals" : globals_arg,
                "locals"  : locals_arg,
                "source"  : source_code
            }
        )

    def setChild( self, name, value ):
        if name in ( "globals", "locals" ):
            value = convertNoneConstantToNone( value )

        return CPythonChildrenHaving.setChild( self, name, value )

    getSourceCode = CPythonChildrenHaving.childGetter( "source" )
    getGlobals = CPythonChildrenHaving.childGetter( "globals" )
    getLocals = CPythonChildrenHaving.childGetter( "locals" )

    def needsLocalsDict( self ):
        return _couldBeNone( self.getGlobals() ) or \
               self.getGlobals().isExpressionBuiltinLocals() or \
               self.getLocals() is not None and self.getLocals().isExpressionBuiltinLocals()


# TODO: This is totally bitrot
class CPythonStatementExecInline( CPythonChildrenHaving, CPythonClosureTaker, CPythonClosureGiverNodeBase ):
    kind = "STATEMENT_EXEC_INLINE"

    named_children = ( "body", )

    early_closure = True

    def __init__( self, provider, source_ref ):
        CPythonClosureTaker.__init__( self, provider )
        CPythonClosureGiverNodeBase.__init__(
            self,
            name        = "exec_inline",
            code_prefix = "exec_inline",
            source_ref  = source_ref
        )

        CPythonChildrenHaving.__init__(
            self,
            values = {}
        )

    getBody = CPythonChildrenHaving.childGetter( "body" )
    setBody = CPythonChildrenHaving.childSetter( "body" )

    def getVariableForAssignment( self, variable_name ):
        # print ( "ASS inline", self, variable_name )

        if self.hasProvidedVariable( variable_name ):
            return self.getProvidedVariable( variable_name )

        result = self.getProvidedVariable( variable_name )

        # Remember that we need that closure for something.
        self.registerProvidedVariable( result )

        # print ( "RES inline", result )

        return result

    def getVariableForReference( self, variable_name ):
        # print ( "REF inline", self, variable_name )

        result = self.getVariableForAssignment( variable_name )

        # print ( "RES inline", result )

        return result

    def createProvidedVariable( self, variable_name ):
        # print ( "CREATE inline", self, variable_name )

        # An exec in a module gives a module variable always, on the top level
        # of an exec, if it's not already a global through a global statement,
        # the parent receives a local variable now.
        if self.provider.isModule():
            return self.provider.getProvidedVariable(
                variable_name = variable_name
            )
        else:
            return Variables.LocalVariable(
                owner         = self.provider,
                variable_name = variable_name
            )

    def needsLocalsDict( self ):
        return True
