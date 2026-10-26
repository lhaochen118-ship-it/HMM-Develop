# Calibrated Condition-Belief Filtering (CCBF)
## Methodology and Theory

*Paper-ready draft of the Method + Theory sections for the DIVE-HMM / CCBF submission.
Notation is kept consistent with the reference implementation in `DIVE_HMM_CCBF_NB1.ipynb`.*

---

## 1. Problem formulation and notation

We address **sequential visual place recognition (VPR) / topological localization under appearance change**.
A fixed **map** stores one global descriptor per reference image, $\mathcal{R}=\{r_1,\dots,r_M\}$, $r_j\in\mathbb{S}^{D-1}$
(unit sphere; descriptors are $\ell_2$-normalized). A **query traversal** is a *temporally ordered* image stream
$x_{1:T}$ with frozen descriptors $d_t=f(x_t)\in\mathbb{S}^{D-1}$ produced by any off-the-shelf encoder
$f$ (SALAD, DINOv2, BoQ, …). We write the **similarity vector**
$$
s_t\in\mathbb{R}^{M},\qquad s_t[j]=\langle d_t,\,r_j\rangle .
$$

The task at time $t$ is to estimate the **place** $p_t\in\mathcal{P}=\{1,\dots,M\}$ (or declare *off-map*),
together with a **calibrated** confidence, using the prefix $d_{1:t}$ (filtering) or the whole stream
(smoothing).

Two structural facts drive the method:

* **(F1) Appearance is a slowly-varying latent.** The *condition* of the stream — season, weather, time of day,
  illumination — changes on a far slower timescale than the place. Within a short window, successive frames share
  a condition; across a traversal it drifts smoothly.
* **(F2) Retrieval scores are not likelihoods.** $s_t[j]$ is an uncalibrated inner product whose match/non-match
  distributions **shift with the condition** (night scores are compressed and noisier than day scores). Feeding raw
  $s_t$ into a sequence filter — as every prior HMM/Bayes-filter VPR method does — injects a *condition-dependent
  calibration error* into the observation model.

CCBF turns (F1) into a prior that makes the condition *identifiable online without labels*, and uses the inferred
condition to repair (F2).

---

## 2. A factored generative model

We posit a **factored hidden Markov model** with two coupled latent chains:

$$
\underbrace{c_{t-1}\!\to\! c_t}_{\text{condition (slow)}}\qquad
\underbrace{p_{t-1}\!\to\! p_t}_{\text{place (fast)}}\qquad
(p_t,c_t)\;\to\; d_t .
$$

* **Place** $p_t\in\mathcal{P}\cup\{\varnothing\}$, where $\varnothing$ is an explicit **off-map / null** state.
* **Condition** $c_t\in\mathcal{C}=\{1,\dots,K\}$, a discrete latent appearance state (a *learned* cluster, not
  necessarily a human season label).

**Transitions.**

* *Place (motion model).* Traversals are quasi-1-D and revisit the mapped route in order, so
  $$
  T_p(p_t=j'\mid p_{t-1}=j)\;\propto\;(1-\eta)\,\mathcal{N}_{\mathbb{Z}}\!\big(j'-j;\,v,\sigma_m^2\big)\;+\;\eta/M,
  $$
  a banded kernel centered at an expected velocity $v$ (default $v{=}1$) with width $\sigma_m$ and a uniform leak
  $\eta$ (kidnap robustness). Entry/exit to $\varnothing$ carries small probabilities $(p_{\text{exit}},p_{\text{enter}})$
  with self-persistence $T_p(\varnothing\mid\varnothing){=}\rho_\varnothing$.
