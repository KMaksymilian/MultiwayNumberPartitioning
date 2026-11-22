# Pruning w modelu LP

## 1. Problem i zakres optymalizacji

Dla nieujemnych liczb całkowitych dzielimy elementy na `k` grup. Minimalizujemy
rozstęp ich sum:

\[
D=\max_j S_j-\min_j S_j.
\]
Co nie jest równoznaczne z minimalizacją największej sumy lub maksymalizacją minimalnej.[1]

## 2. Rozwiązanie początkowe i ograniczenie rozstępu

Uruchamiamy KK i GNP na zredukowanym zbiorze, obliczamy rozstęp każdego podziału i wybieramy
mniejszy [3]. Jego wartość `U` jest górną granicą optimum. Do modelu dodajemy:

\[
D\le U.
\]

Podczas branch-and-bound solver może odrzucać węzły, których poprawna dolna
granica celu nie pozwala poprawić najlepszego znanego wyniku.

## 3. Granice sum grup wynikające z rozstępu

Niech `T` oznacza sumę elementów `B`. Dla każdego podziału o rozstępie
nie większym niż `U` dodajemy:

\[
\max\left(0,\left\lceil\frac{T-(k-1)U}{k}\right\rceil\right)
\le S_j\le
\left\lfloor\frac{T+(k-1)U}{k}\right\rfloor.
\]


Niech `s` będzie najmniejszą sumą. Każda inna jest nie większa niż `s+U`, zatem

\[
T\le s+(k-1)(s+U)=ks+(k-1)U.
\]
Analogicznie, dla największej sumy `M`, każda inna suma jest co najmniej równa `M-U`, więc

\[
T\ge M+(k-1)(M-U)=kM-(k-1)U.
\]



## 4. Redukcja symetrii przez porządek sum

Bezpośrednim odniesieniem dla tej metody w problemie multi-way number partitioning
jest praca Michaela D. Moffitta [2],
[sekcja 4.4 „Pruning Symmetric Solutions”, s. 627 (piąta strona PDF)](https://www.ijcai.org/Proceedings/13/Papers/099.pdf#page=5).
Autor opisuje eliminowanie równoważnych numeracji grup przez wymaganie,
aby sumy kolejnych podzbiorów były niemalejące. W jego notacji `S_j` oznacza
podzbiór, więc warunek ma postać:

\[
\sum_{a\in S_j}a\le\sum_{a\in S_{j'}}a
\qquad\text{dla }j<j'.
\]

W naszym modelu symbol `S_j` oznacza już sumę grupy. Przyjmujemy odwrotną,
równoważną konwencję numeracji — porządek nierosnący — i dodajemy `k-1` ograniczeń:

\[
S_0\ge S_1\ge\ldots\ge S_{k-1}.
\]

Grupy nie mają różnych pojemności ani innych indywidualnych własności. Można
więc zmienić ich numerację bez zmiany celu.

## 5. Co gwarantuje obecna implementacja

- Pruning nie jest domyślnie włączany w samodzielnym wywołaniu LP dla całego wejścia.
- Nadal obowiązuje konfigurowalny limit czasu, domyślnie jedna sekunda.
- W najgorszym przypadku pozostaje kombinatoryczna trudność MILP. Pruning nie
  stanowi gwarancji wielomianowego czasu ani przyspieszenia każdej instancji.


## Bibliografia z zakresem powołania

**[1]** Richard E. Korf (2010). *Objective Functions for Multi-Way Number
Partitioning*. Proceedings of the International Symposium on Combinatorial
Search, 1(1), 71–72.
[Strona publikacji i dostęp do PDF](https://ojs.aaai.org/index.php/SOCS/article/view/18172).
DOI: 10.1609/socs.v1i1.18172.
Powołanie: nierównoważność trzech funkcji celu dla co najmniej trzech grup.

**[2]** Michael D. Moffitt (2013). *Search Strategies for Optimal Multi-Way
Number Partitioning*. Proceedings of the Twenty-Third International Joint
Conference on Artificial Intelligence (IJCAI 2013), 623–629.
[Pełny tekst PDF](https://www.ijcai.org/Proceedings/13/Papers/099.pdf) ·
[Sekcja 4.4 „Pruning Symmetric Solutions”, s. 627](https://www.ijcai.org/Proceedings/13/Papers/099.pdf#page=5).

**[3]** Dr Rafał Górak. *Konsultacja osobista*.
Zakres powołania: uzgodnienie pomysłu wprowadzenia rozwiązania początkowego dla modelu LP i wykonania pruningu.
