# Algorytm Karmarkara–Karpa

## 1. Ogólny opis
Algorytm Karmarkara–Karpa jest algorytmem aproksymacyjnym dla problemu podziału liczb. Dany jest zbiór liczb naturalnych $S = \{a_1, \dots, a_n\}$ oraz liczba $k \ge 1$. Szukamy podziału $S$ na $k$ podzbiorów, których sumy są możliwie zbliżone.

Problem ten jest NP-trudny, więc nie znamy algorytmu wielomianowego, który zawsze daje rozwiązanie optymalne. Algorytm Karmarkara–Karpa działa w czasie wielomianowym i zwraca rozwiązanie, które może być nieoptymalne. Jego błąd jest jednak ograniczony z góry, co wykażemy w sekcji 4.

Zespół wybrał ogólny wariant problemu, czyli podział na $k$ podzbiorów. Dlatego algorytm omawiamy dla dowolnego naturalnego $k$.

## 2. Pojęcia i kroki algorytmu
### 2.1. Pojęcia
- **Grupa** – lista liczb ze zbioru $S$. Grupy będą kandydatami na docelowe podzbiory.
- **Wartość grupy** $w(G)$ – suma liczb w grupie $G$ (dla grupy pustej $w(G) = 0$).
- **Wiersz** – $k$-elementowa krotka grup $R = (G_1, \dots, G_k)$.
- **Rozpiętość wiersza** – różnica między największą i najmniejszą wartością grupy w wierszu:
  $$\mathrm{rozp}(R) = \max_i w(G_i) - \min_i w(G_i).$$
- **Sortowanie wiersza** – ustawienie grup w kolejności rosnących wartości.
  Wszystkie wiersze utrzymujemy posortowane.
- **Odwrócenie wiersza** – odwrócenie kolejności grup w wierszu.

### 2.2. Kroki algorytmu
**Inicjalizacja.**
Dla każdej liczby $a_i \in S$ tworzymy wiersz
$$\big(\,[\,],\ \dots,\ [\,],\ [a_i]\,\big),$$
czyli $k-1$ pustych grup i jedną grupę zawierającą $a_i$. Taki wiersz jest posortowany,
a jego rozpiętość wynosi $a_i$. Otrzymujemy $n$ wierszy.

**Pętla główna.** Dopóki jest więcej niż jeden wiersz:
1. Wybierz dwa wiersze o największych rozpiętościach. Wiersz o mniejszej rozpiętości
   oznacz jako B, a drugi jako A (przy równych rozpiętościach wybór jest dowolny).
2. Odwróć wiersz B. Teraz jego grupy są ustawione malejąco według wartości.
3. Dołącz B do A pozycyjnie: wszystkie liczby z $i$-tej grupy B dopisz do $i$-tej
   grupy A ($i = 1, \dots, k$). W efekcie:
   - najmniejsza grupa A łączy się z największą grupą B,
   - druga najmniejsza grupa A łączy się z drugą największą grupą B,
   - i tak dalej.
4. Posortuj wiersz A, bo wartości jego grup mogły się zmienić.
5. Usuń pusty już wiersz B.

**Wynik.**
Po zakończeniu pętli zostaje jeden wiersz z $k$ grupami. Każda grupa jest jednym z docelowych podzbiorów. To, że jest to poprawny podział, wykazujemy w sekcji 3.

### 2.3. Przykład
$S = \{8, 7, 6, 5, 4\}$, $k = 2$. Rozpiętość wiersza podajemy w nawiasie.

| Krok | Wiersze |
|---|---|
| start | $([\,],[8])_{(8)},\ ([\,],[7])_{(7)},\ ([\,],[6])_{(6)},\ ([\,],[5])_{(5)},\ ([\,],[4])_{(4)}$ |
| 1 | $([7],[8])_{(1)},\ ([\,],[6])_{(6)},\ ([\,],[5])_{(5)},\ ([\,],[4])_{(4)}$ |
| 2 | $([5],[6])_{(1)},\ ([7],[8])_{(1)},\ ([\,],[4])_{(4)}$ |
| 3 | $([4,7],[8])_{(3)},\ ([5],[6])_{(1)}$ |
| 4 | $([8,6],[4,7,5])_{(2)}$ |

Wynik to sumy $14$ i $16$. Optymalny podział $\{8,7\}, \{6,5,4\}$ ma sumy równe $15$,
więc algorytm nie zawsze znajduje optimum.

## 3. Dowód poprawności

Algorytm jest aproksymacyjny, więc nie dowodzimy optymalności wyniku. Dowód poprawności
składa się z trzech części:
1. algorytm się zatrzymuje (sekcja 3.1),
2. zwraca poprawny podział zbioru $S$ na $k$ podzbiorów (sekcja 3.2),
3. wynik jest gorszy od optimum co najwyżej o ograniczoną wartość (sekcja 4).

