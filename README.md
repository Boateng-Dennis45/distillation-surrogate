# Neural-Network Surrogate of a Benzene–Toluene Distillation Column (Aspen Plus + Python)

A small end-to-end project: generate data from an Aspen Plus RadFrac column, train machine-learning surrogates in Python, stress-test them, use the surrogate to optimize operating conditions, and verify the result against the original simulator.

**Author:** Dennis Boateng Adu (GitHub: Boateng-Dennis45)

## What this project does

1. Builds a benzene–toluene distillation column in Aspen Plus V14.
2. Samples 1,000 operating cases (Latin hypercube) and runs each one in Aspen automatically from Python (COM automation).
3. Trains and compares four model types as surrogates for reboiler duty and distillate purity.
4. Tests how each model behaves when asked to predict outside its training range.
5. Uses the best surrogate to minimize reboiler duty subject to purity and recovery constraints.
6. Checks the optimum against Aspen.

## Process model

- Aspen Plus V14, RadFrac, equilibrium calculation
- 20 stages, total condenser, kettle reboiler, feed on stage 10 (above-stage)
- Pressure 1 atm, Peng–Robinson property method
- Feed: saturated liquid, benzene/toluene

The Aspen files are not included in this repository (licensing). The set-up above is enough to rebuild the model.

## Dataset

| Input | Range |
|---|---|
| Feed flow (kmol/h) | 80 – 120 |
| Benzene mole fraction in feed | 0.40 – 0.60 |
| Reflux ratio | 1.5 – 4.0 |
| Distillate-to-feed ratio D/F | 0.35 – 0.60 |

Samples were drawn with a Latin hypercube (seed 42). Distillate flow is D = F × (D/F). Recorded outputs: reboiler and condenser duty, benzene mole fraction in distillate and bottoms.

Quality checks: all 1,000 runs completed without error, and all satisfy the benzene mass balance F·z = D·xD + B·xB to within 0.01 kmol/h.

Because D/F and feed composition were sampled independently, many cases ask for more distillate than the feed has benzene (D/F > z). Purity in those cases is capped at z/(D/F) regardless of reflux, which produces a low-purity tail in the data (minimum xD about 0.69).

## Models

Linear regression, random forest, gradient boosting, and a small neural network (two hidden layers of 32 units, L-BFGS solver, inputs standardized). Purity is modeled as "nines", −log10(1 − xD), which stretches out the region near 1.0.

Engineered feature: **boilup = D × (R + 1)**, which comes from the vapor balance around the condenser and is roughly proportional to reboiler duty. Two other physics-based features for purity (the cap z/(D/F) and the difference D/F − z) were also tried and did **not** improve the neural network.

## Results

### 5-fold cross-validation, reboiler duty (R²)

| Model | Base inputs | + boilup |
|---|---|---|
| Linear | 0.9767 | 0.9991 |
| Random forest | 0.9849 | 0.9981 |
| Gradient boosting | 0.9895 | 0.9989 |
| Neural network | 0.9977 | 0.9999 |

The boilup feature turns a linear model from 0.977 to 0.999. Neural network scores in this table used the default Adam solver and hit the iteration limit; the L-BFGS version used later converged.

### Distillate purity

With the same four inputs, switching the neural network from the default Adam solver to L-BFGS raised R² on "nines" from 0.983 to 0.9996. With L-BFGS, the 5-fold cross-validated mean absolute error is 0.0012 in purity overall and 0.0001 in the region xD ≥ 0.98. Linear regression performs poorly on purity (R² about 0.75) because purity saturates near 1.0.

### Extrapolation test

Trained on reflux ratio < 3.2 (680 cases) and tested on reflux ratio ≥ 3.2 (320 cases):

| Model | Duty R² | Duty MAE (kW) | Purity ("nines") R² | MAE ("nines") |
|---|---|---|---|---|
| Linear (+ boilup) | 0.998 | 13.3 | 0.706 | 0.516 |
| Random forest | 0.460 | 242 | 0.939 | 0.191 |
| Gradient boosting | 0.635 | 191 | 0.907 | 0.249 |
| Neural network (+ boilup for duty) | 0.9999 | 2.3 | 0.9935 | 0.048 |

Tree-based models cannot predict outside the range they were trained on, so their predictions flatten at the edge. The neural network kept tracking Aspen for both outputs.

![Stress test](figures/fig_stress_test.png)
![Parity plots](figures/fig_parity.png)

### Optimization

