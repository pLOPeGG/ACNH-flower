import itertools as it
import json

from operator import mul
from collections import deque, namedtuple, Counter
from dataclasses import dataclass
from functools import reduce
from pprint import pprint
from os import path
from typing import *

# This code uses informations provided by this source: https://docs.google.com/document/d/1ARIQCUc5YVEd01D7jtJT9EEJF45m07NXhAm4fOpNvCs/mobilebasic
# All flowers rules are explained deeply an thoroughly inside.

FlowerType = NewType("FlowerType", str)
FlowerColor = NewType("FlowerColor", str)
ColorSeedIsland = namedtuple("ColorSeedIsland", "color seed island")

# Mixing rules for any genesself.
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

    BLACK = FlowerColor("Black")
    BLUE = FlowerColor("Blue")
    GREEN = FlowerColor("Green")
    PINK = FlowerColor("Pink")
    PURPLE = FlowerColor("Purple")
    ORANGE = FlowerColor("Orange")
    RED = FlowerColor("Red")
    YELLOW = FlowerColor("Yellow")
    WHITE = FlowerColor("White")

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
        self.type = flower_type
        self.genes = tuple(genes)

    @property
    def color(self) -> FlowerColor:
        return FlowerColor(flower_color[self].color)

    @property
    def is_seed(self) -> bool:
        return bool(flower_color[self].seed)

    @property
    def is_island(self) -> bool:
        return bool(flower_color[self].island)

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
        """
        if self.type != other.type:
            return []
        res_genes = [mix_d[g] for g in zip(self.genes, other.genes)]

        res = []
        for p in it.product(*res_genes):
            genes, probs = zip(*p)
            prob = reduce(mul, probs)
            res.append((Flower(self.type, genes), prob))

        return res

    def __eq__(self, other) -> bool:
        if isinstance(other, Flower):
            return self.type == other.type and self.genes == other.genes
        elif isinstance(other, Sequence):
            return self.genes == other
        return False

    def __hash__(self):
        return hash((self.type, self.genes))

    def __str__(self) -> str:
        return f"({self.type} {self.code} {self.color} {self.genes} {self.is_seed})"

    def __repr__(self):
        return str(self)
        return f"Flower({self.type}, {self.genes})"


FlowerDB = NewType("FlowerDB", Dict[Flower, ColorSeedIsland])


def load_colors(file_type_couples: List[Tuple[str, FlowerType]]) -> FlowerDB:
    """
    Reads a csv file containing color information about flowers.
    """
    d = FlowerDB({})

    def helper(s, l):
        res = sum(1 for c in s if c.isupper())
        if l == "w":
            return 2 - res
        return res

    for file, flower_type in file_type_couples:
        with open(path.join("data", file), "r") as fp:
            for line in fp.readlines():
                _, gene, *_, color_info = line.strip().split("\t")

                gene_code = []
                for i in range(0, len(gene), 2):
                    gene_code.append(helper(gene[i : i + 2], gene[i].lower()))

                c = FlowerColor(color_info.split()[0])
                is_seed = color_info.split()[1] == "(seed)" if len(color_info.split()) > 1 else False
                is_island = color_info.split()[1] == "(island)" if len(color_info.split()) > 1 else False
                
                d[Flower(flower_type, tuple(gene_code))] = ColorSeedIsland(c, is_seed, is_island)
    return d


flower_color = load_colors(
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
    test_flower: Optional[Flower]
    test_prob: float
    test_color: Optional[FlowerColor]

@dataclass
class AncestorInfo:
    parents: Optional[Tuple[Flower, Flower]]
    ancestors: Set[Flower]
    test: Optional[HybridTestInfo]
    micro_prob: float
    no_test_global_prob: float
    
    
    @property
    def total_prob(self) -> float:
        if self.test:
            return self.test.test_prob * self.no_test_global_prob
        else:
            return self.no_test_global_prob
    

FlowerPedia = NewType(
    "FlowerPedia",
    Dict[Flower, AncestorInfo],
)


def universal_get(
    flower_color: FlowerPedia,
    _type: Optional[FlowerType] = None,
    _color: Optional[FlowerColor] = None,
    _seed: Optional[bool] = None,
    _island: Optional[bool] = None
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
        test_cond(_island, "is_island")
    ]
    
    for flower in flower_color:
        if all(test(flower) for test in tests_AND):
            res.append(flower)
    return res


def prob_test_hybrid(f1: Flower, f2: Flower, f_h: Flower, known_flowers: Set[Flower]) -> HybridTestInfo:
    assert f_h in (f[0] for f in f1 + f2), f"Flower {f_h} is not an hybrid of {f1} + {f2}."

    # return None, 1., None

    color_counter = Counter(f.color for f, _ in f1 + f2)
    if color_counter[f_h.color] == 1:
        return HybridTestInfo(test_flower=None, test_prob=1., test_color=None)

    # Now we need to test the flower because we are not sure. 
    f_h_p = next(p for f, p in f1 + f2 if f == f_h)
    concurrent_flowers = [(f, p) for f, p in f1 + f2 if f.color == f_h.color and f != f_h]
    
    best_test_f = None
    best_p_color = 0.
    best_color = None
    
    # TODO (FEAT001): flower should be able to test with itself.
    for other_f in known_flowers:
        h_colors = {f.color for f, p in f_h + other_f}
        
        concurrent_colors = {f.color for ff, pp in concurrent_flowers for f, p in ff + other_f}
        
        possible_test_colors = h_colors - concurrent_colors

        
        
        # We cannot be sure the popped flower is not a duplicate of any of the two (and we won't test it ;) ).
        if other_f.color == f_h.color and f_h.color in possible_test_colors:
            possible_test_colors.remove(f_h.color)

        # print(f"{possible_test_colors=}")

        if len(possible_test_colors) > 0:
            # There is some color that we can use.
            for test_color in possible_test_colors:
                # print(f"{test_color=}")
                p_color = sum(p for f, p in f_h + other_f if f.color == test_color)
                
                if p_color > best_p_color:
                    best_p_color = p_color
                    best_test_f = other_f
                    best_color = test_color

    return HybridTestInfo(test_flower=best_test_f, test_prob=best_p_color, test_color=best_color)
"""
p(f OK) = p(f color OK) * p(f OK | f color OK)

