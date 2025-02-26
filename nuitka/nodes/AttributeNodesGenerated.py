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
"""Specialized attribute nodes

WARNING, this code is GENERATED. Modify the template AttributeNodeFixed.py.j2 instead!
"""

from nuitka.specs.BuiltinParameterSpecs import extractBuiltinArgs

from .AttributeLookupNodes import ExpressionAttributeLookupFixedBase
from .NodeBases import SideEffectsFromChildrenMixin

attribute_classes = {}
attribute_typed_classes = {}


class ExpressionAttributeLookupFixedClear(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Clear of an object.

    Typically code like: source.clear
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_CLEAR"
    attribute_name = "clear"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictClear(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'clear' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="clear",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="clear"
        )


attribute_classes["clear"] = ExpressionAttributeLookupFixedClear


from nuitka.specs.BuiltinDictOperationSpecs import dict_clear_spec


class ExpressionAttributeLookupDictClear(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedClear
):
    """Attribute Clear lookup on a dict.

    Typically code like: some_dict.clear
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_CLEAR"
    attribute_name = "clear"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationClear(source_ref):
            from .DictionaryNodes import ExpressionDictOperationClear

            return ExpressionDictOperationClear(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationClear,
            builtin_spec=dict_clear_spec,
        )

        return result, "new_expression", "Call to 'clear' of dictionary recognized."


attribute_typed_classes["clear"] = ExpressionAttributeLookupDictClear


class ExpressionAttributeLookupFixedCopy(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Copy of an object.

    Typically code like: source.copy
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_COPY"
    attribute_name = "copy"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictCopy(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'copy' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="copy",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="copy"
        )


attribute_classes["copy"] = ExpressionAttributeLookupFixedCopy


from nuitka.specs.BuiltinDictOperationSpecs import dict_copy_spec


class ExpressionAttributeLookupDictCopy(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedCopy
):
    """Attribute Copy lookup on a dict.

    Typically code like: some_dict.copy
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_COPY"
    attribute_name = "copy"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationCopy(source_ref):
            from .DictionaryNodes import ExpressionDictOperationCopy

            return ExpressionDictOperationCopy(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationCopy,
            builtin_spec=dict_copy_spec,
        )

        return result, "new_expression", "Call to 'copy' of dictionary recognized."


attribute_typed_classes["copy"] = ExpressionAttributeLookupDictCopy


class ExpressionAttributeLookupFixedFromkeys(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Fromkeys of an object.

    Typically code like: source.fromkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_FROMKEYS"
    attribute_name = "fromkeys"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictFromkeys(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'fromkeys' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="fromkeys",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="fromkeys"
        )


attribute_classes["fromkeys"] = ExpressionAttributeLookupFixedFromkeys


class ExpressionAttributeLookupDictFromkeys(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedFromkeys
):
    """Attribute Fromkeys lookup on a dict.

    Typically code like: some_dict.fromkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_FROMKEYS"
    attribute_name = "fromkeys"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as dict operation ExpressionDictOperationFromkeys is not yet implemented


attribute_typed_classes["fromkeys"] = ExpressionAttributeLookupDictFromkeys


class ExpressionAttributeLookupFixedGet(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Get of an object.

    Typically code like: source.get
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_GET"
    attribute_name = "get"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictGet(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'get' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="get",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="get"
        )


attribute_classes["get"] = ExpressionAttributeLookupFixedGet


from nuitka.specs.BuiltinDictOperationSpecs import dict_get_spec


class ExpressionAttributeLookupDictGet(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedGet
):
    """Attribute Get lookup on a dict.

    Typically code like: some_dict.get
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_GET"
    attribute_name = "get"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationGet(key, default, source_ref):
            if default is not None:
                from .DictionaryNodes import ExpressionDictOperationGet3

                return ExpressionDictOperationGet3(
                    dict_arg=self.subnode_expression,
                    key=key,
                    default=default,
                    source_ref=source_ref,
                )
            else:
                from .DictionaryNodes import ExpressionDictOperationGet2

                return ExpressionDictOperationGet2(
                    dict_arg=self.subnode_expression, key=key, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationGet,
            builtin_spec=dict_get_spec,
        )

        return result, "new_expression", "Call to 'get' of dictionary recognized."


attribute_typed_classes["get"] = ExpressionAttributeLookupDictGet


class ExpressionAttributeLookupFixedHaskey(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Haskey of an object.

    Typically code like: source.has_key
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_HASKEY"
    attribute_name = "has_key"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictHaskey(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'has_key' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="has_key",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="has_key"
        )


attribute_classes["has_key"] = ExpressionAttributeLookupFixedHaskey


from nuitka.specs.BuiltinDictOperationSpecs import dict_has_key_spec


class ExpressionAttributeLookupDictHaskey(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedHaskey
):
    """Attribute Haskey lookup on a dict.

    Typically code like: some_dict.has_key
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_HASKEY"
    attribute_name = "has_key"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationHaskey(key, source_ref):
            from .DictionaryNodes import ExpressionDictOperationHaskey

            return ExpressionDictOperationHaskey(
                dict_arg=self.subnode_expression, key=key, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationHaskey,
            builtin_spec=dict_has_key_spec,
        )

        return result, "new_expression", "Call to 'has_key' of dictionary recognized."


attribute_typed_classes["has_key"] = ExpressionAttributeLookupDictHaskey


class ExpressionAttributeLookupFixedItems(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Items of an object.

    Typically code like: source.items
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ITEMS"
    attribute_name = "items"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictItems(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'items' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="items",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="items"
        )


attribute_classes["items"] = ExpressionAttributeLookupFixedItems


from nuitka.specs.BuiltinDictOperationSpecs import dict_items_spec


class ExpressionAttributeLookupDictItems(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedItems
):
    """Attribute Items lookup on a dict.

    Typically code like: some_dict.items
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_ITEMS"
    attribute_name = "items"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationItems(source_ref):
            if str is bytes:
                from .DictionaryNodes import ExpressionDictOperationItems

                return ExpressionDictOperationItems(
                    dict_arg=self.subnode_expression, source_ref=source_ref
                )
            else:
                from .DictionaryNodes import ExpressionDictOperationIteritems

                return ExpressionDictOperationIteritems(
                    dict_arg=self.subnode_expression, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationItems,
            builtin_spec=dict_items_spec,
        )

        return result, "new_expression", "Call to 'items' of dictionary recognized."


attribute_typed_classes["items"] = ExpressionAttributeLookupDictItems


class ExpressionAttributeLookupFixedIteritems(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Iteritems of an object.

    Typically code like: source.iteritems
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ITERITEMS"
    attribute_name = "iteritems"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictIteritems(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'iteritems' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="iteritems",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="iteritems"
        )


attribute_classes["iteritems"] = ExpressionAttributeLookupFixedIteritems


from nuitka.specs.BuiltinDictOperationSpecs import dict_iteritems_spec


class ExpressionAttributeLookupDictIteritems(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIteritems
):
    """Attribute Iteritems lookup on a dict.

    Typically code like: some_dict.iteritems
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_ITERITEMS"
    attribute_name = "iteritems"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationIteritems(source_ref):
            from .DictionaryNodes import ExpressionDictOperationIteritems

            return ExpressionDictOperationIteritems(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationIteritems,
            builtin_spec=dict_iteritems_spec,
        )

        return result, "new_expression", "Call to 'iteritems' of dictionary recognized."


attribute_typed_classes["iteritems"] = ExpressionAttributeLookupDictIteritems


class ExpressionAttributeLookupFixedIterkeys(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Iterkeys of an object.

    Typically code like: source.iterkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ITERKEYS"
    attribute_name = "iterkeys"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictIterkeys(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'iterkeys' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="iterkeys",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="iterkeys"
        )


attribute_classes["iterkeys"] = ExpressionAttributeLookupFixedIterkeys


from nuitka.specs.BuiltinDictOperationSpecs import dict_iterkeys_spec


class ExpressionAttributeLookupDictIterkeys(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedIterkeys
):
    """Attribute Iterkeys lookup on a dict.

    Typically code like: some_dict.iterkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_ITERKEYS"
    attribute_name = "iterkeys"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationIterkeys(source_ref):
            from .DictionaryNodes import ExpressionDictOperationIterkeys

            return ExpressionDictOperationIterkeys(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationIterkeys,
            builtin_spec=dict_iterkeys_spec,
        )

        return result, "new_expression", "Call to 'iterkeys' of dictionary recognized."


attribute_typed_classes["iterkeys"] = ExpressionAttributeLookupDictIterkeys


class ExpressionAttributeLookupFixedItervalues(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Itervalues of an object.

    Typically code like: source.itervalues
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_ITERVALUES"
    attribute_name = "itervalues"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictItervalues(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'itervalues' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="itervalues",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="itervalues"
        )


attribute_classes["itervalues"] = ExpressionAttributeLookupFixedItervalues


from nuitka.specs.BuiltinDictOperationSpecs import dict_itervalues_spec


class ExpressionAttributeLookupDictItervalues(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedItervalues
):
    """Attribute Itervalues lookup on a dict.

    Typically code like: some_dict.itervalues
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_ITERVALUES"
    attribute_name = "itervalues"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationItervalues(source_ref):
            from .DictionaryNodes import ExpressionDictOperationItervalues

            return ExpressionDictOperationItervalues(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationItervalues,
            builtin_spec=dict_itervalues_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'itervalues' of dictionary recognized.",
        )


attribute_typed_classes["itervalues"] = ExpressionAttributeLookupDictItervalues


class ExpressionAttributeLookupFixedKeys(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Keys of an object.

    Typically code like: source.keys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_KEYS"
    attribute_name = "keys"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictKeys(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'keys' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="keys",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="keys"
        )


attribute_classes["keys"] = ExpressionAttributeLookupFixedKeys


from nuitka.specs.BuiltinDictOperationSpecs import dict_keys_spec


class ExpressionAttributeLookupDictKeys(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedKeys
):
    """Attribute Keys lookup on a dict.

    Typically code like: some_dict.keys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_KEYS"
    attribute_name = "keys"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationKeys(source_ref):
            if str is bytes:
                from .DictionaryNodes import ExpressionDictOperationKeys

                return ExpressionDictOperationKeys(
                    dict_arg=self.subnode_expression, source_ref=source_ref
                )
            else:
                from .DictionaryNodes import ExpressionDictOperationIterkeys

                return ExpressionDictOperationIterkeys(
                    dict_arg=self.subnode_expression, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationKeys,
            builtin_spec=dict_keys_spec,
        )

        return result, "new_expression", "Call to 'keys' of dictionary recognized."


attribute_typed_classes["keys"] = ExpressionAttributeLookupDictKeys


class ExpressionAttributeLookupFixedPop(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Pop of an object.

    Typically code like: source.pop
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_POP"
    attribute_name = "pop"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictPop(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'pop' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="pop",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="pop"
        )


attribute_classes["pop"] = ExpressionAttributeLookupFixedPop


from nuitka.specs.BuiltinDictOperationSpecs import dict_pop_spec


class ExpressionAttributeLookupDictPop(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedPop
):
    """Attribute Pop lookup on a dict.

    Typically code like: some_dict.pop
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_POP"
    attribute_name = "pop"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationPop(key, default, source_ref):
            if default is not None:
                from .DictionaryNodes import ExpressionDictOperationPop3

                return ExpressionDictOperationPop3(
                    dict_arg=self.subnode_expression,
                    key=key,
                    default=default,
                    source_ref=source_ref,
                )
            else:
                from .DictionaryNodes import ExpressionDictOperationPop2

                return ExpressionDictOperationPop2(
                    dict_arg=self.subnode_expression, key=key, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationPop,
            builtin_spec=dict_pop_spec,
        )

        return result, "new_expression", "Call to 'pop' of dictionary recognized."


attribute_typed_classes["pop"] = ExpressionAttributeLookupDictPop


class ExpressionAttributeLookupFixedPopitem(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Popitem of an object.

    Typically code like: source.popitem
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_POPITEM"
    attribute_name = "popitem"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictPopitem(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'popitem' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="popitem",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="popitem"
        )


attribute_classes["popitem"] = ExpressionAttributeLookupFixedPopitem


class ExpressionAttributeLookupDictPopitem(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedPopitem
):
    """Attribute Popitem lookup on a dict.

    Typically code like: some_dict.popitem
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_POPITEM"
    attribute_name = "popitem"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as dict operation ExpressionDictOperationPopitem is not yet implemented


attribute_typed_classes["popitem"] = ExpressionAttributeLookupDictPopitem


class ExpressionAttributeLookupFixedSetdefault(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Setdefault of an object.

    Typically code like: source.setdefault
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_SETDEFAULT"
    attribute_name = "setdefault"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictSetdefault(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'setdefault' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="setdefault",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="setdefault"
        )


attribute_classes["setdefault"] = ExpressionAttributeLookupFixedSetdefault


from nuitka.specs.BuiltinDictOperationSpecs import dict_setdefault_spec


class ExpressionAttributeLookupDictSetdefault(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedSetdefault
):
    """Attribute Setdefault lookup on a dict.

    Typically code like: some_dict.setdefault
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_SETDEFAULT"
    attribute_name = "setdefault"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationSetdefault(key, default, source_ref):
            if default is not None:
                from .DictionaryNodes import ExpressionDictOperationSetdefault3

                return ExpressionDictOperationSetdefault3(
                    dict_arg=self.subnode_expression,
                    key=key,
                    default=default,
                    source_ref=source_ref,
                )
            else:
                from .DictionaryNodes import ExpressionDictOperationSetdefault2

                return ExpressionDictOperationSetdefault2(
                    dict_arg=self.subnode_expression, key=key, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationSetdefault,
            builtin_spec=dict_setdefault_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'setdefault' of dictionary recognized.",
        )


attribute_typed_classes["setdefault"] = ExpressionAttributeLookupDictSetdefault


class ExpressionAttributeLookupFixedUpdate(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Update of an object.

    Typically code like: source.update
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_UPDATE"
    attribute_name = "update"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictUpdate(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'update' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="update",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="update"
        )


attribute_classes["update"] = ExpressionAttributeLookupFixedUpdate


class ExpressionAttributeLookupDictUpdate(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedUpdate
):
    """Attribute Update lookup on a dict.

    Typically code like: some_dict.update
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_UPDATE"
    attribute_name = "update"

    def computeExpression(self, trace_collection):
        return self, None, None

    # No computeExpressionCall as dict operation ExpressionDictOperationUpdate is not yet implemented


attribute_typed_classes["update"] = ExpressionAttributeLookupDictUpdate


class ExpressionAttributeLookupFixedValues(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Values of an object.

    Typically code like: source.values
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_VALUES"
    attribute_name = "values"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictValues(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'values' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="values",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="values"
        )


attribute_classes["values"] = ExpressionAttributeLookupFixedValues


from nuitka.specs.BuiltinDictOperationSpecs import dict_values_spec


class ExpressionAttributeLookupDictValues(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedValues
):
    """Attribute Values lookup on a dict.

    Typically code like: some_dict.values
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_VALUES"
    attribute_name = "values"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationValues(source_ref):
            if str is bytes:
                from .DictionaryNodes import ExpressionDictOperationValues

                return ExpressionDictOperationValues(
                    dict_arg=self.subnode_expression, source_ref=source_ref
                )
            else:
                from .DictionaryNodes import ExpressionDictOperationItervalues

                return ExpressionDictOperationItervalues(
                    dict_arg=self.subnode_expression, source_ref=source_ref
                )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationValues,
            builtin_spec=dict_values_spec,
        )

        return result, "new_expression", "Call to 'values' of dictionary recognized."


attribute_typed_classes["values"] = ExpressionAttributeLookupDictValues


class ExpressionAttributeLookupFixedViewitems(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Viewitems of an object.

    Typically code like: source.viewitems
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_VIEWITEMS"
    attribute_name = "viewitems"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictViewitems(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'viewitems' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="viewitems",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="viewitems"
        )


attribute_classes["viewitems"] = ExpressionAttributeLookupFixedViewitems


from nuitka.specs.BuiltinDictOperationSpecs import dict_viewitems_spec


class ExpressionAttributeLookupDictViewitems(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedViewitems
):
    """Attribute Viewitems lookup on a dict.

    Typically code like: some_dict.viewitems
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_VIEWITEMS"
    attribute_name = "viewitems"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationViewitems(source_ref):
            from .DictionaryNodes import ExpressionDictOperationViewitems

            return ExpressionDictOperationViewitems(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationViewitems,
            builtin_spec=dict_viewitems_spec,
        )

        return result, "new_expression", "Call to 'viewitems' of dictionary recognized."


attribute_typed_classes["viewitems"] = ExpressionAttributeLookupDictViewitems


class ExpressionAttributeLookupFixedViewkeys(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Viewkeys of an object.

    Typically code like: source.viewkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_VIEWKEYS"
    attribute_name = "viewkeys"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictViewkeys(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'viewkeys' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="viewkeys",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="viewkeys"
        )


attribute_classes["viewkeys"] = ExpressionAttributeLookupFixedViewkeys


from nuitka.specs.BuiltinDictOperationSpecs import dict_viewkeys_spec


class ExpressionAttributeLookupDictViewkeys(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedViewkeys
):
    """Attribute Viewkeys lookup on a dict.

    Typically code like: some_dict.viewkeys
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_VIEWKEYS"
    attribute_name = "viewkeys"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationViewkeys(source_ref):
            from .DictionaryNodes import ExpressionDictOperationViewkeys

            return ExpressionDictOperationViewkeys(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationViewkeys,
            builtin_spec=dict_viewkeys_spec,
        )

        return result, "new_expression", "Call to 'viewkeys' of dictionary recognized."


attribute_typed_classes["viewkeys"] = ExpressionAttributeLookupDictViewkeys


class ExpressionAttributeLookupFixedViewvalues(ExpressionAttributeLookupFixedBase):
    """Looking up an attribute value Viewvalues of an object.

    Typically code like: source.viewvalues
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_FIXED_VIEWVALUES"
    attribute_name = "viewvalues"

    def computeExpression(self, trace_collection):
        subnode_expression = self.subnode_expression

        if str is bytes and subnode_expression.hasShapeDictionaryExact():
            result = ExpressionAttributeLookupDictViewvalues(
                expression=subnode_expression, source_ref=self.source_ref
            )

            return (
                result,
                "new_expression",
                "Attribute lookup 'viewvalues' on dict shape resolved.",
            )

        return subnode_expression.computeExpressionAttribute(
            lookup_node=self,
            attribute_name="viewvalues",
            trace_collection=trace_collection,
        )

    def mayRaiseException(self, exception_type):
        return self.subnode_expression.mayRaiseExceptionAttributeLookup(
            exception_type=exception_type, attribute_name="viewvalues"
        )


attribute_classes["viewvalues"] = ExpressionAttributeLookupFixedViewvalues


from nuitka.specs.BuiltinDictOperationSpecs import dict_viewvalues_spec


class ExpressionAttributeLookupDictViewvalues(
    SideEffectsFromChildrenMixin, ExpressionAttributeLookupFixedViewvalues
):
    """Attribute Viewvalues lookup on a dict.

    Typically code like: some_dict.viewvalues
    """

    kind = "EXPRESSION_ATTRIBUTE_LOOKUP_DICT_VIEWVALUES"
    attribute_name = "viewvalues"

    def computeExpression(self, trace_collection):
        return self, None, None

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        def wrapExpressionDictOperationViewvalues(source_ref):
            from .DictionaryNodes import ExpressionDictOperationViewvalues

            return ExpressionDictOperationViewvalues(
                dict_arg=self.subnode_expression, source_ref=source_ref
            )

        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=wrapExpressionDictOperationViewvalues,
            builtin_spec=dict_viewvalues_spec,
        )

        return (
            result,
            "new_expression",
            "Call to 'viewvalues' of dictionary recognized.",
        )


attribute_typed_classes["viewvalues"] = ExpressionAttributeLookupDictViewvalues
