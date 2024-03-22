import re
from typing import TypedDict


class OperationDict(TypedDict):
    AND: str
    OR: str
    NOT: str
    LEFT_PARENTHESIS: str
    RIGHT_PARENTHESIS: str


OPERATION_DICT: OperationDict = {
    # Must use raw string, otherwise the following "re.findall(pattern, query)" will throw future warnings as it contains string like "&&"
    # Reference: https://github.com/PyCQA/pycodestyle/issues/728#issuecomment-414099172
    'AND': r'\&\&',
    'OR': r'\|\|',
    'NOT': r'\!\!',
    'LEFT_PARENTHESIS': r'\(\(',
    'RIGHT_PARENTHESIS': r'\)\)',
}

QUOTE_STRING = '""'

# Set of operations that are not valid for direct evaluation in the recursive function
INVALID_EVAL_OPERATION_SET = set(
    [item.replace('\\', '') for item in [OPERATION_DICT['AND'], OPERATION_DICT['OR'], OPERATION_DICT['RIGHT_PARENTHESIS']]])


class LogQuerier:
    def __init__(self, logs: list[str], raw_operation_dict: OperationDict = OPERATION_DICT, quote_string=QUOTE_STRING):
        """
        Initialize the LogQuerier class with logs and an operation dictionary.

        :param logs: List of log entries as strings.
        :type logs: list[str]
        :param raw_operation_dict: Dictionary of operation symbols, defaults to OPERATION_DICT.
        :type raw_operation_dict: OperationDict, optional
        """

        # Store the provided logs.
        self.logs = logs

        # Prepare the operation dictionary by removing escape characters for regex processing.
        self.operationo_dict: OperationDict = {
            key: value.replace('\\', '') for key, value in raw_operation_dict.items()}

        # Compile a regex pattern to find the operations in the query string.
        all_ops: str = '|'.join(list(raw_operation_dict.values()))
        self.pattern = rf'{all_ops}'

        self.quote_string = quote_string

    def _tokenize(self, query: str):
        """
        Tokenize the given query string.

        :param query: Query string to tokenize.
        :type query: str

        :return: List of tokens obtained from the query string.
        :rtype: list[str]
        """

        # TODO: Add query string validation

        # Find all matches for either pre-defined operator strings or any other strings
        # E.g. query "a && b || c" will gives tokens "['a ', '&&', ' b ', '&&', ' c']"
        tokens = []
        current_query = query
        operations = re.findall(self.pattern, query)

        for operation in operations:
            sub_strings = current_query.split(operation)

            # If there is a non-empty string before the operation, add it to the tokens
            if sub_strings[0]:
                tokens.append(sub_strings[0])

            # Add the current operation to the tokens
            tokens.append(operation)

            # The current query will be the rest of the string
            current_query = operation.join(sub_strings[1:])

        # Append the last part of the query string after the last operation
        if current_query:
            tokens.append(current_query)

        def parse_quoted_token(token: str):
            return token.strip().replace(self.quote_string, '')

        # Return the tokens after stripping whitespace and removing empty tokens.
        return [parse_quoted_token(token) for token in tokens if parse_quoted_token(token)]

    def _evaluate_tokens(self, tokens: list[str], log: str, pos=0, enable_case_insensitive=False):
        """
        Evaluate tokens against a log string recursively.

        :param tokens: List of tokens to evaluate.
        :type tokens: list[str]
        :param log: Log string to evaluate against.
        :type log: str
        :param pos: Current position in the token list, defaults to 0.
        :type pos: int, optional

        :return: Boolean indicating if the log satisfies the query represented by the tokens.
        :rtype: bool
        """

        def eval_next(pos):
            # Evaluates the next token in the list, handling parentheses, negation, and value presence check.

            if pos < len(tokens):
                token: str = tokens[pos]

                # The token is LEFT_PARENTHESIS "((" operator
                if token == self.operationo_dict['LEFT_PARENTHESIS']:
                    # "next_pos" will be the associated right parenthesis
                    # Calling "eval_or()" to handle the full evaluation of the sub-query surrounded by parentheses
                    result, next_pos = eval_or(pos + 1)

                    # Return the result of the sub-query surrounded by parentheses, and skip the right parenthesis
                    return result, next_pos + 1

                # The token is NOT "!!" operator
                elif token == self.operationo_dict['NOT']:
                    # "next_pos" will be the next token to be processed
                    result, next_pos = eval_next(pos + 1)

                    # Return the opposite result
                    return not result, next_pos

                # The token is any other operator
                # This should never happen, but just in case
                elif token in INVALID_EVAL_OPERATION_SET:
                    raise Exception(
                        f"Invalid operation token {token} encountered when evaluating query")

                # The token is non-operator
                else:
                    # Only need to check if the token is in the log, and move to the next token
                    return token.lower() in log.lower() if enable_case_insensitive else token in log, pos + 1

            # This should never happen, but just in case
            return False, pos

        def eval_and(pos):
            # Evaluates a series of AND conditions, handling the logical AND operation.

            # Calling "eval_next()" to evaluate next token as AND operator has higher priority than OR
            result, next_pos = eval_next(pos)

            # Keep processing until the next token is not AND "&&" operator
            while next_pos < len(tokens) and tokens[next_pos] == self.operationo_dict['AND']:
                # Calling "eval_next()" to evaluate next token as AND operator has higher priority than OR
                next_result, next_pos = eval_next(next_pos + 1)

                # Take the intersaction of results as the operator is AND
                result = result and next_result

            return result, next_pos

        def eval_or(pos):
            # Evaluates a series of OR conditions, handling the logical OR operation.

            # Calling "eval_and()" to evaluate AND operation as OR operator has lower priority than AND
            result, next_pos = eval_and(pos)

            # Keep processing until the next token is not OR "||" operator
            while next_pos < len(tokens) and tokens[next_pos] == self.operationo_dict['OR']:
                # Calling "eval_and()" to evaluate AND operation as OR operator has lower priority than AND
                next_result, next_pos = eval_and(next_pos + 1)

                # Take the union of results as the operator is OR
                result = result or next_result

            return result, next_pos

        # Calling "eval_or()" to handle the full evaluation as OR operator has lower priority than AND
        return eval_or(pos)[0]

    def query(self, query='', limit=None, ordering='asc', enable_case_insensitive=False):
        """
        Query the logs based on the provided query string.

        :param query: Query string to use for filtering logs, defaults to an empty string.
        :type query: str, optional
        :param limit: Maximum number of logs to return, optional.
        :type limit: int, optional
        :param ordering: Sort order, 'asc' for ascending and 'desc' for descending, defaults to 'asc'.
        :type ordering: str, optional

        :return: List of logs that match the query.
        :rtype: list[str]
        """

        tokens = self._tokenize(query) if query else []

        # Tokenize the query if provided, and filter the logs based on the evaluation of tokens.
        if tokens:
            logs = [
                log for log in self.logs if self._evaluate_tokens(tokens, log, 0, enable_case_insensitive)]
        else:
            logs = self.logs

        # Apply limit to the number of logs if specified.
        if limit:

            if ordering == 'asc':
                # If ascending, take the logs from the tail
                logs = logs[-limit:]
            else:
                # If descending, take the logs from the head, and reverse them
                logs = logs[:limit]
                logs.reverse()

        return logs
