#!/usr/bin/env python3

"""
File:   main.py
Author: Thibault Douzon
Date:   2020-04-29
        12:01:14
mail:   douzont@gmail.com
"""


import argparse
import itertools as it
import json
import math
import pickle
import warnings

from collections import deque, namedtuple, Counter
from dataclasses import dataclass
from functools import reduce, lru_cache
from pprint import pprint
from operator import mul
from os import path
from typing import *

# This code uses informations provided by this source: https://docs.google.com/document/d/1ARIQCUc5YVEd01D7jtJT9EEJF45m07NXhAm4fOpNvCs/mobilebasic
# All flowers rules are explained deeply an thoroughly inside.

FlowerType = NewType("FlowerType", str)
FlowerColor = NewType("FlowerColor", str)
ColorSeedIsland = namedtuple("ColorSeedIsland", "color seed island")

# Mixing rules for any genes.
# (gene_flower_1, gene_flower_2): [(gene_hybrid_flower, probability of apparition)]
mix_d = {
    (0, 0): [(0, 1.0)],
    (1, 0): [(0, 0.5), (1, 0.5)],
    (0, 1): [(0, 0.5), (1, 0.5)],
    (1, 1): [(0, 0.25), (1, 0.5), (2, 0.25)],
    (2, 0): [(1, 1.0)],
    (0, 2): [(1, 1.0)],
    (2, 1): [(1, 0.5), (2, 0.5)],
    (1, 2): [(1, 0.5), (2, 0.5)],
    (2, 2): [(2, 1.0)],
}


@lru_cache(maxsize=81 ** 2 + 27 ** 2)
def mix_flowers(f1, f2):
    """
    Memoized flower hybridation for speedup. Equivalent to a lookup table.
    Do not use as is, use Flower's addition to combine Flowers.
    """
    res_genes = (mix_d[g] for g in zip(f1, f2))

    res = []
    for p in it.product(*res_genes):
        genes, probs = zip(*p)
        prob = reduce(mul, probs)
        res.append((genes, prob))

    return res


class Flower:

    COSMOS = FlowerType("__COSMOS__")
    HYACINTHS = FlowerType("__HYACINTHS__")
    LILIES = FlowerType("__LILIES__")
    MUMS = FlowerType("__MUMS__")
    PANSIES = FlowerType("__PANSIES__")
    ROSES = FlowerType("__ROSES__")
    TULIPS = FlowerType("__TULIPS__")
    VIOLETS = FlowerType("__VIOLETS__")
    WINDFLOWERS = FlowerType("__WINDFLOWERS__")

    flowertypes = [
        COSMOS,
        HYACINTHS,
        LILIES,
        MUMS,
        PANSIES,
        ROSES,
        TULIPS,
        VIOLETS,
        WINDFLOWERS,
    ]

    BLACK = FlowerColor("Black")
    BLUE = FlowerColor("Blue")
    GREEN = FlowerColor("Green")
    PINK = FlowerColor("Pink")
    PURPLE = FlowerColor("Purple")
    ORANGE = FlowerColor("Orange")
    RED = FlowerColor("Red")
    YELLOW = FlowerColor("Yellow")
    WHITE = FlowerColor("White")

    flowercolors = [BLACK, BLUE, GREEN, PINK, PURPLE, ORANGE, RED, YELLOW, WHITE]

    # r y o w s
    flower_unused_gene: Dict[FlowerType, List[int]] = {
        COSMOS: [-3, -2],
        HYACINTHS: [-3, -1],
        LILIES: [-3, -2],
        MUMS: [-3, -1],
        PANSIES: [-3, -1],
        ROSES: [-3],
        TULIPS: [-3, -2],
        VIOLETS: [-3, -1],
        WINDFLOWERS: [-4, -1],
    }

    def __init__(self, flower_type: FlowerType, genes: Sequence[int]):
        """
        Create a Flower based on its genes.
        Genes are represented by a sequence of 3 or 4 integers 0⩽x_i⩽2
        """
        if flower_type == Flower.VIOLETS:
            warnings.warn(f"Flower type {flower_type} is not supported, gene data is missing in csv file.")
        assert len(genes) == 5 - len(Flower.flower_unused_gene[flower_type]), f"Expected genes length of {5 - len(Flower.flower_unused_gene[flower_type])}, got {len(genes)} instead."
        
        self.type = flower_type
        self.genes = tuple(genes)

        # self._hash = hash((self.type, self.genes))

    @property
    def color(self) -> FlowerColor:
        return FlowerColor(flower_info[self].color)

    @property
    def is_seed(self) -> bool:
        return bool(flower_info[self].seed)

    @property
    def is_island(self) -> bool:
        return bool(flower_info[self].island)

    @property
    def code(self) -> str:
        gene_name = [
            "rr Rr RR".split(),
            "yy Yy YY".split(),
            "oo Oo OO".split(),  # Replaces Y gene for Windflowers.
            "WW Ww ww".split(),  # 0 is dominant over 2 for W gene.
            "ss Ss SS".split(),
        ]

        # Some flowers don't use all genes.
        for i in Flower.flower_unused_gene[self.type]:
            del gene_name[i]

        res = []
        for i, g in enumerate(self.genes):
            res.append(gene_name[i][g])

        return " ".join(res)

    def __add__(self, other) -> List[Tuple["Flower", float]]:
        """
        Compute all possible hybrids (and their probability) generated by self and another Flower.
        Uses LRU cache for speedup.
        """
        if self.type != other.type:
            return []
        return [
            (Flower(self.type, g), p) for g, p in mix_flowers(self.genes, other.genes)
        ]

    def __eq__(self, other) -> bool:
        if isinstance(other, Flower):
            return self.genes == other.genes and self.type == other.type
        elif isinstance(other, Sequence):
            return self.genes == other
        return False

    def __lt__(self, other) -> bool:
        return (self.type, self.genes) < (other.type, other.genes)

    def __hash__(self):
        return hash((self.type, self.genes))

    def __str__(self) -> str:
        return f"({self.type} {self.code} {self.color} {self.genes} {self.is_seed})"

    def __repr__(self):
        return str(self)
        return f"Flower({self.type}, {self.genes})"