Feed fixed at 100 kmol/h, 50 mol% benzene. Decision variables: reflux ratio R and distillate rate D. Objective: minimize reboiler duty. Constraints: xD ≥ 0.99 and benzene recovery D·xD/(F·z) ≥ 0.95.

The recovery constraint is necessary. Without it, the optimizer can take a tiny distillate stream, which is trivially pure and cheap but discards most of the benzene.

SLSQP from 10 random starting points all converged to the same point, and a 126 × 126 grid search agreed to within 1 kW.

| | Surrogate | Aspen |
|---|---|---|
| Reflux ratio | 1.739 | 1.739 |
| Distillate (kmol/h) | 47.98 | 47.98 |
| Reboiler duty (kW) | 1131.6 | 1131.8 |
| Distillate purity | 0.99000 | 0.98985 |
| Recovery | 0.9500 | 0.9499 |

Duty is predicted to within 0.2 kW. The optimum sits exactly on both constraints, and Aspen's purity at that point (0.98985) is 0.00015 below the target, so the surrogate's optimum is marginally infeasible in the real column. This is expected when an optimizer lands on a constraint boundary.

Further Aspen runs at D = 47.98 kmol/h located the true boundary:

| Reflux ratio | Aspen duty (kW) | Aspen xD | Recovery |
|---|---|---|---|
| 1.739 (surrogate optimum) | 1131.8 | 0.98985 | 0.9499 |
| 1.744 | 1133.8 | 0.99001 | 0.9500 |
| 1.745 | 1134.2 | 0.99003 | 0.9500 |
| 1.750 | 1136.2 | 0.99017 | 0.9502 |

The smallest tested reflux ratio that satisfies both constraints in Aspen is R = 1.744, with a duty of 1,133.8 kW. The surrogate's optimum was therefore about 0.005 low in reflux ratio and about 2 kW (0.2%) low in duty. A linear interpolation between the earlier Aspen points predicted R of about 1.745 and about 1,134 kW, which agrees with the Aspen result.

![Surrogate vs Aspen](figures/fig_optimum_vs_aspen.png)

For a real design, add a safety margin (for example, target xD ≥ 0.9905) rather than operating exactly on the limit.

## Limitations

- One column, fixed number of stages and feed stage, one thermodynamic model, one pressure. Data are noise-free simulation output, not plant data.
- Equilibrium-stage model only; no tray hydraulics or efficiency.
- The extrapolation test varied only reflux ratio and extended it about 25% beyond the training range. Larger extrapolations were not tested.
- Test errors are reported from single splits and 5-fold cross-validation on one dataset; no repeated experiments.
- The neural network is not guaranteed to extrapolate in general. The result here may partly reflect how close to linear the duty is.
- The surrogate optimum was verified at only ten reflux ratios and one distillate rate.

## How to reproduce

1. Build the Aspen column described above and save it as `column.bkp`.
2. Install Python 3.13/3.14 and `pip install pywin32` (Windows only, needed for COM automation).
3. Generate `inputs.csv` with the Latin hypercube cell in the notebook.
4. Run `python run_aspen.py` (set `MAX_ROWS = None` for all 1,000 cases) to create `results.csv`.
5. Run `python check_results.py` to confirm the mass balances.
6. Open `surrogate_modeling.ipynb` (for example in Google Colab), upload `results.csv`, and run the cells in order.
7. Run `python verify_aspen.py` to check optimization results against Aspen.

## Files

| File | Purpose |
|---|---|
| `run_aspen.py` | Runs the sampled cases in Aspen and writes `results.csv` |
| `check_results.py` | Mass-balance check on the results |
| `verify_aspen.py` | Runs chosen cases in Aspen to verify surrogate predictions |
| `inputs.csv`, `results.csv` | Sampled inputs and Aspen outputs |
| `surrogate_modeling.ipynb` | Model training, comparison, stress test, optimization |
| `figures/` | Plots used in this README |

## Possible extensions

- Add more points near the optimum and retrain (adaptive sampling).
- Add pressure and feed temperature as inputs.
- Add prediction-uncertainty estimates (for example, a Gaussian process or ensemble).
- Try physics-informed training, with mass and energy balances in the loss.
- Extend to a ternary system or a full flowsheet.ng).
Add pressure and feed temperature as inputs.
Add prediction-uncertainty estimates (for example, a Gaussian process or ensemble).
Try physics-informed training, with mass and energy balances in the loss.
Extend to a ternary system or a full flowsheet.