* *Condition (sticky prior — the operationalization of F1).*
  $$
  T_c(c_t=k'\mid c_{t-1}=k)=\rho\,\mathbb{1}[k'{=}k]+(1-\rho)\tfrac{1}{K-1}\mathbb{1}[k'{\neq}k],\qquad \rho\to 1^-.
  $$
  High self-persistence is what lets the filter **integrate condition evidence over a whole window** and thereby
  identify the condition from data alone.

**Emission.** $d_t\sim g(\cdot\mid p_t,c_t)$ — the *condition-conditional* observation density defined next.
This single modeling choice — making the emission depend on $c_t$ — is the crux of the paper; everything else is
the machinery needed to exploit it.

---

## 3. Calibrated condition-conditional observation model

### 3.1 Density-ratio form (general, well-defined)

We adopt the standard VPR observation assumption: given the true place $p_t=j$ and condition $c_t=k$, the score at
the matching reference follows a **match density** $h_{1,k}$, while the scores at all other references follow a
shared, condition-robust **non-match density** $h_0$, conditionally independently:
$$
g(d_t\mid p_t=j,c_t=k)\;=\;h_{1,k}\big(s_t[j]\big)\!\!\prod_{j'\neq j}\! h_0\big(s_t[j']\big).
$$
Taking logs and separating the only place-dependent factor,
$$
\boxed{\;\log g(d_t\mid p_t=j,c_t=k)=\underbrace{\log\frac{h_{1,k}(s_t[j])}{h_0(s_t[j])}}_{\textstyle \ell_t(j,k)}\;+\;\underbrace{\textstyle\sum_{j'}\log h_0(s_t[j'])}_{\text{indep. of }(j,k)}\;}
$$
The constant cancels in every posterior, so the filter only needs the **calibrated log-potential**
$$
\ell_t(j,k)\;=\;\log h_{1,k}(s_t[j])-\log h_0(s_t[j]),
$$
a *proper per-place, per-condition log-likelihood-ratio*. The off-map state uses the null potential
$\ell_t(\varnothing,k)=\log\!\int h_{1,k}(s)\,u(s)\,ds / h_0(\cdot)$ — operationally a high-quantile of $s_t$ scored
under $h_0$ (no reference is a true match).

### 3.2 Temperature form (special case, used in NB1)

If $h_{1,k}=\mathcal{N}(\mu_k,\varsigma^2)$ and $h_0=\mathcal{N}(\mu_0,\varsigma^2)$ (equal-variance Gaussians on the
cosine score), the LLR is **affine** in the score:
$$
\ell_t(j,k)=\frac{\mu_k-\mu_0}{\varsigma^2}\,s_t[j]+\text{const}_k\;=\;\frac{s_t[j]}{\tau_k}+a_k,
\qquad \tau_k:=\frac{\varsigma^2}{\mu_k-\mu_0}.
$$
Thus a **per-condition temperature** $\tau_k$ is exactly the Gaussian-LLR instance of the general model: small
$\tau_k$ (easy condition, large match/non-match gap) ⇒ sharp likelihood; large $\tau_k$ (hard condition) ⇒ humble
likelihood. A single global $\tau$ — the baseline — is the *mis-specified* restriction $\tau_k\equiv\tau$.

> *Implementation note (NB1).* The reference notebook uses the temperature potential $\ell_t(j,k)=s_t[j]/\tau_k$ and
> omits the condition-constant $a_k$; since the condition belief $b^c_t$ there is driven by the appearance model
> (§4), $a_k$ only re-scales the mixture weight and is immaterial to the per-condition *sharpness* being tested.
> The full density-ratio potential with $a_k$ (§3.1) is used once match/non-match densities are fit in later
> experiments.

### 3.3 Calibration by a strictly proper scoring rule

The potential parameters $\theta=\{h_{1,k},h_0\}$ (or $\{\tau_k,a_k\}$) are fit **offline on cached descriptors** by
minimizing a strictly proper scoring rule of the place label under the induced single-frame posterior
$q_\theta(j\mid s_t,k)\propto e^{\ell_t(j,k)}$:
$$
\widehat{\theta}=\arg\min_{\theta}\;\mathbb{E}_{(s,k,j^\star)}\big[\,\mathcal{S}\big(q_\theta(\cdot\mid s,k),\,j^\star\big)\big],
\qquad \mathcal{S}=\text{log-loss or Brier}.
$$
Condition labels are available **only at training time** (e.g. the season folder) and are used solely to stratify
this fit; at test time $k$ is latent. Because $\mathcal{S}$ is strictly proper, its population minimizer is the true
conditional (Gneiting & Raftery, 2007) — this is what makes the observation model *calibrated by construction*
(Theorem 2). The parameter count is $\mathcal{O}(K)$ scalars (temperature form) or a handful of density parameters
per condition — no backbone training.

---

## 4. The condition latent and label-free inference

**Condition representation.** Each condition $k$ owns a centroid $\mu^c_k\in\mathbb{R}^{D}$ in descriptor space
(the per-season mean when train labels are used, or a $K$-means centroid otherwise). The **appearance evidence** for
condition $k$ at time $t$ is the responsibility
$$
\log r_t(k)\;\propto\;-\tfrac{1}{2\varsigma_c^{2}}\,\lVert d_t-\mu^c_k\rVert^2 ,\qquad \textstyle\sum_k r_t(k)=1 .
$$
This reads the condition **from the visual descriptor only** — never from metadata — satisfying the test-time
protocol (the filter may not peek at the season folder).

