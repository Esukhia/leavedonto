from pathlib import Path
from itertools import zip_longest

import yaml

from .load_xlsx import LoadXlsx
from .triedicts import DictsToTrie
from .convert2xlsx import Convert2Xlsx
from .convert2yaml import Convert2Yaml
from .sort_bo_lists import SortBoLists
from .trie import OntTrie


class LeavedOnto:
    def __init__(self, ont, ont_path=None):
        self.ont_path = ont
        self.ont = None
        if isinstance(ont, str) or isinstance(ont, Path):
            self.ont_path = Path(ont)
            self._load()
        elif isinstance(ont, dict):
            dt = DictsToTrie(ont)
            self.ont = dt.trie
            self.ont_path = ont_path
        elif isinstance(ont, OntTrie):
            self.ont = ont
            self.ont_path = ont_path
        else:
            ValueError("either a dict or a filename or an OntTrie object")

        self._cleanup()

    def convert2xlsx(self, out_path=None):
        cx = Convert2Xlsx(self.ont_path, self.ont)
        cx.convert2xlsx(out_path)

    def convert2yaml(self, out_path=None):
        cy = Convert2Yaml(self.ont_path, self.ont)
        cy.convert2yaml(out_path)

    def find_word(self, word):
        return self.ont.find_entries(lemma=word)

    def get_field_value(self, entry, field):
        if field not in self.ont.legend:
            raise IndexError(f"{field} not contained in legend:\n{self.ont.legend}")
        for legend, value in zip_longest(self.ont.legend, entry):
            if legend == field:
                return value
        return None

    def set_field_value(self, entry, field, value, mode="append"):
        if mode != "replace" and mode != "append":
            raise ValueError('mode can be "replace" or "append"')
        if field not in self.ont.legend:
            raise IndexError(f"{field} not contained in legend:\n{self.ont.legend}")

        for i, legend in enumerate(self.ont.legend):
            if legend == field:
                if mode == "replace":
                    entry[i] = value
                if mode == "append":
                    parts = entry[i].split(" — ")
                    parts.append(value)
                    parts = sorted([p for p in set(parts) if p])
                    entry[i] = " — ".join(parts)

    def _load(self):
        if self.ont_path.suffix == ".xlsx":
            lx = LoadXlsx(self.ont_path)
            self.ont = lx.load_xlsx()
        elif self.ont_path.suffix == ".yaml":
            self._load_yaml()
        else:
            raise ValueError("only supports xlsx and yaml files.")

    def _load_yaml(self):
        ont_yaml = yaml.safe_load(self.ont_path.read_text())
        dt = DictsToTrie(ont_yaml)
        self.ont = dt.trie

    def _cleanup(self):
        queue = [self.ont.head]
        while queue:
            current_node = queue.pop()
            if current_node.leaf:
                # remove duplicates and sort in tibetan order
                no_dups = [list(L) for L in set(map(tuple, current_node.data))]
                sorted_ = SortBoLists().sort_list_of_lists(no_dups)
                current_node.data = sorted_

            queue = [node for key, node in current_node.children.items()] + queue
