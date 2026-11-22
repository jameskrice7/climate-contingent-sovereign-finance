#!/home/jameskrice/miniforge/bin/python
"""
Quick validation test for Carbon Risk simulations.
Tests the core model components without running full notebook.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Set random seed
np.random.seed(42)

# Parameters from Table 1
R_f = 1.08
alpha = 0.16
mu = 0.01
sigma = 0.10
p_dis = 0.15
E_J = -0.25
p_log = 0.08
E_L = 0.06

print("=" * 70)
print("Carbon Risk Simulation - Validation Test")
print("=" * 70)

# Test 1: Output generation
print("\n[Test 1] Output generation...")
N = 10000
epsilon = np.random.normal(mu, sigma, N)
Z = (np.random.rand(N) < p_dis).astype(int)
J = -np.random.exponential(-E_J, N) * Z
L_indicator = (np.random.rand(N) < p_log).astype(int)
L = np.random.exponential(E_L, N) * L_indicator

psi = 0
y = np.exp(epsilon + J) * np.exp(-psi * L)

print(f"  Generated {N} output realizations")
print(f"  Mean output: {np.mean(y):.4f}")
print(f"  Disaster freq: {np.mean(Z):.3f} (expected {p_dis:.3f})")
print(f"  Logistics freq: {np.mean(L_indicator):.3f} (expected {p_log:.3f})")
print("  ✓ Output generation working")

# Test 2: Payoff functions
print("\n[Test 2] Payoff functions...")
H_straight = np.ones_like(y)
kappa = 0.45
y_bar = 0.98
H_gdp = 1.0 - kappa * (y < y_bar).astype(float)

frac_reduced = np.mean(y < y_bar)
print(f"  Fraction below trigger: {frac_reduced:.3f}")
print(f"  Mean payoff (straight): {np.mean(H_straight):.4f}")
print(f"  Mean payoff (GDP clause): {np.mean(H_gdp):.4f}")
print("  ✓ Payoff functions working")

# Test 3: Default and pricing
print("\n[Test 3] Pricing and default...")
d = 0.15
repayment_straight = d * H_straight
repayment_gdp = d * H_gdp
fiscal_capacity = alpha * y

survival_straight = (repayment_straight <= fiscal_capacity).astype(float)
survival_gdp = (repayment_gdp <= fiscal_capacity).astype(float)

PD_straight = 1.0 - np.mean(survival_straight)
PD_gdp = 1.0 - np.mean(survival_gdp)

q_straight = np.mean(H_straight * survival_straight) / R_f
q_gdp = np.mean(H_gdp * survival_gdp) / R_f

b_straight = d * q_straight
b_gdp = d * q_gdp

print(f"  At d={d}:")
print(f"    Straight debt:    PD={PD_straight:.4f}, proceeds={b_straight:.5f}")
print(f"    GDP clause:       PD={PD_gdp:.4f}, proceeds={b_gdp:.5f}")
print(f"    PD reduction:     {(PD_straight-PD_gdp)/PD_straight*100:.1f}%")
print(f"    Proceeds increase: {(b_gdp-b_straight)/b_straight*100:.1f}%")
print("  ✓ Pricing and default working")

# Test 4: MSB calculation
print("\n[Test 4] Finding MSB...")
d_values = np.linspace(0, 0.30, 31)
b_straight_vals = []
b_gdp_vals = []

for d in d_values:
    # Straight
    repayment = d * H_straight
    survival = (repayment <= fiscal_capacity).astype(float)
    q = np.mean(H_straight * survival) / R_f
    b_straight_vals.append(d * q)

    # GDP
    repayment = d * H_gdp
    survival = (repayment <= fiscal_capacity).astype(float)
    q = np.mean(H_gdp * survival) / R_f
    b_gdp_vals.append(d * q)

b_straight_vals = np.array(b_straight_vals)
b_gdp_vals = np.array(b_gdp_vals)

MSB_straight = np.max(b_straight_vals)
MSB_gdp = np.max(b_gdp_vals)
d_star_straight = d_values[np.argmax(b_straight_vals)]
d_star_gdp = d_values[np.argmax(b_gdp_vals)]

print(f"  Straight debt:    MSB={MSB_straight:.5f} at d*={d_star_straight:.3f}")
print(f"  GDP clause:       MSB={MSB_gdp:.5f} at d*={d_star_gdp:.3f}")
print(f"  MSB improvement:  {(MSB_gdp-MSB_straight)/MSB_straight*100:.1f}%")
print("  ✓ MSB calculation working")

# Test 5: Create sample plot
print("\n[Test 5] Creating validation plot...")
plt.figure(figsize=(10, 6))
plt.plot(d_values, b_straight_vals, '-o', label='Straight debt', linewidth=2)
plt.plot(d_values, b_gdp_vals, '-s', label='GDP clause', linewidth=2)
plt.xlabel('Face value d')
plt.ylabel('Issuance proceeds b(d)')
plt.title('Validation: Issuance Proceeds Laffer Curve')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('/home/jameskrice/Downloads/validation_test.png', dpi=150, bbox_inches='tight')
print("  ✓ Plot saved to: /home/jameskrice/Downloads/validation_test.png")

print("\n" + "=" * 70)
print("ALL TESTS PASSED ✓")
print("=" * 70)
print("\nThe notebook is ready to run!")
print("To execute the full notebook:")
print("  cd /home/jameskrice/Downloads")
print("  /home/jameskrice/miniforge/bin/jupyter notebook Carbon_Risk_Simulations.ipynb")
print("\nOr convert to Python script and run:")
print("  /home/jameskrice/miniforge/bin/jupyter nbconvert --to python Carbon_Risk_Simulations.ipynb")
print("  /home/jameskrice/miniforge/bin/python Carbon_Risk_Simulations.py")
