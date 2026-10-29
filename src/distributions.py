import math
from abc import ABC, abstractmethod


class Distribution(ABC):
    """Interface of a distribution usable by the dataset generator."""
    name: str
    max_cv: float = math.inf

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

class Gamma(Distribution):
	"""Represents gamma distribution with shape k and scale theta.

	Warning: for CV > 1 (k < 1) the density goes to infinity at 0, so many
	values fall below 1 and are clipped by discretization
	(from testing.py: ~1.6% for CV = 1.5, ~9% for CV = 2, ~31% for CV = 3 at mean 10 000).
	"""

	name = "gamma"

	def sample(self, rng, k, theta):
		return rng.gammavariate(k, theta)

	def params_for_cv(self, cv, mean):
		k = 1 / cv ** 2
		return {"k": k, "theta": mean / k}

	def theoretical_cv(self, k, theta):
		return 1 / math.sqrt(k)


class Uniform(Distribution):
	"""Represents uniform distribution U(low, high).

	For low >= 0: CV = (high - low) / (sqrt(3) * (low + high)) <= 1 / sqrt(3) ~ 0.577.
	Therefore, it can never exceed the orchestrator threshold of 0.6.
	"""

	name = "uniform"
	max_cv = 1 / math.sqrt(3)

	def sample(self, rng, low, high):
		return rng.uniform(low, high)

	def params_for_cv(self, cv, mean):
		# Symmetric range around the mean: sd = half_width / sqrt(3).
		half_width = math.sqrt(3) * cv * mean
		return {"low": mean - half_width, "high": mean + half_width}

	def theoretical_cv(self, low, high):
		return (high - low) / (math.sqrt(3) * (low + high))


DISTRIBUTIONS = {
	dist.name: dist
	for dist in [Lognormal(), Gamma(), Uniform()]
}


def get_distribution(name):
    """Return a distribution by name."""
    try:
        return DISTRIBUTIONS[name]
    except KeyError:
        raise ValueError(
            f"Unknown distribution: {name}. Available: {sorted(DISTRIBUTIONS)}"
        ) from None
