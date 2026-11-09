# Porównanie orkiestratora z algorytmem Karmarkara–Karpa

## 1. Cel
Orkiestrator (`src/orchestrator.py`) przy $\mathrm{CV} \le \tau$ dzieli cały zbiór algorytmem KK, a przy $\mathrm{CV} > \tau$ wybiera ścieżkę LP+GNP opisaną w rozdziale o orkiestratorze (`orkiestrator.md`). Celem badania jest sprawdzenie, czy orkiestrator daje lepsze podziały niż sam algorytm KK i jakim kosztem czasowym. Porównujemy dwa progi:

- $\tau = 0{,}6$ – próg domyślny,
- $\tau = 4{,}26$ – próg minimax wyznaczony w rozdziale o wyborze progu CV.

## 2. Metoda
Podobnie jak przy wyborze progu, korzystamy z tego, że próg decyduje tylko o wyborze ścieżki. Każdy zbiór dzielimy raz algorytmem KK i raz orkiestratorem z progiem $0$, który na każdym zbiorze używa LP+GNP. Wynik orkiestratora z progiem $\tau$ to wynik KK, gdy zmierzone CV zbioru nie przekracza $\tau$, a w przeciwnym razie wynik LP+GNP. Oba progi oceniamy więc na tych samych zbiorach.

Dane wygenerowano generatorem o zadanym CV:

- rozkłady log-normalny, gamma i jednostajny, średnia $10\,000$,
- $n \in \{100, 1000\}$, $k \in \{3, 5\}$,
- zadane CV: $0{,}1; 0{,}2; \dots; 0{,}5$ oraz $0{,}6; 0{,}8; \dots; 6{,}0$ (wartości nieosiągalne dla rozkładu są pomijane, dla rozkładu jednostajnego zostaje $0{,}1$–$0{,}5$),
- 5 zbiorów na każdą kombinację (rozkład, $n$, $k$, CV), łącznie 1420 zbiorów,
- limit czasu LP: 1 s, `seed = 0`.

Generator każdego scenariusza (rozkład, $n$, $k$) ma ziarno wyprowadzone z `seed`, więc zmiana ustawień jednego scenariusza nie zmienia zbiorów pozostałych.

Miarą jakości jest rozpiętość $D = \max_j S_j - \min_j S_j$. Oznaczamy przez $D_{\mathrm{KK}}$ rozpiętość podziału KK, przez $D_{\mathrm{LP}}$ rozpiętość podziału LP+GNP, a przez $D_{\mathrm{O}}$ rozpiętość podziału orkiestratora z danym progiem. Wyniki porównujemy na każdym zbiorze osobno oraz za pomocą ilorazu
$$
q = \frac{D_{\mathrm{LP}} + 1}{D_{\mathrm{KK}} + 1}.
$$
Wartość $q > 1$ oznacza, że KK dał mniejszą rozpiętość, a jedynka w liczniku i mianowniku pozwala porównywać podziały o rozpiętości $0$. Czas mierzymy dla każdego zbioru i podajemy medianę oraz 95. percentyl.

## 3. Uruchomienie
```sh
cd src
uv run python kk_vs_orchestrator.py --quick        # szybki test
uv run python kk_vs_orchestrator.py --seed 0       # pełne badanie
uv run python kk_vs_orchestrator.py --report-only  # tylko raport
```
Wyniki trafiają do `src/results/kk_vs_orchestrator/`: `results.json` (wszystkie zbiory), `report.md` (tabele). Pełne badanie trwało około 16 minut (Python 3.13, PuLP 4.0.0, highspy 1.15.1, Windows 11, procesor AMD).

## 4. Wyniki

### 4.1. Zmierzone CV
| Rozkład | $n$ | mediana CV | max CV | CV > 0,6 | CV > 4,26 | udział jedynek |
| ----------- | ------ | -------- | -------- | -------- | -------- | -------- |
| lognormal | 100 | 1,71 | 7,06 | 83% | 2% | 0% |
| lognormal | 1000 | 2,34 | 17,70 | 83% | 8% | 0% |
| gamma | 100 | 2,57 | 7,61 | 83% | 15% | 29,8% |
| gamma | 1000 | 2,71 | 7,70 | 83% | 24% | 29,6% |
| uniform | 100 | 0,31 | 0,56 | 0% | 0% | 0% |
| uniform | 1000 | 0,30 | 0,52 | 0% | 0% | 0% |

