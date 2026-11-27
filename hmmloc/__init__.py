"""hmmloc — HMM-centred monocular sequence-based visual localization (research package).

Modules
-------
hmm       : mass-conserving forward filter over a map graph with off-map (null) state, latent velocity,
            evidence tempering, fixed-lag smoothing and Viterbi.
emission  : observation models (softmax-temperature, calibrated logistic LLR, per-frame normalisation).
data      : episode loaders for the cached feature bank (Nordland, RobotCar Seasons v2, Extended CMU Seasons).
baselines : single-image retrieval and causal SeqSLAM.
metrics   : R@1, event NLL, confidence/ECE, confident-wrong, AUROC, block bootstrap CIs.
"""
__version__ = "0.1.0"
