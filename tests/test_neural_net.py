import numpy as np
import pytest

from src.models.linear_model import fit_ridge, predict_ridge, tune_ridge
from src.models.neural_net import (
    NetConfig,
    TrainingSettings,
    build_grid,
    fit,
    forward,
    gradients,
    init_params,
    penalty,
    predict,
    predict_ensemble,
)
from src.models.setup_a import tune_network

SETTINGS = TrainingSettings(batch_size=128, max_epochs=60, patience=6)


def test_grid_has_144_settings_with_halving_units():
    spec = {'hidden_layers': [1, 2, 3], 'first_layer_units': [64, 32], 'keep_prob': [0.9, 0.95],
            'learning_rate': [0.001, 0.1], 'l1': [0.0, 1e-5], 'l2': [0.0, 0.01, 0.001]}
    grid = build_grid(spec)
    assert len(grid) == 144 == len(set(grid))
    hidden = {c.hidden for c in grid}
    assert (64, 32, 16) in hidden and (32, 16, 8) in hidden and (64,) in hidden


def test_backpropagation_matches_numerical_gradient():
    rng = np.random.default_rng(0)
    x, y = rng.normal(size=(12, 4)), rng.normal(size=12)
    config = NetConfig((5, 3), keep_prob=1.0, learning_rate=0.01, l1=0.01, l2=0.05)
    params = init_params(4, config.hidden, rng)

    def loss(p):
        return float(np.mean((forward(p, x)[0] - y) ** 2)) + penalty(p, config.l1, config.l2)

    analytic = gradients(params, x, y, config, rng=None)
    for index, array in enumerate(params):
        for position in np.ndindex(array.shape):
            up = [p.copy() for p in params]
            down = [p.copy() for p in params]
            up[index][position] += 1e-6
            down[index][position] -= 1e-6
            numeric = (loss(up) - loss(down)) / 2e-6
            assert analytic[index][position] == pytest.approx(numeric, abs=1e-5)


def interaction_data(n, seed):
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1, 1, size=(n, 3))
    return x, x[:, 0] * x[:, 1] + 0.05 * rng.normal(size=n)


def test_network_learns_an_interaction_that_ridge_cannot():
    x, y = interaction_data(4000, 1)
    xv, yv = interaction_data(1000, 2)
    xt, yt = interaction_data(1000, 3)
    model = fit(x, y, xv, yv, NetConfig((32,), 1.0, 0.01, 0.0, 0.0), SETTINGS, seed=1)
    ridge, _ = tune_ridge(x, y, xv, yv, [0.1, 1.0])
    network_error = np.mean((predict(model, xt) - yt) ** 2)
    ridge_error = np.mean((predict_ridge(ridge, xt) - yt) ** 2)
    assert network_error < 0.5 * ridge_error


def test_best_validation_weights_are_returned_and_fits_are_reproducible():
    x, y = interaction_data(1500, 4)
    xv, yv = interaction_data(500, 5)
    config = NetConfig((16,), 0.95, 0.01, 0.0, 0.0)
    a = fit(x, y, xv, yv, config, SETTINGS, seed=7)
    b = fit(x, y, xv, yv, config, SETTINGS, seed=7)
    recomputed = np.mean((forward(a.params, xv)[0] - (yv - a.y_mean) / a.y_std) ** 2)
    assert a.validation_loss == pytest.approx(recomputed)
    assert np.allclose(predict(a, xv), predict(b, xv))


def test_ensemble_is_the_mean_of_its_members():
    x, y = interaction_data(800, 6)
    xv, yv = interaction_data(300, 7)
    config = NetConfig((8,), 1.0, 0.01, 0.0, 0.0)
    models = [fit(x, y, xv, yv, config, SETTINGS, seed=s) for s in (1, 2)]
    expected = (predict(models[0], xv) + predict(models[1], xv)) / 2
    assert np.allclose(predict_ensemble(models, xv), expected)


def test_constant_target_fails_fast():
    x = np.random.default_rng(0).normal(size=(50, 2))
    with pytest.raises(ValueError):
        fit(x, np.ones(50), x, np.ones(50), NetConfig((4,), 1.0, 0.01, 0.0, 0.0), SETTINGS, seed=0)
    with pytest.raises(ValueError):
        tune_network(x, np.ones(50), x, np.ones(50), [NetConfig((4,), 1.0, 0.01, 0.0, 0.0)], SETTINGS, 0)


def test_ridge_recovers_a_linear_signal_and_breaks_ties_toward_small_alpha():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(500, 2))
    y = 3 + 2 * x[:, 0] - x[:, 1]
    intercept, beta = fit_ridge(x, y, 1e-9)
    assert intercept == pytest.approx(3, abs=1e-6) and beta == pytest.approx([2, -1], abs=1e-6)
    _, alpha = tune_ridge(x, y, x, y, [10.0, 0.01, 1.0])
    assert alpha == 0.01