Dla rozkładu log-normalnego zmierzone CV jest przy dużym zadanym CV wyraźnie niższe od zadanego: dla zadanego CV $= 5$ średnio $2{,}61$ przy $n = 100$ i $3{,}81$ przy $n = 1000$. Rozkład gamma odtwarza zadane CV dokładniej ($4{,}04$ i $4{,}72$), ale jedynki stanowią średnio około 30% wartości wszystkich zbiorów z tego rozkładu, a przy dużym CV jeszcze więcej. Rozkład jednostajny nie przekracza progu $0{,}6$, więc orkiestrator zawsze używa na nim KK.

### 4.2. Orkiestrator a KK
Każdy scenariusz obejmuje 165 zbiorów. Kolumna „CV > $\tau$” podaje liczbę zbiorów, na których orkiestrator wybrał LP+GNP, a mediana $q$ jest liczona tylko na tych zbiorach. Na 100 zbiorach z rozkładu jednostajnego orkiestrator przy obu progach daje ten sam wynik co KK, dlatego tabele ich nie obejmują.

Próg $\tau = 0{,}6$:

| Scenariusz | CV > $\tau$ | $D_{\mathrm{O}} < D_{\mathrm{KK}}$ | $D_{\mathrm{O}} = D_{\mathrm{KK}}$ | $D_{\mathrm{O}} > D_{\mathrm{KK}}$ | mediana $q$ |
| -------------------------- | -------- | ----------- | ----------- | ----------- | -------- |
| lognormal, $n = 100$, $k = 3$ | 136 | 0 | 39 | 126 | 28,9 |
| lognormal, $n = 100$, $k = 5$ | 137 | 5 | 55 | 105 | 3,6 |
| lognormal, $n = 1000$, $k = 3$ | 137 | 0 | 34 | 131 | 11,0 |
| lognormal, $n = 1000$, $k = 5$ | 137 | 0 | 29 | 136 | 14,0 |
| gamma, $n = 100$, $k = 3$ | 136 | 1 | 132 | 32 | 1,0 |
| gamma, $n = 100$, $k = 5$ | 137 | 8 | 115 | 42 | 1,0 |
| gamma, $n = 1000$, $k = 3$ | 136 | 0 | 152 | 13 | 1,0 |
| gamma, $n = 1000$, $k = 5$ | 138 | 0 | 149 | 16 | 1,0 |

Próg $\tau = 4{,}26$:

| Scenariusz | CV > $\tau$ | $D_{\mathrm{O}} < D_{\mathrm{KK}}$ | $D_{\mathrm{O}} = D_{\mathrm{KK}}$ | $D_{\mathrm{O}} > D_{\mathrm{KK}}$ | mediana $q$ |
| -------------------------- | -------- | ----------- | ----------- | ----------- | -------- |
| lognormal, $n = 100$, $k = 3$ | 6 | 0 | 165 | 0 | 1,0 |
| lognormal, $n = 100$, $k = 5$ | 2 | 0 | 164 | 1 | 1,0 |
| lognormal, $n = 1000$, $k = 3$ | 15 | 0 | 153 | 12 | 3,0 |
| lognormal, $n = 1000$, $k = 5$ | 13 | 0 | 153 | 12 | 6,0 |
| gamma, $n = 100$, $k = 3$ | 26 | 0 | 164 | 1 | 1,0 |
| gamma, $n = 100$, $k = 5$ | 25 | 0 | 163 | 2 | 1,0 |
| gamma, $n = 1000$, $k = 3$ | 38 | 0 | 165 | 0 | 1,0 |
| gamma, $n = 1000$, $k = 5$ | 42 | 0 | 165 | 0 | 1,0 |

Łącznie na 1420 zbiorach:

- przy progu $0{,}6$ orkiestrator wybrał LP+GNP na 1094 zbiorach (77%). Dał mniejszą rozpiętość niż KK na 14 z nich, równą na 479 i większą na 601,
- przy progu $4{,}26$ wybrał LP+GNP na 167 zbiorach (12%). Na żadnym z nich nie dał mniejszej rozpiętości niż KK, na 139 dał równą, a na 28 większą.

### 4.3. LP+GNP a KK w przedziałach zmierzonego CV
Tabele porównują LP+GNP i KK na wszystkich zbiorach, niezależnie od progu.

Rozkład log-normalny:

