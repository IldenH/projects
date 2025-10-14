def annuitetslån(lån, rente, annuitet):
    antall_terminer = 0
    print(f"{'Terminer':>15}\t{'Start':>15}\t{'Avdrag':>15}\t{'Rente':>15}\t{'Restlån':>15}")
    while lån > 0:
        antall_terminer += 1
        start = lån
        rentebeløp = lån * rente
        avdrag = annuitet - rentebeløp
        if avdrag <= 0:
            raise Exception(f"For lav annuitet, annuiteten må være > {rentebeløp:_.0f}")
        lån -= avdrag
        print(f"{antall_terminer:>15}\t{start:>15.2f}\t{avdrag:>15.2f}\t{rentebeløp:>15.2f}\t{lån:>15.2f}")

annuitetslån(100_000, 0.03, 15_000)
