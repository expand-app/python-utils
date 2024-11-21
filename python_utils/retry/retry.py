import logging
import time
import random
from functools import wraps

from python_utils.retry.exponential_backoff import calculate_exponential_backoff


def retry(should_retry_on_exception=None, should_retry_on_result=None,
          max_attempts=3, delay_mode="normal",
          delay=1, random_delay_range=None,
          backoff_factor=2, max_backoff_delay=None, jitter=True,
          custom_delay_callback=None,
          verbose=False):
    """
    Retry decorator with customizable delay logic.

    :param should_retry_on_exception: Function to determine if retry is needed based on exception. Must return True to retry.
    :param should_retry_on_result: Function to determine if retry is needed based on result. Must return True to retry.
    :param max_attempts: Number of attempts before giving up.
    :param delay_mode: 'normal', 'exponential', or 'custom' for delay behavior.
    :param delay: Initial delay for exponential backoff.
    :param random_delay_range: Tuple (min, max) for random delay.
    :param backoff_factor: Multiplicative factor for exponential growth.
    :param max_backoff_delay: Maximum delay cap for exponential backoff.
    :param jitter: Whether to add random jitter to the delay.
    :param custom_delay_callback: Function to calculate custom delay. Must accept attempt number and return delay in seconds.
    :param verbose: Whether to log detailed retry information.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0

            while attempts < max_attempts:
                try:
                    attempts += 1
                    result = func(*args, **kwargs)

                    if should_retry_on_result and should_retry_on_result(result):
                        if verbose:
                            logging.info(f"Retrying due to result: {result}")

                        raise ValueError("Retry triggered by result check")

                    if verbose:
                        logging.info(
                            f"Attempt {attempts}/{max_attempts} succeeded with result: {result}")

                    return result
                except Exception as e:
                    if should_retry_on_exception and not should_retry_on_exception(e):
                        if verbose:
                            logging.info(f"Not retrying due to exception: {e}")

                        raise e

                    if attempts < max_attempts:
                        base_delay = random.uniform(
                            *random_delay_range) if random_delay_range else delay

                        if delay_mode == "normal":
                            final_delay = base_delay
                        elif delay_mode == "exponential":
                            final_delay = calculate_exponential_backoff(
                                base_delay=base_delay,
                                attempt=attempts,
                                backoff_factor=backoff_factor,
                                max_delay=max_backoff_delay,
                                jitter=jitter
                            )
                        elif delay_mode == "custom":
                            if custom_delay_callback:
                                final_delay = custom_delay_callback(attempts)
                            else:
                                raise ValueError(
                                    "Custom delay mode requires a custom delay callback")
                        else:
                            raise ValueError(
                                f"Invalid delay mode: {delay_mode}")

                        if verbose:
                            logging.info(
                                f"Attempt {attempts}/{max_attempts} failed with error: {e}. Retrying in {final_delay:.2f} seconds...")

                        time.sleep(final_delay)
                    else:
                        if verbose:
                            logging.info(
                                f"All {attempts}/{max_attempts} attempts failed. Last error: {e}")

                        raise e
        return wrapper
    return decorator
