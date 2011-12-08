#  Copyright 2008-2011 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from robot.reporting.jsondump import JsonDumper


class ScriptBlockWriter(object):
    _OUTPUT = 'window.output'
    _SETTINGS = 'window.settings'
    _SUITE_KEY = 'suite'
    _STRINGS_KEY = 'strings'

    def __init__(self, separator, split_threshold=9500):
        self._separator = separator
        self._split_threshold = split_threshold

    def write_to(self, output, model, config):
        writer = SeparatingWriter(output, self._separator)
        writer.write(self._OUTPUT+' = {};\n')
        writer.separator()
        self._write_suite(writer, model.suite)
        writer.separator()
        self._write_strings(model.strings, writer)
        writer.separator()
        for key, value in model.data.items():
            writer.dump_json(self._output_var(key)+' = ', value)
            writer.separator()
        writer.dump_json(self._SETTINGS+' = ', config)

    def _write_suite(self, writer, suite):
        split_writer = SplittingSuiteWriter(writer, self._split_threshold)
        mapping = split_writer.write(suite)
        writer.dump_json(self._output_var(self._SUITE_KEY)+' = ', suite, mapping=mapping)

    def _output_var(self, key):
        return self._OUTPUT+'["%s"]' % key

    def _write_strings(self, strings, writer):
        writer.write(self._output_var(self._STRINGS_KEY)+' = [];\n')
        while strings:
            writer.separator()
            writer.dump_json(self._output_var(self._STRINGS_KEY)
                             +' = '+self._output_var(self._STRINGS_KEY)
                             +'.concat(', strings[:self._split_threshold], ');\n')
            strings = strings[self._split_threshold:]


class SeparatingWriter(object):

    def __init__(self, output, separator=''):
        self._dumper = JsonDumper(output)
        self._separator = separator

    def separator(self):
        self._dumper.write(self._separator)

    def dump_json(self, prefix, data, postfix=';\n', mapping=None):
        if prefix:
            self.write(prefix)
        self._dumper.dump(data, mapping)
        self.write(postfix)

    def write(self, string):
        self._dumper.write(string)

#TODO: Naming
class SplittingSuiteWriter(object):

    def __init__(self, writer, split_threshold):
        self._index = 0
        self._writer = writer
        self._split_threshold = split_threshold

    def write(self, data_block):
        mapping = {}
        self._write(data_block, mapping)
        return mapping

    def _write(self, data, mapping, size=1):
        if not isinstance(data, tuple):
            return size
        for item in data:
            size += self._write(item, mapping)
        if size > self._split_threshold:
            self._dump_suite_part(mapping, data)
            return 1
        return size

    @property
    def _list_name(self):
        return 'window.sPart%s' % self._index

    def _dump_suite_part(self, mapping, data_block):
        self._writer.dump_json(self._list_name+' = ', data_block,
                               mapping=mapping)
        self._writer.separator()
        mapping[data_block] = self._list_name
        self._index += 1
