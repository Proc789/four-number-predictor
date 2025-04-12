from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
sources = []
hot_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0
current_stage = 1
training_enabled = False
rhythm_history = []
rhythm_state = "未知"
last_champion_zone = ""
was_observed = False
observation_message = ""

TEMPLATE = """...（保持不變，略）"""

@app.route('/observe')
def observe():
    global was_observed, observation_message
    was_observed = True
    observation_message = "上期為觀察期"
    try:
        first = int(request.args.get('first', '10'))
        second = int(request.args.get('second', '10'))
        third = int(request.args.get('third', '10'))
        current = [first, second, third]
        history.append(current)

        if len(history) >= 5:
            stage_to_use = current_stage if 1 <= current_stage <= 4 else 1
            prediction = make_prediction(stage_to_use)
            predictions.append(prediction)
            champion = current[0]
            hot_pool = sources[-1]['hot'] + sources[-1]['dynamic'] if sources else []
            rhythm_history.append(1 if champion in hot_pool else 0)
            if len(rhythm_history) > 5:
                rhythm_history.pop(0)
            recent = rhythm_history[-3:]
            total = sum(recent)
            if recent == [0, 0, 1]:
                rhythm_state = "預熱期"
            elif total >= 2:
                rhythm_state = "穩定期"
            elif total == 0:
                rhythm_state = "失準期"
            else:
                rhythm_state = "搖擺期"
    except:
        pass
    return redirect('/')

@app.route('/', methods=['GET', 'POST'])
def index():
    global hot_hits, dynamic_hits, extra_hits, all_hits, total_tests
    global current_stage, training_enabled, was_observed, observation_message
    global rhythm_history, rhythm_state, last_champion_zone

    prediction = None
    last_prediction = predictions[-1] if predictions else None
    observation_message = ""

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if len(history) >= 5 or training_enabled:
                stage_to_use = current_stage if 1 <= current_stage <= 4 else 1
                prediction = make_prediction(stage_to_use)
                predictions.append(prediction)

                if len(predictions) >= 2:
                    champion = current[0]
                    if champion in predictions[-2]:
                        all_hits += 1
                        current_stage = 1
                    else:
                        current_stage += 1

                    if training_enabled:
                        total_tests += 1
                        if champion in sources[-1]['hot']:
                            hot_hits += 1
                            last_champion_zone = "熱號區"
                        elif champion in sources[-1]['dynamic']:
                            dynamic_hits += 1
                            last_champion_zone = "動熱區"
                        elif champion in sources[-1]['extra']:
                            extra_hits += 1
                            last_champion_zone = "補碼區"
                        else:
                            last_champion_zone = "未命中"

                    hot_pool = sources[-1]['hot'] + sources[-1]['dynamic']
                    rhythm_history.append(1 if champion in hot_pool else 0)
                    if len(rhythm_history) > 5:
                        rhythm_history.pop(0)
                    recent = rhythm_history[-3:]
                    total = sum(recent)
                    if recent == [0, 0, 1]:
                        rhythm_state = "預熱期"
                    elif total >= 2:
                        rhythm_state = "穩定期"
                    elif total == 0:
                        rhythm_state = "失準期"
                    else:
                        rhythm_state = "搖擺期"
        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=current_stage,
        history=history,
        training=training_enabled,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests,
        rhythm_state=rhythm_state,
        last_champion_zone=last_champion_zone,
        observation_message=observation_message)

def make_prediction(stage):
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    freq = Counter(flat)

    hot = [n for n, _ in freq.most_common(3)][:2]
    dynamic_pool = [n for n in freq if n not in hot]
    dynamic_sorted = sorted(dynamic_pool, key=lambda x: (-freq[x], -flat[::-1].index(x)))
    dynamic = dynamic_sorted[:2]

    used = set(hot + dynamic)
    pool = [n for n in range(1, 11) if n not in used]
    random.shuffle(pool)
    extra_count = 2 if stage == 4 else 3
    extra = pool[:extra_count]

    sources.append({'hot': hot, 'dynamic': dynamic, 'extra': extra})
    return sorted(hot + dynamic + extra)
