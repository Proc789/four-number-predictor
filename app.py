# 4碼預測器改版：第一關 7碼、第二關起 5碼，七關失敗清空資料，命中回歸第一關（UI 不變）
from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
hot_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0
current_stage = 1
training_mode = False

TEMPLATE = """<html>...（保持不變，略）..."""  # 保留原 TEMPLATE 區塊

@app.route('/', methods=['GET', 'POST'])
def index():
    global hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage, training_mode, history, predictions
    prediction = None
    last_prediction = predictions[-1] if predictions else None

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            # 命中判定邏輯（不論是否訓練模式）
            if len(predictions) >= 1:
                champion = current[0]
                if champion in predictions[-1]:
                    if training_mode:
                        all_hits += 1
                    current_stage = 1
                else:
                    current_stage += 1
                    if current_stage > 6:
                        history.clear()
                        predictions.clear()
                        current_stage = 1

                if training_mode:
                    total_tests += 1
                    if champion in predictions[-1][:2]:
                        hot_hits += 1
                    elif champion == predictions[-1][2]:
                        dynamic_hits += 1
                    elif champion in predictions[-1][3:]:
                        extra_hits += 1

            # 預測條件：統計模式啟用或輸入滿5筆
            if training_mode or len(history) >= 5:
                prediction = generate_prediction(current_stage)
                predictions.append(prediction)

        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=current_stage,
        training=training_mode,
        history=history,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests)

@app.route('/toggle')
def toggle():
    global training_mode, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage, predictions
    training_mode = not training_mode
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    current_stage = 1
    predictions = []
    return redirect('/')

@app.route('/reset')
def reset():
    global history, predictions, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage
    history.clear()
    predictions.clear()
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    current_stage = 1
    return redirect('/')

def generate_prediction(stage):
    recent = history[-3:]
    flat = [n for group in recent for n in group]
    freq = Counter(flat)
    hot = [n for n, _ in freq.most_common(3)][:2]

    flat_dynamic = [n for n in flat if n not in hot]
    freq_dyn = Counter(flat_dynamic)
    dynamic_pool = sorted(freq_dyn.items(), key=lambda x: (-x[1], -flat_dynamic[::-1].index(x[0])))
    dynamic = [n for n, _ in dynamic_pool[:2 if stage == 1 else 2]][:2 if stage == 1 else 2][:1 if stage > 1 else 2]

    used = set(hot + dynamic)
    pool = [n for n in range(1, 11) if n not in used]
    random.shuffle(pool)
    extra_count = 3 if stage == 1 else 1
    extra = pool[:extra_count]

    return sorted(hot + dynamic + extra)

if __name__ == '__main__':
    app.run(debug=True)