FlowerDB = NewType("FlowerDB", Dict[Flower, ColorSeedIsland])


def read_code(code: str) -> tuple:
    code = code.replace(" ", "")
    def helper(s, l):
        res = sum(1 for c in s if c.isupper())
        if l == "w":
            return 2 - res
        return res

    gene_code = []
    for i in range(0, len(code), 2):
        gene_code.append(helper(code[i : i + 2], code[i].lower()))
    
    return tuple(gene_code)


def load_flower_info(file_type_couples: List[Tuple[str, FlowerType]]) -> FlowerDB:
    """
    Reads a csv file containing color information about flowers.
    """
    d = FlowerDB({})

    for file, flower_type in file_type_couples:
        with open(path.join("data", file), "r") as fp:
            for line in fp.readlines():
                _, gene, *_, color_info = line.strip().split(",")

                gene_code = read_code(gene)

                c = FlowerColor(color_info.split()[0])
                is_seed = (
                    color_info.split()[1] == "(seed)"
                    if len(color_info.split()) > 1
                    else False
                )
                is_island = (
                    color_info.split()[1] == "(island)"
                    if len(color_info.split()) > 1
                    else False
                )

                # For violets
                if gene_code:
                    d[Flower(flower_type, tuple(gene_code))] = ColorSeedIsland(
                        c, is_seed, is_island
                    )

    return d


flower_info = load_flower_info(
    [
        ("cosmos.csv", Flower.COSMOS),
        ("hyacinths.csv", Flower.HYACINTHS),
        ("lilies.csv", Flower.LILIES),
        ("mums.csv", Flower.MUMS),
        ("pansies.csv", Flower.PANSIES),
        ("roses.csv", Flower.ROSES),
        ("tulips.csv", Flower.TULIPS),
        ("violets.csv", Flower.VIOLETS),
        ("windflowers.csv", Flower.WINDFLOWERS),
    ]
)


@dataclass
class HybridTestInfo:
    unknown_flower: Optional[Flower]
    test_flower: Optional[Flower]
    test_prob: float
    test_color: Optional[FlowerColor]


@dataclass
class AncestorInfo:
    parents: Optional[Tuple[Flower, Flower]]
    ancestors: Set[Flower]
    test: HybridTestInfo
    micro_prob: float
    no_test_global_prob: float

    @property
    def total_prob(self) -> float:
        if self.test:
            return self.test.test_prob * self.no_test_global_prob
        else:
            return self.no_test_global_prob


