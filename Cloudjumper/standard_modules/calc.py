#!/usr/bin/env python3
import math
import multiprocessing
import operator

private_message = False
name_needed = True
EXPRESSIONS = {
    "%": (operator.mod, 2),
    "*": (operator.mul, 2),
    "**": (pow, 2),
    "+": (operator.add, 2),
    "-": (operator.sub, 2),
    "/": (operator.truediv, 2),
    "factorial": (math.factorial, 1),
    "log": (math.log, 2),
    "sqrt": (math.sqrt, 1),
    "xor": (operator.xor, 2),
    "and": (operator.and_, 2),
    "or": (operator.or_, 2),
    "not": (operator.not_, 1),
}
# Should these be in the config?
ALIASES = {
    "*": "xX✕",
    "**": "^",
    "-": "−—–—‒",
    "/": "∕÷",
    "factorial": "!",
    "sqrt": "√",
}
for k, v in ALIASES.items():
    for i in set(v):
        EXPRESSIONS[i] = EXPRESSIONS[k]


def reverse_polish(exprs, bot=None):
    """
    Calculates a given iterable of Reverse Polish notation expressions.
    Also known as post-fix.
    Arguments:
        exprs: An iterable containing Reverse Polish expressions.
        bot: A Cloudjumper instance.
    """
    # TODO Implement proper errors
    timeout = getattr(bot, "config", {}).get("calc_timeout", 5)
    stack = []
    reciever, sender = multiprocessing.Pipe(False)
    for expr in exprs:
        if isinstance(expr, str):
            expr = expr.lower()
        try:
            expr = float(expr)
            if expr.is_integer():
                expr = int(expr)
            stack.append(expr)
            if bot is not None:
                bot.cloudjumper_logger.debug("[Adding num '{}' to stack]".format(stack[-1]))
        except (ValueError, TypeError):
            if expr in EXPRESSIONS:
                func, argc = EXPRESSIONS[expr]
                args = [stack.pop(-1) for _ in range(argc)][::-1]
                """
                A Process is used here because they have timing out built in.
                The sender and receiver are just two ends of a pipe, which are used to send-recieve values.
                """
                proc = Process(target=lambda: sender.send(func(*args)))
                proc.start()
                proc.join(timeout)
                if proc.is_alive():
                    raise TimeoutError("Calculation is taking too long!")
                res = reciever.recv()
                if bot is not None:
                    bot.cloudjumper_logger.debug("[Called Function '{}'({}) With Args {}, Result: {}]".format(func.__name__,
                                                                                                          expr,
                                                                                                          ", ".join(map(str, args)),
                                                                                                          res))
                stack.append(res)
            else:
                raise RuntimeError("Unknown expression!")
    if len(stack) != 1:
        raise RuntimeError("Invalid number of operations!")
    stack_res = stack[0]
    if getattr(stack_res, "is_integer", lambda: False)():
        stack_res = int(stack_res)
    return round(stack_res, 3)


def message_handler(bot, message, sender):
    args = message.split(" ", 1+int(name_needed))
    if bot.is_command("calc", message, name_needed):
        if len(args) > 1 + int(name_needed):
            to_calc = args[1 + int(name_needed)].split(" ")
            try:
                res = reverse_polish(to_calc, bot) 
            except Exception as e:
                # TODO Implement proper messages.
                bot.cloudjumper_logger.debug("[Failed Calculating With {0.__class__.__name__} '{0!s}']".format(e))
                bot.send_action(bot.get_message("calc_error").format(e))
            else:
                bot.send_action(bot.get_message("calc_result").format(res))
        else:
            bot.send_action(bot.get_message("command_error"))
        return True


