"""Local Hugging Face model (default Qwen/Qwen2.5-1.5B-Instruct) run on CPU with transformers.

Only used by the pipeline (make notes). The app never calls a model: it reads notes.parquet offline.
"""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _load(model_id: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(4)
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32)
    model.eval()
    return tok, model


def generate(model_id: str, system: str, user: str, max_new_tokens: int = 320, seed: int = 42,
             sample: bool = False) -> str:
    import torch

    tok, model = _load(model_id)
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = tok([text], return_tensors="pt")
    torch.manual_seed(seed)
    kw = dict(max_new_tokens=max_new_tokens, repetition_penalty=1.05)
    if sample:
        kw.update(do_sample=True, temperature=0.7, top_p=0.9)
    else:
        kw.update(do_sample=False)
    with torch.no_grad():
        out = model.generate(**inputs, **kw)
    return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