FlowerPedia = NewType("FlowerPedia", Dict[Flower, AncestorInfo],)


def universal_get(
    flower_info: FlowerDB,
    _type: Optional[FlowerType] = None,
    _color: Optional[FlowerColor] = None,
    _seed: Optional[bool] = None,
    _island: Optional[bool] = None,
) -> List[Flower]:

    res = []

    def test_cond(val, attr):
        def test(x, val=val, attr=attr):
            if val is None:
                return True
            if not isinstance(val, Sequence):
                val = [val]

            if getattr(x, attr) in val:
                return True
            return False

        return test

    tests_AND = [
        test_cond(_type, "type"),
        test_cond(_color, "color"),
        test_cond(_seed, "is_seed"),
        test_cond(_island, "is_island"),
    ]

    for flower in flower_info:
        if all(test(flower) for test in tests_AND):
            res.append(flower)
    return res


uget = universal_get


def prob_test_hybrid(
    f1: Flower, f2: Flower, f_h: Flower, known_flowers: Set[Flower]
) -> HybridTestInfo:
    f12 = f1 + f2
    assert f_h in (f[0] for f in f12), f"Flower {f_h} is not an hybrid of {f1} + {f2}."

    if f1.color == f2.color == f_h.color:
        # TODO FEAT???: Implement a test that blocks one flower and perform test to prove hybrid is not duplicate.
        return HybridTestInfo(unknown_flower=None, test_flower=None, test_prob=0., test_color=None)

    color_counter = Counter(f.color for f, _ in f12)
    if color_counter[f_h.color] == 1:
        return HybridTestInfo(unknown_flower=None, test_flower=None, test_prob=1.0, test_color=None)

    # return HybridTestInfo(test_flower=None, test_prob=0., test_color=None)

    # Now we need to test the flower because we are not sure.
    concurrent_flowers = [(f, p) for f, p in f12 if f.color == f_h.color and f != f_h]

    best_test_f = None
    best_p_color = 0.0
    best_color = None

    # Try to hybrid new flower with old (known_flowers).
    for other_f in known_flowers:
        h_colors = {f.color for f, p in f_h + other_f}

        concurrent_colors = {
            f.color for ff, pp in concurrent_flowers for f, p in ff + other_f
        }

        possible_test_colors = h_colors - concurrent_colors

        # We cannot be sure the popped flower is not a duplicate of any of the two (and we won't test it ;) ).
        if other_f.color == f_h.color and f_h.color in possible_test_colors:
            possible_test_colors.remove(f_h.color)

        if len(possible_test_colors) > 0:
            # There is some color that we can use.
            for test_color in possible_test_colors:
                p_color = sum(p for f, p in f_h + other_f if f.color == test_color)

                if p_color > best_p_color:
                    best_p_color = p_color
                    best_test_f = other_f
                    best_color = test_color

    # Try to hybrid new flower with self.
    f_h_colors = {f.color for f, p in f_h + f_h}
    for other_f, _ in concurrent_flowers:
        concurrent_colors = {f.color for f, p in other_f + other_f}

        possible_test_colors = (
            h_colors - concurrent_colors - {f_h.color,}
        )

        if len(possible_test_colors) > 0:
            for test_color in possible_test_colors:
                p_color = sum(p for f, p in f_h + f_h if f.color == test_color)

                if p_color > best_p_color:
                    best_p_color = p_color
                    best_test_f = f_h
                    best_color = test_color

    return HybridTestInfo(
        unknown_flower=f_h, test_flower=best_test_f, test_prob=best_p_color, test_color=best_color
    )


"""
p(f OK) = p(f color OK) * p(f OK | f color OK)

o for obtention
o(f OK & f test)    = o(f color ok) * o(f ok | f color OK) * o(f_test color | f OK & f color OK)
"""


