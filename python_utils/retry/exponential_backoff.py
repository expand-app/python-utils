import random


def calculate_exponential_backoff(
        base_delay, attempt, backoff_factor=2, max_delay=None, jitter=True):
    """
    Calculate the delay for exponential backoff.

    :param base_delay: Initial delay in seconds.
    :param attempt: Current retry attempt (1-based index).
    :param backoff_factor: Multiplicative factor for exponential growth.
    :param max_delay: Maximum delay in seconds (optional).
    :param jitter: Whether to add random jitter to the delay.
    :return: Calculated delay in seconds.
    """
    # Exponential delay calculation
    delay = base_delay * (backoff_factor ** (attempt - 1))

    # Cap delay at max_delay if specified
    if max_delay is not None:
        delay = min(delay, max_delay)

    # Add jitter if enabled
    if jitter:
        delay = random.uniform(0, delay)

    return delay
