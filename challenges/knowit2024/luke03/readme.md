# Pytt i julepanne

Alvefine setter seg ned for å nyte sitt daglige julemåltid. Hun spiser såklart `ris`, `erter`, `gulrøtter`, `reinsdyrkjøtt` og hennes favoritt: `julekringle`. Hun ELSKER `julekringle`, men må spise opp resten av maten før hun kan begynne på den sier Alvemor.

Tallerkenen hennes starter med 100g av hver type mat. Hvert sekund kan hun spise 5g av én type mat og 3g av en annen type mat, prioritert fra venstre i listen. Hun kan kun spise 2g kjøtt om gangen, og hun liker ikke å spise det sammen med noe. Hun får kun lov til å spise 1g julekringle om gangen, og det går såklart heller ikke å spise sammen med noe annet.

Alvemor fyller på mat etterhvert som Alvefine spiser: Tallene under viser hvor mange gram av en type mat som fylles på hver gang det kommer mer. Når man er gått gjennom lista en gang starter man på nytt i det uendelige. `ris`, `erter `og `gulrøtter `fylles på hvert sekund.

```
ris: [0, 0, 1, 0, 0, 2]
erter: [0, 3, 0, 0]
gulrøtter: [0, 1, 0, 0, 0, 8]
reinsdyrkjøtt: [100, 80, 40, 20, 10]
julekringle: -
```

I tillegg er det noen spesielle regler:

- Gulrøtter begynner ikke med påfyll før etter 30 sekunder.
- Reinsdyrkjøtt fylles ikke på før det er helt tomt, og etter det er tomt går det 50 sekunder før Alvemor kommer med påfyll.
- Det er ikke mer reinsdyrkjøtt når den opprinnelige listen er ferdig.
- Julekringle fylles ikke på.

Begynnelsen ser slik ut:

- `t=0` Alvefine spiser 5g ris og 3g erter. Alvemor fyller på 0g ris og 0g erter, påfyll av gulrøtter har ikke begynt. Det er masse kjøtt, så ingen påfyll begynner.
- `t=1` Alvefine spiser 5g ris og 3g erter. Alvemor fyller på 0g ris og 3g erter.
- `t=2` Alvefine spiser 5g ris og 3g erter. Alvemor fyller på 1g ris og 0g erter.
- ...
- `t=22` Det er tomt for ris. Alvefine spiser 5g erter og 3g gulrøtter.
- ...
- `t=71` Alvefine spiser den første biten med reinsdyrkjøtt.
- ...
- `t=269` Den første biten julekringle treffer endelig munnen!!!

Hvor mange sekunder tar det Alvefine å spise opp all julekringla mens Alvemor fortsetter å fylle på den andre maten?