def explore(base_flowers: List[Flower]) -> FlowerPedia:
    """
    Compute best path to obtain each flower using only `base_flowers`
    """
    flowerpedia = FlowerPedia(
        {
            f: AncestorInfo(
                parents=None,
                ancestors=set(),
                test=HybridTestInfo(None, None, 1, None),
                micro_prob=1.0,
                no_test_global_prob=1.0,
            )
            for f in base_flowers
        }
    )

    flower_l = base_flowers.copy()
    new_flowers = set(base_flowers)
    next_new_flowers: Set[Flower] = set()

    # Floyd Warshall algorithm with no negative cycles
    # Stop when no modification are made to the FlowerPedia

    modified = True
    i = 0

    while modified:
        i += 1
        modified = False

        for f1 in flowerpedia.copy():  # Iterate over all flowers seen so far
            dp_f1 = flowerpedia[f1]
            for f2 in new_flowers:
                if f1 in new_flowers and f1 > f2:
                    continue
                dp_f2 = flowerpedia[f2]

                # Compute unique flowers needed to produce f1 and f2
                pred_common = dp_f1.ancestors & dp_f2.ancestors
                prob_common = (
                    dp_f1.total_prob
                    * dp_f2.total_prob
                    / reduce(
                        mul,
                        (
                            flowerpedia[fi].micro_prob * flowerpedia[fi].test.test_prob
                            for fi in pred_common
                        ),
                        1.0,
                    )  # All flower in pred_common are counter twice in `prob_f1 * prob_f2`
                    # We must divide by `product(prob(i) for i in pred_common)`
                )

                for f, p in f1 + f2:
                    if f in (f1, f2):
                        continue
                    if f in flowerpedia and prob_common < flowerpedia[f].total_prob:
                        continue

                    h_ancestors = dp_f1.ancestors | dp_f2.ancestors | {f1, f2}

                    test_result = prob_test_hybrid(f1, f2, f, h_ancestors)

                    prob_f = prob_common * p * test_result.test_prob
                    if prob_f > 0:
                        # We want to maximize overall total probability of obtaining flower f.
                        if not f in flowerpedia or flowerpedia[f].total_prob < prob_f:
                            flowerpedia[f] = AncestorInfo(
                                parents=(f1, f2),
                                ancestors=h_ancestors,
                                test=test_result,
                                micro_prob=p,
                                no_test_global_prob=prob_common * p,
                            )
                            modified = True
                            next_new_flowers.add(f)

        # All flowers will be mixed with all updates flowers during next iteration of algorithm.
        new_flowers = next_new_flowers
        next_new_flowers = set()
    return flowerpedia


def ancestors(
    tgt: Flower, flowerpedia: FlowerPedia, mem: Dict[Flower, Dict] = None
) -> Dict[str, Any]:
    """
    Determines best way to obtain Flower `tgt` given a `flowerpedia`
    Recursively get ancestors of `tgt`in the FlowerPedia and aggregate results.
    """
    if mem is None:
        mem = {}
    # Memoization for speedup
    if tgt in mem:
        return mem[tgt]

    tgt_info = flowerpedia[tgt]

    if tgt_info.parents is None:
        return {"color": tgt.color, "code": tgt.code}
    else:
        p1, p2 = tgt_info.parents

        a1 = ancestors(p1, flowerpedia, mem)
        mem[p1] = a1

        a2 = ancestors(p2, flowerpedia, mem)
        mem[p2] = a2

        comb_prob = dict(p1 + p2)[tgt]
        return {
            "code": tgt.code,
            "A": a1,
            "B": a2 if a1 != a2 else None,
            "prob": f"{comb_prob:.03}",
            "total_prob": f"{flowerpedia[tgt].total_prob:.03}",
            "color": tgt.color,
            "test": tgt_info.test if tgt_info.test.test_flower else None,
        }


