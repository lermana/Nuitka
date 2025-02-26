#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
from __future__ import print_function

# nuitka-project: --nofollow-import-to=numpy
import numpy


g = 6

def calledRepeatedly():
    y = numpy.array([[1, 2, 3], [4, 5, 6]], numpy.int32)
    # This is supposed to make a call to a compiled function, which is
    # being optimized separately.
# construct_begin
    x = numpy.array([[1, 2, 3], [4, 5, 6]], numpy.int32)
# construct_alternative
    x = g
# construct_end

    return x, y

import itertools
for x in itertools.repeat(None, 20000):
    calledRepeatedly()

print("OK.")
