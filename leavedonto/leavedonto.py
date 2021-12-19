from pathlib import Path

import yaml

from .load_xlsx import LoadXlsx
from .convert2xlsx import Convert2Xlsx
from .convert2yaml import Convert2Yaml
from .sort_bo_lists import SortBoLists


class OntoBasis:
    def __init__(self, ont, ont_path=None):
        self.ont_path = ont
        self.ont = {'ont': None, 'legend': None}
        if isinstance(ont, str) or isinstance(ont, Path):
            self.ont_path = Path(ont)
            self._load()
        elif isinstance(ont, dict):
            self.ont = ont
            self.ont_path = ont_path
        else:
            ValueError('either a dict or a filename')

    def _load(self):
        if self.ont_path.suffix == '.xlsx':
            lx = LoadXlsx(self.ont_path)
            self.ont = lx.load_xlsx()
        elif self.ont_path.suffix == '.yaml':
            self._load_yaml()
        else:
            raise ValueError('only supports xlsx and yaml files.')

    def _load_yaml(self):
        self.ont = yaml.safe_load(self.ont_path.read_text())

    def recursive_walk(self, input, func=None):
        """
        walks through the whole nested dict and applies the given function.
        If no function is provided, prints keys and values.
        :param input: nested dicts
        :param func: function to be applied
        """
        for key, value in input.items():
            if isinstance(value, dict):
                self.recursive_walk(value, func)
            else:
                if func:
                    func(input, key, value)
                else:
                    print(key, value)

    @staticmethod
    def process_value(func):
        def process(dictionary, key, value):
            if value:
                dictionary[key] = func(value)
            else:
                print(f'"{key}" is empty.')

        return process


class LeavedOnto(OntoBasis):
    def __init__(self, ont, ont_path=None):
        super().__init__(ont, ont_path=ont_path)
        self.convert2xlsx = Convert2Xlsx(self.ont_path, self.ont).convert2xlsx
        self.convert2yaml = Convert2Yaml(self.ont_path, self.ont).convert2yaml

        self._remove_duplicates()
        self._bo_sort()

    def get_leaf_value(self, leaf, v_name):
        idx = {l: n for n, l in enumerate(self.ont['legend'])}
        return leaf[idx[v_name]]

    def get_entries(self, onto, path, word, found):
        for key, value in onto.items():
            path.append(key)
            if isinstance(value, dict):
                self.get_entries(value, path, word, found)
            else:
                for entry in value:
                    if entry[0] == word:
                        occ = {'path': path, 'entry': entry}
                        found.append(occ)
                path = []

    def _remove_duplicates(self):
        def remove_dups(sheet):
            filtered = []
            for line in sheet:
                if line not in filtered:
                    filtered.append(line)
            return filtered

        self._process_leaves(remove_dups)

    def _bo_sort(self):
        def bo_sort(sheet):
            return SortBoLists().sort_list_of_lists(sheet)

        self._process_leaves(bo_sort)

    def _process_leaves(self, func):
        """
        apply a function to all the leaves of the ontology
        :param func:
        :return:
        """
        return self.recursive_walk(self.ont['ont'], self.process_value(func))