def stepify(tgt_flower: Flower, ancestor_tree: Dict[str, Any]) -> Tuple[List[Any], Dict[Flower, str]]:
    """
    Gives an ordered list of steps to obtain root flower of the ancestor tree.
    each step is: 

        If this is the first time we make this flower:
            - Obtained Flower
            - Flowers needed (their names) -> 0, 1 (self hybrid) or 2
            - Tests needed (HybridTestInfo)
        
        Otherwise no steps needed
        
    """
    res: List[Any] = []
    names: Dict[Flower, str] = {}

    def helper_postfix(tree: dict, names_ref: Dict[Flower, str], res_ref: List[Any]):
        curr_gene = read_code(tree["code"])
        print(curr_gene)
        curr_f = Flower(tgt_flower.type, curr_gene)
        
        # Downstream
        children = [tree[v] for v in ["A", "B"] if v in tree and tree[v]]

        for child in children:
            helper_postfix(child, names_ref, res_ref)

        # Upstream
        
        # This is a new flower
        if tree["code"] not in names_ref:
            n_color = sum(1 for v in names_ref.values() if v.startswith(tree["color"]))
            names_ref[tree["code"]] = f"{tree['color']}_{n_color}"
            
            if "test" in tree and tree["test"] and tree["test"].test_flower not in names_ref:
                n_color = sum(1 for v in names_ref.values() if v.startswith(tree["test"].test_flower.color))
                names_ref[tree["test"].test_flower.code] = f"{tree['test'].test_flower.color}_{n_color}"
            
            
            res_ref.append((curr_f,
                            tuple(Flower(tgt_flower.type, read_code(c["code"])) for c in children),
                            tree["prob"] if "prob" in tree else 1.,
                            tree["test"] if "test" in tree else None))
        
    helper_postfix(ancestor_tree, names, res)
    return res, names


def get_flowerpedia_db():
    if path.isfile("db/flowerpedia_db.pkl"):
        db = pickle.load(open("db/flowerpedia_db.pkl", "rb"))
        return db

    db = {}
    for t in Flower.flowertypes:
        print(t)
        for s in [True, False]:
            for i in [True, False]:
                if not s and not i:
                    continue
                
                base_flowers = []
                if s:
                    base_flowers += uget(flower_info, _type=t, _seed=s, _island=False)
                if i:
                    base_flowers += uget(flower_info, _type=t, _seed=False, _island=i)
                    
                
                db[(t, s, i)] = explore(base_flowers)
    return db


def cli():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-t",
        "--type",
        type=(lambda x: getattr(Flower, x.upper())),
        choices=Flower.flowertypes,
        help="Type of the searched flower",
    )
    tgt_group = parser.add_mutually_exclusive_group()
    
    tgt_group.add_argument(
        "-c",
        "--color",
        type=(lambda x: getattr(Flower, x.upper())),
        choices=Flower.flowercolors,
        help="Color of the searched flower",
    )

    tgt_group.add_argument("--code", action="extend", type=int, nargs="+", help="Genes of the searched flower")

    parser.add_argument(
        "-s",
        "--seed",
        action="store_true",
        help="Use seed flowers to obtain target flower",
    )
    parser.add_argument(
        "-i",
        "--island",
        action="store_true",
        help="Use island flowers to obtain target flower",
    )

    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Include tests during the search",
        default=False,
    )

    args = parser.parse_args()

    print(args)

    if args.code:
        tgt_flowers = [Flower(args.type, args.code)]
    else:
        tgt_flowers = uget(
            flower_info, _type=args.type, _color=args.color, _seed=None, _island=None
        )

    base_flowers = []
    if args.seed:
        base_flowers += uget(
            flower_info, _type=args.type, _color=None, _seed=args.seed, _island=None
        )
    if args.island:
        base_flowers += uget(
            flower_info, _type=args.type, _color=None, _seed=None, _island=args.island
        )

    # print(f"{args=}")
    # print(f"{tgt_flowers=}")
    return base_flowers, tgt_flowers


def main():
    # import cProfile

    # cProfile.run(
    #     "explore(uget(flower_info, _type=Flower.ROSES, _color=None, _seed=True, _island=False))"
    # )

    # --- 

    # flowerpedia = explore(universal_get(flower_info, _type=Flower.ROSES, _color=None, _seed=True, _island=False))
    # pprint(ancestors(universal_get(flower_info, _type=Flower.ROSES, _color=Flower.BLUE, _seed=None, _island=None)[0], flowerpedia))

    # ---

    base, tgt = cli()
    flowerpedia = explore(base)

    print(len(flowerpedia))
    
    for t in tgt:
        print(t, t in flowerpedia)
    
    max_tgt = max(tgt, key=lambda x: flowerpedia[x].total_prob if x in flowerpedia else -math.inf)
    pprint(a := ancestors(max_tgt, flowerpedia))
    pprint(stepify(max_tgt, a))

    # ---
    
    # db = get_flowerpedia_db()
    
    # with open("flowerpedia_db.pkl", "wb") as f:
    #     pickle.dump(db, f)
        
    # print(db)

if __name__ == "__main__":
    
    main()
