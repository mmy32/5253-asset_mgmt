"""Feedforward network in numpy: ReLU hidden layers, dropout, L1/L2 penalties, Adam.

Follows the paper's Appendix C structure. The training loop details (batch size,
epochs, patience) come from the settings passed in, not from the paper.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any

import numpy as np

Params = list[np.ndarray]  # W0, b0, W1, b1, ..., output W, output b


@dataclass(frozen=True)
class NetConfig:
    hidden: tuple[int, ...]
    keep_prob: float
    learning_rate: float
    l1: float
    l2: float


@dataclass(frozen=True)
class TrainingSettings:
    batch_size: int
    max_epochs: int
    patience: int


@dataclass(frozen=True)
class Model:
    params: Params
    y_mean: float
    y_std: float
    validation_loss: float


def build_grid(spec: dict[str, Any]) -> list[NetConfig]:
    grid = []
    for layers, units, keep, rate, l1, l2 in product(
            spec['hidden_layers'], spec['first_layer_units'], spec['keep_prob'],
            spec['learning_rate'], spec['l1'], spec['l2']):
        hidden = tuple(units // 2 ** i for i in range(layers))
        grid.append(NetConfig(hidden, keep, rate, l1, l2))
    return grid


def init_params(n_inputs: int, hidden: tuple[int, ...], rng: np.random.Generator) -> Params:
    sizes = [n_inputs, *hidden, 1]
    params: Params = []
    for fan_in, fan_out in zip(sizes[:-1], sizes[1:]):
        params += [rng.normal(0, np.sqrt(2 / fan_in), (fan_in, fan_out)), np.zeros(fan_out)]
    return params


def forward(params: Params, x: np.ndarray, keep_prob: float = 1.0,
            rng: np.random.Generator | None = None):
    """Return predictions plus what the backward pass needs."""
    layers = len(params) // 2
    inputs, relu_out, masks = [x], [], []
    a = x
    for i in range(layers - 1):
        a = np.maximum(a @ params[2 * i] + params[2 * i + 1], 0)
        relu_out.append(a)
        mask = None
        if rng is not None and keep_prob < 1:
            mask = (rng.random(a.shape) < keep_prob) / keep_prob
            a = a * mask
        masks.append(mask)
        inputs.append(a)
    return (a @ params[-2] + params[-1])[:, 0], inputs, relu_out, masks


def penalty(params: Params, l1: float, l2: float) -> float:
    weights = params[0::2]
    return float(sum(l1 * np.abs(w).sum() + l2 * (w ** 2).sum() for w in weights))


def gradients(params: Params, x: np.ndarray, y: np.ndarray, config: NetConfig,
              rng: np.random.Generator | None) -> Params:
    pred, inputs, relu_out, masks = forward(params, x, config.keep_prob, rng)
    delta = (2 * (pred - y) / len(y))[:, None]
    grads: Params = [np.empty(0)] * len(params)
    for i in reversed(range(len(params) // 2)):
        w = params[2 * i]
        grads[2 * i] = inputs[i].T @ delta + 2 * config.l2 * w + config.l1 * np.sign(w)
        grads[2 * i + 1] = delta.sum(axis=0)
        if i > 0:
            delta = delta @ w.T
            if masks[i - 1] is not None:
                delta = delta * masks[i - 1]
            delta = delta * (relu_out[i - 1] > 0)
    return grads


def fit(x: np.ndarray, y: np.ndarray, x_val: np.ndarray, y_val: np.ndarray,
        config: NetConfig, settings: TrainingSettings, seed: int) -> Model:
    """Train with Adam; keep the weights with the lowest validation loss."""
    if len(y) == 0 or len(y_val) == 0:
        raise ValueError('Training and validation sets must be nonempty')
    y_mean, y_std = float(y.mean()), float(y.std())
    if y_std == 0:
        raise ValueError('Constant training target')
    ys, yv = (y - y_mean) / y_std, (y_val - y_mean) / y_std
    rng = np.random.default_rng(seed)
    params = init_params(x.shape[1], config.hidden, rng)
    m = [np.zeros_like(p) for p in params]
    v = [np.zeros_like(p) for p in params]
    best, best_loss, stale, step = [p.copy() for p in params], np.inf, 0, 0
    for _ in range(settings.max_epochs):
        order = rng.permutation(len(ys))
        for start in range(0, len(order), settings.batch_size):
            batch = order[start:start + settings.batch_size]
            step += 1
            for i, g in enumerate(gradients(params, x[batch], ys[batch], config, rng)):
                m[i] = 0.9 * m[i] + 0.1 * g
                v[i] = 0.999 * v[i] + 0.001 * g ** 2
                update = (m[i] / (1 - 0.9 ** step)) / (np.sqrt(v[i] / (1 - 0.999 ** step)) + 1e-8)
                params[i] = params[i] - config.learning_rate * update
        loss = float(np.mean((forward(params, x_val)[0] - yv) ** 2))
        if not np.isfinite(loss):
            break
        if loss < best_loss:
            best, best_loss, stale = [p.copy() for p in params], loss, 0
        else:
            stale += 1
            if stale >= settings.patience:
                break
    if not np.isfinite(best_loss):
        raise ValueError('Training diverged before any usable epoch')
    return Model(best, y_mean, y_std, best_loss)


def predict(model: Model, x: np.ndarray) -> np.ndarray:
    return forward(model.params, x)[0] * model.y_std + model.y_mean


def predict_ensemble(models: list[Model], x: np.ndarray) -> np.ndarray:
    return np.mean([predict(m, x) for m in models], axis=0)