| $n$ | CV | $D_{\mathrm{LP}} < D_{\mathrm{KK}}$ | $D_{\mathrm{LP}} = D_{\mathrm{KK}}$ | $D_{\mathrm{LP}} > D_{\mathrm{KK}}$ | mediana $D_{\mathrm{KK}}$ | mediana $D_{\mathrm{LP}}$ | mediana $q$ |
| ------ | ----------- | ----------- | ----------- | ----------- | --------- | --------- | -------- |
| 100 | (0; 0,6] | 0 | 0 | 57 | 8 | 1915 | 128,8 |
| 100 | (0,6; 1] | 0 | 0 | 22 | 6 | 834 | 98,2 |
| 100 | (1; 2] | 2 | 0 | 118 | 4 | 124 | 15,7 |
| 100 | (2; 3] | 3 | 17 | 77 | 6 | 56 | 6,1 |
| 100 | (3; 4,26] | 0 | 13 | 13 | 47015 | 47015 | 1,0 |
| 100 | > 4,26 | 0 | 7 | 1 | 303313 | 320326 | 1,0 |
| 1000 | (0; 0,6] | 0 | 0 | 56 | 1 | 2310 | 1052,8 |
| 1000 | (0,6; 1] | 0 | 0 | 21 | 1 | 611 | 375,5 |
| 1000 | (1; 2] | 0 | 0 | 60 | 1 | 134 | 69,0 |
| 1000 | (2; 3] | 0 | 0 | 97 | 1 | 15 | 10,5 |
| 1000 | (3; 4,26] | 0 | 3 | 65 | 1 | 9 | 6,8 |
| 1000 | > 4,26 | 0 | 4 | 24 | 1 | 8 | 4,5 |

Rozkład gamma:

| $n$ | CV | $D_{\mathrm{LP}} < D_{\mathrm{KK}}$ | $D_{\mathrm{LP}} = D_{\mathrm{KK}}$ | $D_{\mathrm{LP}} > D_{\mathrm{KK}}$ | mediana $D_{\mathrm{KK}}$ | mediana $D_{\mathrm{LP}}$ | mediana $q$ |
| ------ | ----------- | ----------- | ----------- | ----------- | --------- | --------- | -------- |
| 100 | (0; 0,6] | 0 | 0 | 57 | 8 | 1779 | 144,8 |
| 100 | (0,6; 1] | 0 | 0 | 20 | 20 | 366 | 18,1 |
| 100 | (1; 2] | 4 | 18 | 37 | 1 | 8 | 2,2 |
| 100 | (2; 3] | 1 | 42 | 8 | 1 | 1 | 1,0 |
| 100 | (3; 4,26] | 4 | 82 | 6 | 824 | 1110 | 1,0 |
| 100 | > 4,26 | 0 | 48 | 3 | 219305 | 219305 | 1,0 |
| 1000 | (0; 0,6] | 2 | 0 | 54 | 1 | 1108 | 503,2 |
| 1000 | (0,6; 1] | 0 | 0 | 18 | 1 | 124 | 79,0 |
| 1000 | (1; 2] | 0 | 44 | 11 | 1 | 1 | 1,0 |
| 1000 | (2; 3] | 0 | 52 | 0 | 1 | 1 | 1,0 |
| 1000 | (3; 4,26] | 0 | 69 | 0 | 1 | 1 | 1,0 |
| 1000 | > 4,26 | 0 | 80 | 0 | 1 | 1 | 1,0 |

Rozkład jednostajny:

| $n$ | CV | $D_{\mathrm{LP}} < D_{\mathrm{KK}}$ | $D_{\mathrm{LP}} = D_{\mathrm{KK}}$ | $D_{\mathrm{LP}} > D_{\mathrm{KK}}$ | mediana $D_{\mathrm{KK}}$ | mediana $D_{\mathrm{LP}}$ | mediana $q$ |
| ------ | ----------- | ----------- | ----------- | ----------- | --------- | --------- | -------- |
| 100 | (0; 0,6] | 1 | 0 | 49 | 12 | 541 | 13,8 |
| 1000 | (0; 0,6] | 2 | 0 | 48 | 1 | 200 | 15,8 |

Łącznie LP+GNP dało mniejszą rozpiętość niż KK na 19 zbiorach, równą na 479 i większą na 922. Mediana $q$ wyniosła $6{,}0$.

