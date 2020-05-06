import json
import math

from flask import render_template, request

from app import app
from flower import main

app.flower_db = main.get_flowerpedia_db()

@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
def index():
    flower_types = [
        {"name": str(f_type).strip("_").capitalize()} for f_type in main.Flower.flowertypes
    ]
    
    flower_colors = [
        {"name": str(f_color)} for f_color in main.Flower.flowercolors
    ]
    
    return render_template("form.html", title="Home", flower_types=flower_types, flower_colors=flower_colors)

@app.route("/results", methods=["POST"])
def result_page():
    form = request.form
    
    tgt_type = getattr(main.Flower, form["tgt_type"])
    tgt_color = getattr(main.Flower, form["tgt_color"])
    seed = True if "seed" in form else False
    island = True if "island" in form else False
    
    tgt = main.uget(main.flower_info, _type=tgt_type, _color=tgt_color)
    if len(tgt) == 0:
        return "This target does not exist"
    
    flowerpedia = app.flower_db[(tgt_type, seed, island)]
    best_flower = max(tgt, key=lambda x: flowerpedia[x].total_prob if x in flowerpedia else -math.inf)
    
    path = main.ancestors(best_flower, flowerpedia)
    
    
    res, name = main.stepify(best_flower, path)
    # base flowers in result / steps
    base_flowers_needed = [f for f, a, p, t in res if len(a) == 0]
    # base flowers appearing in tests
    base_flowers_needed.extend(t.test_flower for *_, t in res if t and t.test_flower not in base_flowers_needed and t.test_flower not in (f for f, a, *_ in res if len(a) > 0))
    
    tn = 0
    hybrid_flowers = [(f, (a if len(a) == 2 else (a[0], a[0])), f"{float(p) * 100:0.2f}", t, (tn := tn+1 if t else 0)) for f, a, p, t in res if len(a) > 0]
    
    
    tests = [t for *_, t in res if t]
    # return f"{tgt_type=} {tgt_color=} {seed=} {island=} {json.dumps(path)}"
    return render_template("results.html", base_flowers=base_flowers_needed, hybrid_flowers=hybrid_flowers, names=name, tests=tests,
                           len=len, enumerate=enumerate)





