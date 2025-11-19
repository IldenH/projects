m_a = 32 / 1000  # kg
m_b = 45 / 1000  # kg
v_a = 0.63  # m/s
v_b = 0.75  # m/s
u_b = 0.30  # m/s

u_a = (m_a * v_a + m_b * (v_b - u_b)) / m_a

ek_før = 1/2 * m_a * v_a ** 2 + 1/2 * m_b * v_b ** 2
ek_etter = 1/2 * m_a * u_a ** 2 + 1/2 * m_b * u_b ** 2

if abs(ek_før - ek_etter) < 1e-3:
    print("Elastisk")
else:
    print("Uelastisk")
    print(f"{abs(ek_før - ek_etter)} J går ut i omgivelsene")
print(f"{u_a} m/s")