**Label-free online inference.** The condition belief $b^c_t$ is a Bayesian filter on the condition chain alone:
prediction by the sticky kernel $T_c$, update by the appearance evidence (and, optionally, by how well each
condition *explains the place-matching scores*, §5). Because $T_c$ is sticky (F1), $b^c_t$ aggregates evidence over
a window and concentrates on the true condition — i.e. CCBF performs **test-time domain inference with no labels and
no gradient updates**. This is the mechanism we later show is both *consistent* (Thm 2) and *necessary* (Thm 1).

---

## 5. Inference: factored Bayesian filtering

The exact joint filter is a Bayes recursion over $(p_t,c_t)$ with $M'\!\times\!K$ states ($M'{=}M{+}1$). We keep it
linear in $M$ by a **factored (Rao-Blackwellized / mean-field) posterior** $\pi_t(p,c)\approx b^p_t(p)\,b^c_t(c)$.

### 5.1 Prediction
$$
\bar b^p_t = T_p * b^p_{t-1}\ \ (\text{banded convolution}),\qquad
\bar b^c_t = T_c\, b^c_{t-1}\ \ (\text{sticky}).
$$

### 5.2 Update (condition-mixture observation)
The one-step joint posterior is $\pi_t(j,k)\propto \bar b^p_t(j)\,\bar b^c_t(k)\,e^{\ell_t(j,k)}$. We refactor it:

* **Place update — marginalize the condition belief** (this is the condition-*adaptive* metric):
$$
\boxed{\,b^p_t(j)\;\propto\;\bar b^p_t(j)\,\sum_{k} b^c_t(k)\,\exp\!\big(\ell_t(j,k)\big)\,}
\quad\Longleftrightarrow\quad
\log(\cdot)=\log\bar b^p_t(j)+\operatorname*{logsumexp}_{k}\!\big[\log b^c_t(k)+\ell_t(j,k)\big].
$$
* **Condition update — appearance evidence (and optional place-marginalized fit):**
$$
b^c_t(k)\;\propto\;\bar b^c_t(k)\,r_t(k)\;\big[\,\cdot\;\exp\!\big(\textstyle\sum_j b^p_t(j)\,\ell_t(j,k)\big)\,\big].
$$
The bracketed factor (how well condition $k$ explains the matched scores) is optional; NB1 drives $b^c_t$ by the
appearance responsibility $r_t(k)$, which is simpler and already identifiable. All computation is in log-space with
`logsumexp` for numerical stability.

The place posterior $b^p_t$ yields the prediction $\hat p_t=\arg\max_{j\in\mathcal P} b^p_t(j)$, the **confidence**
$\hat q_t=\max_{j} b^p_t(j)$ (used for ECE), and the **off-map score** $b^p_t(\varnothing)$.

### 5.3 Null / off-map and the open-set decision
Localization is accepted iff $b^p_t(\varnothing)<\gamma$ (equivalently confidence $\hat q_t>1-\gamma$). Sweeping
$\gamma$ traces the open-set operating curve; because $b^p_t(\varnothing)$ is a *calibrated* posterior, this
threshold transfers across conditions — unlike a raw-score threshold.

### 5.4 Complexity
Per step: $\mathcal{O}(MK)$ for the mixture likelihood plus $\mathcal{O}(M\,w)$ for the banded motion ($w$ = kernel
width). Total $\mathcal{O}(T M K)$ — negligible beside the one-off $\mathcal{O}(({M+T})D)$ descriptor extraction,
and trivially batched on GPU. $K$ and the parameter count are tiny, so CCBF adds <1% overhead to any descriptor
pipeline.

---

## 6. Training procedure (offline, on cached descriptors)

1. **Extract & cache** global descriptors for the map and the train traversals (one forward pass; the only
   GPU-heavy step).
2. **Condition model.** Fit $K$ centroids $\{\mu^c_k\}$ (per-season means with train labels, else $K$-means) and the
   responsibility bandwidth $\varsigma_c$.
3. **Calibrated potentials.** For each condition $k$, fit $h_{1,k}$ (and the shared $h_0$) — or the temperature
   $\tau_k$ — by the proper-scoring objective of §3.3 on held-out train places, using a *different-condition map*
   for the match statistics to avoid identical-image degeneracy.
4. **Hyperparameters.** $(\rho,v,\sigma_m,\eta,\gamma)$ by grid/NLL on a validation traversal.

