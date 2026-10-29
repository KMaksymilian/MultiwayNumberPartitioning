import math
from abc import ABC, abstractmethod


class Distribution(ABC):
    """Interface of a distribution usable by the dataset generator."""
    name: str

    @abstractmethod
    def sample(self, rng, **params):
        """Draw one real value using the random generator `rng`."""

    @abstractmethod
    def params_for_cv(self, cv, mean):
        """Return a dict of parameters giving the requested CV and mean."""

    @abstractmethod
    def theoretical_cv(self, **params):
        """Return the CV of the distribution for the given parameters."""


class Lognormal(Distribution):
    """Represents lognormal distribution = e^X, X ~ N(mu, sigma^2)."""

    name = "lognormal"

    def sample(self, rng, mu, sigma):
        return rng.lognormvariate(mu, sigma)

    def params_for_cv(self, cv, mean):
        sigma = math.sqrt(math.log(1 + cv ** 2))
        return {"mu": math.log(mean) - sigma ** 2 / 2, "sigma": sigma}

    def theoretical_cv(self, mu, sigma):
        return math.sqrt(math.exp(sigma ** 2) - 1)


DISTRIBUTIONS = {
    dist.name: dist
    for dist in [Lognormal()]
}


def get_distribution(name):
    """Return a distribution by name."""
    try:
        return DISTRIBUTIONS[name]
    except KeyError:
        raise ValueError(
            f"Unknown distribution: {name}. Available: {sorted(DISTRIBUTIONS)}"
        ) from None