o for obtention
o(f OK & f test)    = o(f color ok) * o(f ok | f color OK) * o(f_test color | f OK & f color OK)
"""

def explore(base_flowers: List[Flower]) -> FlowerPedia:
    """
    Compute best path to obtain each flower using only `base_flowers`
    """
    dp = FlowerPedia({f: AncestorInfo(parents=None,
                                      ancestors=set(),
                                      test=None,
                                      micro_prob=1.,
                                      no_test_global_prob=1.) for f in base_flowers})

    flower_l = base_flowers.copy()

    # Floyd Warshall algorithm with no negative cycles
    # Stop when to modification are made to the FlowerPedia

    modified = True
    i = 0
    while modified:
        print(i, len(dp))
        i += 1
        modified = False
        for f1 in flower_l:
            dp_f1 = dp[f1]
            for f2 in flower_l:
                dp_f2 = dp[f2]

                # Compute unique flowers needed to produce f1 and f2
                pred_common = dp_f1.ancestors & dp_f2.ancestors
                prob_common = (
                    dp_f1.no_test_global_prob
                    * dp_f2.no_test_global_prob
                    / reduce(
                        mul, (dp[fi].micro_prob for fi in pred_common), 1.0
                    )  # All flower in pred_common are counter twice in `prob_f1 * prob_f2`
                    # We must divide by `product(prob(i) for i in pred_common)`
                )

                ff = f1 + f2

                for f, p in ff:
                    if f in (f1, f2):
                        continue
                    if f in dp and prob_common < dp[f].total_prob:
                        continue
                    
                    
                    test_result = prob_test_hybrid(f1, f2, f, dp_f1.ancestors | dp_f2.ancestors | {f1, f2})
                    
                    prob_f = prob_common * p * test_result.test_prob
                    if prob_f > 0:
                        if not f in dp:
                            dp[f] = AncestorInfo(parents=(f1, f2),
                                                 ancestors=dp_f1.ancestors | dp_f2.ancestors | {f1, f2},
                                                 test=test_result if test_result.test_flower is not None else None,
                                                 micro_prob=p,
                                                 no_test_global_prob=prob_common * p)
                            modified = True

                        # We want to maximize overall probability of obtaining flower f.
                        elif dp[f].total_prob < prob_f:
                            dp[f] = AncestorInfo(parents=(f1, f2),
                                                 ancestors=dp_f1.ancestors | dp_f2.ancestors | {f1, f2},
                                                 test=test_result if test_result.test_flower is not None else None,
                                                 micro_prob=p,
                                                 no_test_global_prob=prob_common * p)
                            modified = True

        # All flowers obtained so far will be mixed during next iteration of algortihm.
        flower_l = list(dp)

    return dp


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
            "B": a2,
            "prob": f"{comb_prob:.03}",
            "color": tgt.color,
            "test": tgt_info.test
        }


def main():
    flowerpedia = explore(universal_get(flower_color, _type=Flower.ROSES, _color=None, _seed=True, _island=False))
    # print([(f, flowerpedia[f]) for f in universal_get(flower_color, _type=Flower.ROSES, _color=Flower.BLUE, _seed=None)])
    
    pprint(ancestors(universal_get(flower_color, _type=Flower.ROSES, _color=Flower.BLUE, _seed=None, _island=None)[0], flowerpedia))
    
    r_r = universal_get(flower_color, _type=Flower.ROSES, _color=Flower.RED, _seed=True, _island=False)[0]
    r_p = Flower(Flower.ROSES, (0, 0, 0, 0))
    
    pprint(r_r + r_p)
    # print(universal_get(flower_color, _type=Flower.WINDFLOWERS, _island=True))
    
    # r_w = universal_get(flower_color, _type=Flower.ROSES, _color=Flower.WHITE, _seed=True)[0]
    # r_r = universal_get(flower_color, _type=Flower.ROSES, _color=Flower.RED, _seed=True)[0]
    # r_y = universal_get(flower_color, _type=Flower.ROSES, _color=Flower.YELLOW, _seed=True)[0]
    
    # r_r1 = (r_w + r_r)[0][0]
    # r_r2 = (r_w + r_r)[2][0]
    # print(r_w + r_r)
    # print(r_r1)
    
    # print(prob_test_hybrid(r_w, r_r, r_r2, {r_r, r_w, r_y}))
    
    # print(set(f. color for r in [r_y] for f, p in r_r1 + r))
    # print(set(f. color for r in [r_y] for f, p in r_r2 + r))
    



if __name__ == "__main__":
    main()