Everything after step 1 is seconds on cached features, enabling fast iteration.

---

## 7. Algorithm

```
Input: query descriptors d_{1:T}, map {r_j}, condition model {μ^c_k, ς_c}, potentials {ℓ(·,·)}, motion T_p, sticky ρ
Init:  b^p ← (1-π₀)/M on places, π₀ on ∅ ;  b^c ← uniform(K)
for t = 1..T:
    s_t[j] ← ⟨d_t, r_j⟩                                  # similarities
    # --- condition filter (label-free) ---
    b^c ← sticky_predict(b^c, ρ)
    log r_t(k) ← -‖d_t-μ^c_k‖²/(2ς_c²) ;  b^c ← softmax(log b^c + log r_t)
    # --- place filter (condition-adaptive, calibrated) ---
    b^p ← motion_predict(b^p, T_p)
    ℓℓ(j) ← logsumexp_k[ log b^c(k) + ℓ_t(j,k) ] ;  ℓℓ(∅) ← null_potential(s_t, b^c)
    b^p ← softmax(log b^p + ℓℓ)
    emit  p̂_t=argmax_j b^p(j),  q̂_t=max_j b^p(j),  offmap_t=b^p(∅),  ĉ_t=argmax_k b^c(k)
```
Offline smoothing replaces the forward pass by forward–backward (two-filter) for retrospective analysis.

---

## 8. Theory — miscalibration propagation

We formalize *why* a condition-agnostic observation model (every prior filtering-VPR method) is the real
bottleneck, and *why* CCBF fixes it. Throughout, $\Pr$ denotes the **true** model (condition-conditional emission
$\ell_t(\cdot,c_t)$) and $\widetilde{\Pr}$ the **baseline** filter that uses a single condition-agnostic potential
$\tilde\ell_t(\cdot)$ (e.g. one global temperature). Both share the same motion prior $T_p$ and initial prior.

**Definition 1 (calibration).** A confidence map $\hat q$ for the event $Y_t=\mathbb{1}[\hat p_t\ \text{correct}]$ is
*calibrated* if $\Pr(Y_t{=}1\mid \hat q_t=q)=q$ for all $q$. The Expected Calibration Error is
$\mathrm{ECE}=\mathbb{E}\big|\Pr(Y{=}1\mid\hat q)-\hat q\big|$.

**Definition 2 (potential error).** $\varepsilon_t(p):=\tilde\ell_t(p)-\ell_t(p,c_t)$, with accumulation
$E_T(p_{1:T}):=\sum_{t=1}^T \varepsilon_t(p_t)$.

### Lemma 1 (exact exponential tilt)
*The baseline trajectory-posterior is the true one, tilted by the accumulated potential error:*
$$
\widetilde{\Pr}(p_{1:T}\mid d_{1:T})=\Pr(p_{1:T}\mid d_{1:T})\;\frac{e^{E_T(p_{1:T})}}{\mathbb{E}_{\Pr}\!\big[e^{E_T}\big]} .
$$
**Proof.** Both posteriors factor as (prior $\times$ emissions), identical except the emission potentials:
$\widetilde{\Pr}\propto \big(\prod_t T_p(p_t|p_{t-1})\big)e^{\sum_t\tilde\ell_t(p_t)}$ and
$\Pr\propto \big(\prod_t T_p\big)e^{\sum_t\ell_t(p_t,c_t)}$. Their ratio is $e^{\sum_t(\tilde\ell_t-\ell_t)}=e^{E_T}$;
normalizing over $p_{1:T}$ under $\Pr$ gives the denominator. $\qquad\blacksquare$

Lemma 1 says the baseline does not make a *bounded* error — it **reweights entire trajectories** by an exponential
of a sum that grows with $T$. The next result turns this into a divergence rate.

