from pathlib import Path

from .leavedonto import LeavedOnto
from .tag_to_onto import generate_to_tag, tagged_to_trie, get_entries


class OntoManager:
    def __init__(self, onto_basis):
        self.onto1 = LeavedOnto(onto_basis)

    def diff_ontos(self, onto2, mode="all"):
        """

        :param onto2: path to onto to diff
        :param mode: all, base_only, other_only, shared
        :return:
        """
        if isinstance(onto2, LeavedOnto):
            other_onto = onto2
        elif isinstance(onto2, Path):
            other_onto = LeavedOnto(onto2)
        else:
            raise TypeError(
                "to_diff should be either a Path object, or a LeavedOnto object"
            )

        base_only, shared, other_only = self.__find_differences(other_onto, mode=mode)

        if mode == "all":
            return base_only, shared, other_only
        elif mode == "base_only":
            return base_only
        elif mode == "other_only":
            return other_only
        elif mode == "shared":
            return shared
        else:
            raise SyntaxError("either all, base_only, other_only or shared")

    def tag_segmented(self, in_file, out_file=None):
        generate_to_tag(in_file, self.onto1, out_file=out_file)

    def onto_from_tagged(self, in_file, out_file=None):
        # first merge all ontos you want, then generate onto from tagged

        # load words and tags
        tagged = get_entries(in_file)
        # generate trie
        trie = tagged_to_trie(tagged, self.onto1)
        # write it to out_file
        if not out_file:
            out_file = in_file.parent / (in_file.stem + "_onto.yaml")
        onto = LeavedOnto(trie, out_file)
        onto.convert2yaml()

    @staticmethod
    def __expand_search_results(res):
        return [(path, e) for path, entries in res for e in entries]

    def __find_differences(self, onto2, mode="all"):
        entries_base = self.__expand_search_results(self.onto1.ont.find_entries())
        entries_other = self.__expand_search_results(onto2.ont.find_entries())

        only_in_base, only_in_other, shared = None, None, None
        if mode == "all" or mode == "base_only":
            only_in_base = [e for e in entries_base if e not in entries_other]
        if mode == "all" or mode == "other_only":
            only_in_other = [e for e in entries_other if e not in entries_base]
        if mode == "all" or mode == "shared":
            shared = [e for e in entries_other if e in entries_base]

        return only_in_base, shared, only_in_other

    def batch_merge_to_onto(self, onto_list, in_to_organize=False):
        for onto in onto_list:
            self.merge_to_onto(onto, in_to_organize=in_to_organize)

    def merge_to_onto(self, onto2, in_to_organize=False):
        # add to onto1 the entries that are only in onto2
        onto2 = LeavedOnto(onto2)
        if sorted(onto2.ont.legend) != sorted(self.onto1.ont.legend):
            raise SyntaxError(
                "the two ontos need to have the same elements in the legend, in the same order."
                "\nPlease retry after that."
            )

        to_merge = self.diff_ontos(onto2, mode="other_only")

        # add origin to entries
        for i, t in enumerate(to_merge):
            path, entry = t[0], t[1]
            self.onto1.set_field_value(
                entry, "origin", onto2.ont_path.stem.split("_")[0]
            )

        if in_to_organize:
            for i in range(len(to_merge)):
                to_merge[i] = (["to_organize"] + to_merge[i][0], to_merge[i][1])

        for path, entry in to_merge:
            self.onto1.ont.add(path, entry)

    def _entry_list2dict(self, entry):
        p, e = entry["path"], entry["entry"]
        e = self.__leaf_dict2list(e)
        new = {}
        for n, el in enumerate(reversed(p)):
            if n == 0:
                new[el] = e
            else:
                new = {el: new}
        return new

    def __leaf_dict2list(self, leaf):
        return [leaf[L] for L in self.onto1.ont["legend"]]

    def _filter_entries(self, onto):
        def has_same_path(r_):
            out = [True for rr in ref_res if rr["path"] == r_["path"]]
            return True if out else False

        def has_same_lemma(r_):
            out = [
                True
                for rr in ref_res
                if rr["entry"]["col1_legend"] == r_["entry"]["col1_legend"]
            ]
            return True if out else False

        to_update = []
        to_organize = []
        words = onto.list_words()
        for w in words:
            res = onto.find_word(w)
            ref_res = self.onto1.find_word(w)
            for r in res:
                if r in ref_res:
                    continue
                elif has_same_path(r) and has_same_lemma(r):
                    to_update.append(r)
                else:
                    to_organize.append(r)
        return to_update, to_organize
