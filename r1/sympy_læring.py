import sympy

sympy.init_printing(use_unicode=True)
# sympy.init_printing(use_latex=True)

x, y = sympy.symbols("x y")
uttrykk = x**2 - 1

print(uttrykk)
print(sympy.latex(uttrykk))
print(sympy.factor(uttrykk))
print(sympy.latex(sympy.expand((x - 3) ** 3)))
print(sympy.solve(uttrykk, x))
print(sympy.limit(uttrykk, x, 0))

# likningssett
likning1 = sympy.Eq(x + y, 2)
likning2 = sympy.Eq(2 * x + y, 3)
print(sympy.solve((likning1, likning2), (x, y)))

print(sympy.log(x * y))
print(sympy.expand_log(sympy.log(x * y)))

print(sympy.diff(x**3, x))
print(sympy.diff(x**3, x, 2))  # dobbelt derivert

uttrykk = sympy.exp(x**2 + 1)
d_uttrykk = sympy.diff(uttrykk, x)
print(uttrykk)
print(d_uttrykk)
print(sympy.latex(sympy.factor(d_uttrykk)))

print(sympy.oo, -sympy.oo)
print(sympy.limit(sympy.exp(4 - 2 * x), x, sympy.oo))

delt_forskrift = sympy.Piecewise((x**2, x < 0), (x, x >= 0))
print(delt_forskrift)
delt_venstreside = sympy.limit(delt_forskrift, x, 0, dir="-")  # direction
delt_høyreside = sympy.limit(delt_forskrift, x, 0, dir="+")  # direction

d_delt_forskrift = sympy.diff(delt_forskrift)
print(d_delt_forskrift)

# sympy.plot(
#     sympy.exp(x),
#     (100 * x),
#     (x, -1, 6),
#     title="Nydelig vakker graf",
#     xlabel="x timer etter noe",
#     # backend="text", # støtter kun ett uttrykk om gangen
#     legend=True,
# )
