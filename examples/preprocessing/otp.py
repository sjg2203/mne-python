"""
.. _ex-otp:

===========================================================
Plot sensor denoising using oversampled temporal projection
===========================================================

This demonstrates denoising using the OTP algorithm :footcite:`LarsonTaulu2018` on data
with with sensor artifacts (flux jumps) and random noise.
"""
# Author: Eric Larson <larson.eric.d@gmail.com>
#
# License: BSD-3-Clause
# Copyright the MNE-Python contributors.

# %%
import numpy as np

import mne
from mne import find_events, fit_dipole
from mne.datasets.brainstorm import bst_phantom_elekta
from mne.io import read_raw_fif

print(__doc__)

# %%
# Plot the phantom data, lowpassed to get rid of high-frequency artifacts.
# We also crop to a single 10-second segment for speed.
# Notice that there are two large flux jumps on channel 1522 that could
# spread to other channels when performing subsequent spatial operations
# (e.g., Maxwell filtering, SSP, or ICA).

dipole_number = 1
data_path = bst_phantom_elekta.data_path()
raw = read_raw_fif(data_path / "kojak_all_200nAm_pp_no_chpi_no_ms_raw.fif")
raw.crop(40.0, 50.0).load_data()
order = list(range(160, 170))
raw.copy().filter(0.0, 40.0).plot(order=order, n_channels=10)

# %%
# Now we can clean the data with OTP, lowpass, and plot. The flux jumps have
# been suppressed alongside the random sensor noise.

raw_clean = mne.preprocessing.oversampled_temporal_projection(raw)
raw_clean.filter(0.0, 40.0)
raw_clean.plot(order=order, n_channels=10)


# %%
# We can also look at the effect on single-trial phantom localization.
# See the :ref:`tut-brainstorm-elekta-phantom`
# for more information. Here we use a version that does single-trial
# localization across the 17 trials are in our 10-second window:


def compute_bias(raw):
    events = find_events(raw, "STI201", verbose=False)
    events = events[1:]  # first one has an artifact
    tmin, tmax = -0.2, 0.1
    epochs = mne.Epochs(
        raw,
        events,
        dipole_number,
        tmin,
        tmax,
        baseline=(None, -0.01),
        preload=True,
        verbose=False,
    )
    sphere = mne.make_sphere_model(r0=(0.0, 0.0, 0.0), head_radius=None, verbose=False)
    cov = mne.compute_covariance(epochs, tmax=0, method="oas", rank=None, verbose=False)
    idx = epochs.time_as_index(0.036)[0]
    data = epochs.get_data(copy=False)[:, :, idx].T
    evoked = mne.EvokedArray(data, epochs.info, tmin=0.0)
    dip = fit_dipole(evoked, cov, sphere, verbose=False)[0]
    actual_pos = mne.dipole.get_phantom_dipoles()[0][dipole_number - 1]
    misses = 1000 * np.linalg.norm(dip.pos - actual_pos, axis=-1)
    return misses


bias = compute_bias(raw)
print(f"Raw bias: {np.mean(bias):0.1f}mm (worst: {np.max(bias):0.1f}mm)")
bias_clean = compute_bias(raw_clean)
print(f"OTP bias: {np.mean(bias_clean):0.1f}mm (worst: {np.max(bias_clean):0.1f}m)")

# %%
# References
# ----------
# .. footbibliography::