### Theorem 1 (linear-in-$T$ divergence of the baseline posterior)
*Let $\mathrm{Var}_{\Pr_u}(E_T)$ denote the variance of $E_T$ under the tilted law
$d\Pr_u\propto e^{uE_T}d\Pr$. Suppose the condition genuinely modulates the emission and the baseline cannot match
it, in the quantitative sense*
$$
\inf_{u\in[0,1]}\;\tfrac1T\,\mathrm{Var}_{\Pr_u}(E_T)\;\ge\;v\;>\;0 \qquad(\text{non-degeneracy, N}).
$$
*Then*
$$
\mathrm{KL}\!\big(\Pr(\cdot\mid d_{1:T})\;\big\|\;\widetilde{\Pr}(\cdot\mid d_{1:T})\big)\;\ge\;\tfrac{v}{2}\,T .
$$
**Proof.** Center $E_T$: let $\phi(u)=\log\mathbb{E}_{\Pr}[e^{u(E_T-\mathbb{E}_\Pr E_T)}]$ be its cumulant generating
function. By Lemma 1, $\mathrm{KL}(\Pr\|\widetilde{\Pr})=\log\mathbb{E}_\Pr[e^{E_T}]-\mathbb{E}_\Pr[E_T]=\phi(1)$.
The CGF satisfies $\phi(0)=\phi'(0)=0$ and $\phi''(u)=\mathrm{Var}_{\Pr_u}(E_T)$ (standard exponential-family
identity). Taylor with integral remainder gives
$\phi(1)=\int_0^1(1-u)\,\phi''(u)\,du=\int_0^1(1-u)\,\mathrm{Var}_{\Pr_u}(E_T)\,du\ge vT\int_0^1(1-u)\,du=\tfrac{v}{2}T.$
$\qquad\blacksquare$

Assumption (N) holds whenever the per-step potential errors $\varepsilon_t(p_t^\star)$ are weakly dependent with
conditional variance bounded below — equivalently, whenever conditions carry information the single-$\tau$ baseline
discards. **The baseline posterior and the true posterior become mutually singular at a linear rate**: sequence
filtering on an uncalibrated, condition-agnostic model does not merely fail to help, it *actively degrades* with
longer sequences. This is miscalibration propagation.

### Proposition 2 (confidence corollary: a binary sequential test)
*Consider deciding on-track $H_1$ vs off-track $H_0$. With equal-variance Gaussian scores, the per-step true
log-likelihood-ratio is $\lambda_t=s_t\,(\mu_{c_t}{-}\mu_0)/\varsigma^2$ and, by §3.2, the baseline (single $\tau$)
uses $\tilde\lambda_t=\beta_{c_t}\lambda_t$ with $\beta_{c}=\tau^\star_{c}/\tau$. Under $H_1$ let $(\lambda_t,c_t)$ be
stationary ergodic with $\delta:=\mathbb{E}[(\beta_{c}-1)\lambda]$ and $\nu:=\mathrm{Var}[(\beta_{c}-1)\lambda]$.
The true log-odds are $\Lambda_T=\sum_t\lambda_t$ (confidence $q_T=\sigma(\Lambda_T)$); the baseline reports
$\tilde q_T=\sigma(\widetilde\Lambda_T)$, $\widetilde\Lambda_T=\sum_t\beta_{c_t}\lambda_t$. Then the stated-confidence
error in log-odds is*
$$
\widetilde\Lambda_T-\Lambda_T=\textstyle\sum_{t}(\beta_{c_t}-1)\lambda_t,
\qquad
\begin{cases}
=\delta\,T+o(T)\ \text{a.s.}, & \delta\neq 0\ \ (\Theta(T)\ \text{drift: systematic over/under-confidence}),\\[2pt]
=\Theta_{P}(\sqrt{T}), & \delta=0,\ \nu>0\ \ (\text{diffusive, still diverging}).
\end{cases}
$$
**Proof.** The identity is termwise. For $\delta\neq0$ the SLLN gives $\tfrac1T(\widetilde\Lambda_T-\Lambda_T)\to\delta$
a.s., hence magnitude $|\delta|T+o(T)$. For $\delta=0,\nu>0$ the CLT gives
$\widetilde\Lambda_T-\Lambda_T\Rightarrow\mathcal{N}(0,\nu T)$, i.e. $\Theta_P(\sqrt T)$. $\qquad\blacksquare$

Interpretation: a too-sharp miscalibration ($\beta>1$) makes the filter **overconfident by an amount that grows with
the sequence** and can trigger premature, self-reinforcing commitment to a wrong track (the motion prior then
sustains the error) — precisely the failure CCBF avoids by sizing $\tau_{c_t}$ to the *inferred* condition.

### Theorem 2 (CCBF is consistent and calibrated)
*Assume (A1) the emission family is well-specified, $g(\cdot\mid p,c)$ lies in it; (A2) the potentials are fit by a
strictly proper scoring rule with sufficient data; (A3) conditions are identifiable (distinct $\{h_{1,k}\}$) and the
sticky condition chain is ergodic; (A4) the motion model is correct. Then the CCBF filtered posterior converges to
the exact Bayesian posterior,*
$$
\big\lVert\, b^p_t-\Pr(p_t\mid d_{1:t})\,\big\rVert_{\mathrm{TV}}\xrightarrow[t\to\infty]{}0,
$$
*and is therefore asymptotically calibrated (Def 1), with vanishing potential error $\varepsilon_t\to0$ — so the KL
term of Theorem 1 does not accumulate.*

