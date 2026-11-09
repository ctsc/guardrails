import math

from scorer import SENTINEL, Scorer, load_config, parse_letter_probs


def test_parse_new_format_logprobs():
    resp = {"completion_probabilities": [{"token": "B", "logprob": math.log(0.7), "top_logprobs": [
        {"token": "B", "logprob": math.log(0.7)}, {"token": "A", "logprob": math.log(0.2)}, {"token": "C", "logprob": math.log(0.1)}]}]}
    p = parse_letter_probs(resp)
    assert abs(sum(p.values()) - 1) < 1e-6 and max(p, key=p.get) == "B" and abs(p["B"] - 0.7) < 1e-6


def test_parse_old_format_probs():
    resp = {"completion_probabilities": [{"content": "A", "probs": [{"tok_str": "A", "prob": 0.9}, {"tok_str": "G", "prob": 0.1}]}]}
    p = parse_letter_probs(resp)
    assert max(p, key=p.get) == "A" and p["G"] > 0


def test_prompt_contains_text_once():
    s = Scorer(load_config())
    prompt = s.build_prompt("hello world")
    assert prompt.count("hello world") == 1 and SENTINEL not in prompt and "<|im_start|>assistant" in prompt
