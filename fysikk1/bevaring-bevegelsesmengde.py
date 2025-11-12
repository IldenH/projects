m_a = 32 / 1000  # kg
m_b = 45 / 1000  # kg
v_a = 0  # m/s
v_b = 0.75  # m/s
u_b = 0.30  # m/s

u_a = (m_a * v_a + m_b * (v_b - u_b)) / m_a
print(u_a)
