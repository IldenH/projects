from math import sqrt, cos

type vektor = tuple[float, float]
type skalar = float


def length(u: vektor) -> skalar:
    x, y = u
    return sqrt(x**2 + y**2)


def skalarprodukt(u: vektor, v: vektor, alpha: skalar = 90) -> skalar:
    return length(u) * length(v) * cos(alpha)


def ortogonal(u: vektor, v: vektor) -> bool:
    return skalarprodukt(u, v) == 0


def parallel(u: vektor, v: vektor) -> bool:
    if isNullVektor(u) or isNullVektor(v):
        return False
    return skalarprodukt(u, v, 0) == skalarprodukt(u, v)


def isNullVektor(u: vektor) -> bool:
    (x, y) = u
    return x == 0 and y == 0


if __name__ == "__main__":
    vektor1 = (4, 1)
    vektor2 = (-4, 16)

    print(ortogonal(vektor1, vektor2))
    print(parallel(vektor1, vektor2))