### 3.1. Własność stopu

Każda iteracja pętli usuwa dokładnie jeden wiersz (B). Na początku jest $n$ wierszy,
więc pętla wykona się dokładnie $n - 1$ razy. Algorytm zawsze się zatrzymuje.

### 3.2. Poprawność wyniku

**Niezmiennik.** Przed każdą iteracją każda liczba z $S$ należy do dokładnie jednej
grupy dokładnie jednego wiersza.

- *Inicjalizacja:* każda liczba $a_i$ znajduje się tylko w jednej grupie swojego wiersza.
  Niezmiennik zachodzi.
- *Zachowanie:* w iteracji liczby z grup wiersza B są przenoszone do grup wiersza A,
  a B jest usuwany. Żadna liczba nie zostaje zgubiona ani zduplikowana, a pozostałe
  wiersze się nie zmieniają. Niezmiennik jest zachowany.

**Zakończenie.** Zostaje jeden wiersz - z niezmiennika wynika, że jego $k$ grup jest parami rozłącznych, a ich suma daje $S$. Jest to więc poprawny podział $S$ na $k$ podzbiorów. Gdy $n < k$, część podzbiorów jest pusta, co jest dopuszczalne.

## 4. Jakość rozwiązania

### 4.1. Lemat: rozpiętość nie rośnie
Rozważmy jedno złączenie wierszy A i B (kroki 2–3 pętli). Oznaczmy wartości grup:
- w wierszu A: $x_1 \le x_2 \le \dots \le x_k$,
- w wierszu B przed odwróceniem: $y_1 \le y_2 \le \dots \le y_k$.

Po złączeniu $i$-ta grupa ma wartość
$$z_i = x_i + y_{k+1-i}.$$

**Lemat.**
$$\mathrm{rozp}(A \oplus B) \le \max\big(\mathrm{rozp}(A),\ \mathrm{rozp}(B)\big).$$

*Dowód.* Weźmy dowolne $i < j$. Wtedy
$$z_j - z_i = \underbrace{(x_j - x_i)}_{p\ \in\ [0,\ \mathrm{rozp}(A)]} \;-\; \underbrace{(y_{k+1-i} - y_{k+1-j})}_{q\ \in\ [0,\ \mathrm{rozp}(B)]}.$$
Obie liczby $p$ i $q$ są nieujemne, więc
$$|p - q| \le \max(p, q) \le \max\big(\mathrm{rozp}(A), \mathrm{rozp}(B)\big).$$
Nierówność zachodzi dla każdej pary grup, a więc także dla pary z największą
i najmniejszą wartością. Oznaczenia A oraz B bezstratne w ogólności.

### 4.2. Wniosek: ograniczenie rozpiętości wyniku
Wprowadźmy oznaczenia:
- $a_{\max} = \max_i a_i$ – największa liczba w $S$,
- $M$ – największa wartość grupy w wyniku algorytmu,
- $m$ – najmniejsza wartość grupy w wyniku algorytmu.

Każdy wiersz początkowy ma rozpiętość $a_i \le a_{\max}$. Z lematu wynika, że żadne
złączenie nie tworzy wiersza o rozpiętości większej niż rozpiętości wierszy łączonych.
Przez indukcję po iteracjach każdy wiersz w trakcie działania algorytmu ma rozpiętość
co najwyżej $a_{\max}$. W szczególności dotyczy to wiersza końcowego:
$$M - m \le a_{\max}.$$

### 4.3. Twierdzenie: gwarancja jakości
Wprowadźmy jeszcze:
- $\Sigma = \sum_{i=1}^{n} a_i$ – suma wszystkich liczb,
- $OPT$ – wartość optymalnego rozwiązania. Dla danego podziału $S$ na $k$ grup patrzymy na grupę o największej sumie; $OPT$ to najmniejsza taka suma, jaką można uzyskać spośród wszystkich możliwych podziałów:
  $$OPT = \min_{(P_1,\dots,P_k)} \ \max_{i} \ \sum_{a \in P_i} a.$$

**Twierdzenie.**
$$M \le \frac{\Sigma}{k} + \frac{k-1}{k}\, a_{\max}.$$

*Dowód.* Z sekcji 4.2 każda z $k$ grup wyniku ma wartość co najmniej $M - a_{\max}$.
Jedna grupa ma wartość $M$, a pozostałe $k-1$ grup co najmniej $M - a_{\max}$, więc
$$\Sigma \ge M + (k-1)(M - a_{\max}) = kM - (k-1)\,a_{\max}.$$
Po podzieleniu przez $k$ i przekształceniu otrzymujemy tezę.