- Przy małym CV LP+GNP daje większą rozpiętość niż KK na prawie wszystkich zbiorach, a mediana $q$ sięga od kilkunastu do ponad tysiąca. Przewaga KK maleje wraz ze wzrostem CV.
- Równe rozpiętości występują w dwóch sytuacjach. Przy $n = 1000$ dla rozkładu gamma oba podejścia osiągają $D = 1$. Przy bardzo dużym CV i $n = 100$ oba dają tę samą, bardzo dużą rozpiętość (mediany rzędu $10^4$–$10^5$), porównywalną ze średnią sumą podzbioru $\Sigma/k \approx 2$–$3{,}3 \cdot 10^5$. Wskazuje to, że rozpiętość wyznacza wtedy jedna lub kilka dominujących liczb, których żaden podział nie zrównoważy.
- Dla rozkładu log-normalnego przy $n = 1000$ LP+GNP nie dało mniejszej rozpiętości niż KK na żadnym zbiorze, a KK osiągał medianę $D = 1$ w każdym przedziale CV.

### 4.4. Wpływ $k$
| Dane | $D_{\mathrm{LP}} < D_{\mathrm{KK}}$ | $D_{\mathrm{LP}} = D_{\mathrm{KK}}$ | $D_{\mathrm{LP}} > D_{\mathrm{KK}}$ | mediana $q$ |
| ------------------ | ------------ | ------------ | ------------ | -------- |
| lognormal, $k = 3$ | 0 | 16 | 314 | 24,5 |
| lognormal, $k = 5$ | 5 | 28 | 297 | 11,7 |
| gamma, $k = 3$ | 3 | 226 | 101 | 1,0 |
| gamma, $k = 5$ | 8 | 209 | 113 | 1,0 |
| uniform, $k = 3$ | 3 | 0 | 47 | 34,0 |
| uniform, $k = 5$ | 0 | 0 | 50 | 13,9 |

Dla $k = 5$ przewaga KK jest mniejsza niż dla $k = 3$ (dla rozkładu log-normalnego mediana $q$ spada z $24{,}5$ do $11{,}7$), ale wnioski pozostają te same.

### 4.5. Czas działania
| Dane | KK, mediana [ms] | KK, p95 [ms] | LP+GNP, mediana [ms] | LP+GNP, p95 [ms] | LP przerwane limitem czasu |
| -------------------- | -------- | -------- | -------- | -------- | ---------- |
| $n = 100$, $k = 3$ | 0,30 | 0,44 | 60,69 | 1005,83 | 46 z 355 |
| $n = 100$, $k = 5$ | 0,39 | 0,62 | 192,43 | 1010,92 | 107 z 355 |
| $n = 1000$, $k = 3$ | 3,53 | 5,76 | 1016,64 | 1043,17 | 339 z 355 |
| $n = 1000$, $k = 5$ | 4,64 | 14,21 | 1026,94 | 1075,69 | 350 z 355 |

LP+GNP działa o dwa–trzy rzędy wielkości dłużej niż KK. Przy $n = 1000$ do LP trafia średnio od około 20 do ponad 200 liczb i solver prawie zawsze kończy pracę po upływie limitu czasu, bez dowodu optymalności. Na 14 zbiorach rozwiązanie początkowe dla dużych liczb (lepszy z podziałów KK i GNP) miało rozpiętość $0$, więc LP nie było uruchamiane (status `HeuristicOptimal`). Na żadnym zbiorze orkiestrator nie przeszedł awaryjnie do KK.

### 4.6. Zbiory, na których LP+GNP daje mniejszą rozpiętość
Największą przewagę LP+GNP uzyskało na dwóch zbiorach z rozkładu gamma przy $n = 100$ i CV $3{,}56$ oraz $3{,}04$: KK dał $D = 479$ i $D = 457$, a LP+GNP $D = 1$. Pozostałe przypadki przewagi są mniejsze. Pięć z 19 takich zbiorów ma CV $\le 0{,}6$, więc orkiestrator i tak wybiera na nich KK.

## 5. Podsumowanie
- Algorytm KK jest bardzo silnym punktem odniesienia: LP+GNP dało mniejszą rozpiętość tylko na 19 z 1420 zbiorów. Przy małym i średnim CV rozpiętość LP+GNP jest wyraźnie większa, a przy dużym CV oba podejścia dają najczęściej ten sam wynik.
- Próg $0{,}6$ przełącza orkiestrator zbyt często: na 42% zbiorów daje on większą rozpiętość niż KK.
- Przy progu $4{,}26$ orkiestrator zachowuje jakość KK na 98% zbiorów; większą rozpiętość daje na 28 zbiorach, głównie z rozkładu log-normalnego przy $n = 1000$.
- Wybór LP+GNP wydłuża czas działania do około 1 s przy $n = 1000$, wobec kilku milisekund dla KK.
