# Wstęp

## 1. Opis problemu
Przedmiotem projektu jest problem podziału liczb. Dany jest zbiór liczb naturalnych $S = \{a_1, \dots, a_n\}$ oraz liczba $k \ge 1$. Należy podzielić $S$ na $k$ rozłącznych podzbiorów $P_1, \dots, P_k$ których suma daje cały zbiór $S$, w taki sposób, aby sumy liczb w podzbiorach były możliwie zbliżone.

Jako miarę jakości podziału przyjmujemy sumę największego podzbioru, czyli podzbioru o największej sumie liczb (nie o największej liczności). Szukamy podziału, dla którego ta wartość jest najmniejsza:
$$OPT = \min_{(P_1,\dots,P_k)} \ \max_{j} \ \sum_{a \in P_j} a.$$

Problem jest NP-trudny. Oznacza to, że nie jest znany algorytm, który dla każdego wejścia znajduje rozwiązanie optymalne w czasie wielomianowym. Dlatego w projekcie rozważamy dwa podejścia: dokładne, które zawsze znajduje optimum, ale w najgorszym przypadku działa w czasie wykładniczym, oraz aproksymacyjne, które działa w czasie wielomianowym, ale może zwrócić rozwiązanie nieoptymalne o ograniczonym błędzie.