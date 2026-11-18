"""Ridge regression on the same inputs as the network (closed form, unpenalised intercept)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Ridge:
    intercept: float
    coefficients: np.ndarray
    validation_loss: float


def fit_ridge(x: np.ndarray, y: np.ndarray, alpha: float) -> tuple[float, np.ndarray]:
    if len(y) < 3:
        raise ValueError('Insufficient training data')
    x_mean, y_mean = x.mean(axis=0), y.mean()
    centred = x - x_mean
    gram = centred.T @ centred + alpha * np.eye(x.shape[1])
    beta = np.linalg.solve(gram, centred.T @ (y - y_mean))
    return float(y_mean - x_mean @ beta), beta


def predict_ridge(model: Ridge, x: np.ndarray) -> np.ndarray:
    return model.intercept + x @ model.coefficients


def tune_ridge(x: np.ndarray, y: np.ndarray, x_val: np.ndarray, y_val: np.ndarray,
               alphas: list[float]) -> tuple[Ridge, float]:
    """Pick the alpha with the lowest validation error; ties go to the smaller alpha."""
    best: tuple[float, float, Ridge] | None = None
    for alpha in sorted(alphas):
        intercept, beta = fit_ridge(x, y, alpha)
        loss = float(np.mean((intercept + x_val @ beta - y_val) ** 2))
        if best is None or loss < best[0]:
            best = (loss, alpha, Ridge(intercept, beta, loss))
    if best is None:
        raise ValueError('Empty alpha grid')
    return best[2], best[1]