Dla optimum zachodzą dwa proste oszacowania:
- $OPT \ge \Sigma / k$, bo największy podzbiór ma sumę nie mniejszą od średniej,
- $OPT \ge a_{\max}$, bo największa liczba musi trafić do któregoś podzbioru.

Podstawiając je do twierdzenia, otrzymujemy:
- **błąd bezwzględny:**
  $$M - OPT \le \frac{k-1}{k}\, a_{\max},$$
- **błąd względny:**
  $$M \le \left(2 - \frac{1}{k}\right) OPT.$$

### 4.4. Wyniki z literatury
Oszacowanie z sekcji 4.3 jest zgrubne. W literaturze udowodniono dokładniejsze
(przytaczamy je bez dowodu):
- dla $k = 2$: $M \le \frac{7}{6}\, OPT$ (Fischetti, Martello, 1987),
- dla dowolnego $k$: $M \le \left(\frac{4}{3} - \frac{1}{3k}\right) OPT$. Istnieją
  instancje, dla których $M / OPT \ge \frac{4}{3} - \frac{1}{3(k-1)}$
  (Michiels, Korst, Aarts, 2003).

## 5. Złożoność obliczeniowa
### 5.1. Założenia implementacyjne
- Wiersze trzymamy w kopcu uporządkowanym malejąco według rozpiętości. Moduł `heapq` realizuje kopiec typu min, więc porównanie jest odwrócone tj. na szczycie kopca znajduje się wiersz o największej rozpiętości.
  Wybór dwóch wierszy o największych rozpiętościach to dwa wywołania operacji `heappop`.
- Wartość $w(G)$ każdej grupy przechowujemy jako liczbę aktualizowaną przy złączeniu, zamiast liczyć za każdym razem sumę listy. Dzięki temu rozpiętość wiersza liczymy w czasie $O(1)$.
- Przy złączeniu liczby z każdej grupy wiersza B są kopiowane na koniec listy odpowiadającej grupy wiersza A.

### 5.2. Analiza
Oznaczmy przez $L$ łączną liczbę liczb skopiowanych przez `extend` w trakcie
całego działania algorytmu.

| Etap | Koszt |
|---|---|
| Utworzenie $n$ wierszy po $k$ grup | $O(nk)$ |
| Budowa kopca ($n$ wywołań `heappush`) | $O(n \log n)$ |
| Jedna iteracja bez kopiowania list: 2× `heappop`, odwrócenie B, złączenie $k$ sum, sortowanie wiersza, `heappush` | $O(\log n + k \log k)$ |
| Liczba iteracji (sekcja 3.1) | $n - 1$ |
| Kopiowanie liczb między listami, łącznie | $O(L)$ |

Daje to złożoność czasową
$$O\big(nk + n(\log n + k \log k) + L\big).$$

### 5.3. Oszacowanie kosztu kopiowania list
W jednej iteracji `extend` kopiuje wszystkie liczby znajdujące się w wierszu B. Wiersz nie może zawierać więcej niż $n$ liczb, a iteracji jest $n - 1$, więc
$$L \le n(n-1) = O(n^2).$$

Jedna liczba może być kopiowana wielokrotnie, ponieważ dzieje się to w każdej iteracji, w której jej wiersz zostaje wybrany jako B.

### 5.4. Podsumowanie

**Złożoność czasowa (pesymistyczna):**
$$O\big(n^2 + nk \log k\big).$$
Dla $k = 2$ daje to $O(n^2)$.

Jest to ograniczenie górne. Dla typowych danych wiersz B zawiera zwykle niewiele liczb i rzeczywisty koszt kopiowania jest znacznie mniejszy. Bez kopiowania list złożoność wynosiłaby
$O\big(nk + n(\log n + k \log k)\big)$.

**Złożoność pamięciowa:** $O(nk)$. Każdy z $n$ wierszy przechowuje $k$ obiektów, a każda liczba w danej chwili znajduje się tylko w jednej liście.

## Bibliografia
1. N. Karmarkar, R. M. Karp, *The differencing method of set partitioning*, Technical Report UCB/CSD 82/113, Computer Science Division, University of California, Berkeley, 1982.
2. M. Fischetti, S. Martello, *Worst-case analysis of the differencing method for the partition problem*, Mathematical Programming 37(1), 1987, s. 117–120, doi:10.1007/BF02591687.
3. W. Michiels, J. Korst, E. Aarts, J. van Leeuwen, *Performance ratios of the Karmarkar–Karp differencing method*, Journal of Combinatorial Optimization 13(1), 2007, s. 19–32, doi:10.1007/s10878-006-9010-z.
4. *Largest differencing method*, Wikipedia, https://en.wikipedia.org/wiki/Largest_differencing_method.