**Proof sketch.** By (A2) and strict propriety, the population minimizer of the training objective is the true
conditional, so $\widehat h_{1,k}\to h_{1,k}$ (Gneiting & Raftery, 2007); with (A1) the learned emission equals the
true one. *Known/observed condition:* CCBF is then exact Bayesian filtering, whose posterior is calibrated by the
tower property, $\Pr(Y{=}1\mid \Pr(\cdot\mid d_{1:t}))=\Pr(\cdot\mid d_{1:t})$. *Inferred condition:* the condition
marginal is a finite-state HMM with informative emissions (A3); by Bayesian/HMM filter consistency and geometric
ergodicity under mixing (Baum & Petrie, 1966; Douc, Moulines & Rydén), $b^c_t$ concentrates on $c_t$ at a geometric
rate, so the mixture potential $\sum_k b^c_t(k)e^{\ell_t(\cdot,k)}$ converges to $e^{\ell_t(\cdot,c_t)}$; continuity
of the (normalized, Lipschitz) filter map propagates this to $b^p_t$, giving TV-convergence to the exact posterior.
The mean-field refactorization error is controlled because $T_p$ and $T_c$ act on different coordinates and the
coupling enters only through the shared emission, which the mixture update integrates exactly. $\qquad\blacksquare$

### Remarks (scope — what the theory does and does not claim)
* Theorem 1 needs the **non-degeneracy (N)**: if conditions are truly irrelevant ($v{=}0$), the baseline is fine and
  CCBF reduces to it (the $K{=}1$ ablation). The claim is *conditional on appearance change mattering* — exactly the
  regime of hard benchmarks.
* A *homogeneous* temperature error distorts the reliability curve by a fixed amount (not growing in $T$); the
  growth in Thm 1 / Prop 2 comes from **condition heterogeneity and drift**, the realistic case. We state this
  explicitly to avoid over-claiming.
* Theorem 2 is asymptotic and well-specified; finite-sample and mis-specification gaps are quantified empirically
  (ECE, reliability diagrams) rather than bounded here.

---

## 9. Why each component earns its place (ablation logic)

| Component | Role | Removing it costs |
|---|---|---|
| **Condition latent $c_t$** | makes the emission adaptive; enables label-free TTA | collapses to the fixed-observation baseline ⇒ Thm 1 divergence returns ($K{=}1$ ablation) |
| **Calibrated potential $\ell(\cdot,k)$** | turns scores into proper likelihoods | posterior/off-map threshold miscalibrated across conditions (ECE↑, open-set AUROC↓) |
| **Sticky prior $\rho$** | integrates condition evidence over a window | condition belief gets noisy/unidentifiable; TTA degrades to per-frame guessing |
| **Motion model $T_p$** | temporal place prior | loses sequence gain; reverts toward single-image recall |
| **Null state $\varnothing$** | principled open-set | no calibrated "lost" detection |

Each is minimal and justified; the system is a *thin* probabilistic layer, not a heavy pipeline.

---

## 10. Assumptions and limitations
* **Conditional independence** of non-match scores (§3.1) is the usual VPR idealization; correlated clutter weakens
  but does not void the LLR (a standard robust-likelihood caveat).
* **Quasi-1-D motion** fits route-following benchmarks (Nordland, RobotCar, CMU); general topologies need a graph
  motion model (straightforward extension of $T_p$).
* **Condition identifiability** can fail when two conditions are visually indistinguishable; then $b^c$ stays diffuse
  and CCBF *gracefully* falls back toward the mixture-average temperature (no catastrophic failure — a safety
  property worth stating in rebuttal).

---

*References (classical, for the theory): Gneiting & Raftery, “Strictly Proper Scoring Rules, Prediction, and
Estimation”, JASA 2007; Baum & Petrie, “Statistical Inference for Probabilistic Functions of Finite State Markov
Chains”, Ann. Math. Stat. 1966; Douc, Moulines & Rydén, consistency of HMM estimators. VPR context: Cummins &
Newman (FAB-MAP); Xu et al. 2021 (probabilistic appearance-invariant topometric localization); Izquierdo & Civera
2024 (SALAD); Zaffar et al. 2024 (image-matching uncertainty).*
