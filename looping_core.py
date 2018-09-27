import sys

# for python version 2.7 getfullargspec isn't available and input is different
if sys.version_info < (3, 0):
    input_fn = raw_input
    from inspect import getargspec
    getargspec_fn = getargspec

else:
    input_fn = input
    from inspect import getfullargspec
    getargspec_fn = getfullargspec

# core looping logic
def loop_fn(fn):
    """
    Use this decorator on any function used in Option objects in the option_list
    This allows us to try a function with args, and then try again if it fails.
    By default, all functions called by the loop recieve args but not all of
    them accept args
    """
    def wrapper(args):
        # there may be a better way to do this with custom exceptions
        argspec = getargspec_fn(fn)

        if argspec.args == []:
            fn()
        else:
            fn(args)

    return wrapper

class Option(object):
    """
    This class defines the name of an option, the function it relates to, and the
    trigger that calls it.

    When you create a new option, you should add it to the option_list.
    """
    def __init__(self, name, fn, trigger):
        self.name = name
        self.fn = fn
        self.trigger = trigger

def build_env(option_list):
    environment = {}
    instr_string = ""

    for option in option_list:
        name = option.name
        function_name = option.fn
        trigger = option.trigger
        option_string = "{}: {}".format(trigger, name)
        instr_string += '\n' + option_string
        environment[trigger] = function_name

    return environment, instr_string

def quit_loop(args):
    return 'quit_loop'

def run_command(tokens, environment):
    command_id = tokens[0]
    args = tokens

    try:
        # execute the command by identifier command_id in command_list
        return environment[command_id](args)

    except KeyError:
        # the command might be refereced by a type, try that
        return environment[type(command_id)](args)

    except KeyError:
        print("{} not a recognized command".format(command_id))

def handle_resp(resp, environment):
    tokens = []
    for token in resp.strip().split(" "):

        try:
            token = eval(token)
        except NameError:
            pass
        except SyntaxError:
            pass

        if token in environment or type(token) in environment:
            tokens.append(token)
        else:
            print("{} not in environment".format(token))
            tokens = None
            break

    if tokens is not None:
        return run_command(tokens, environment)

def loop(option_list = [], loop_name = "Default Loop"):
    environment, per_loop_text = build_env(option_list)

    # so that there is always a quit option
    default_environment = {'q':quit_loop}
    environment.update(default_environment)
    per_loop_text += '\nq: Quit {}'.format(loop_name)

    while True:
        if per_loop_text is not None: print(per_loop_text)

        resp = input_fn("\n> ")
        if resp.strip() != '':
            ret_val = handle_resp(resp, environment)

            if ret_val == 'quit_loop':
                break

# end core loop logic

# example functions called by the loop
def main():
    @loop_fn
    def example_fn(args):
        print("SUCCESS")
        print(args)

    # define recursive loop
    @loop_fn
    def another_loop():
        option_list = [
            Option("Input a number to call a function and print that number", example_fn, int),
        ]
        loop(option_list = option_list, loop_name = "Deeper Loop")

    # end functions called by the loop

    option_list = [
        Option("Go a loop deeper", another_loop, 1),
    ]

    # run the main loop
    loop(option_list = option_list, loop_name = "Top Loop")


if __name__ == '__main__':
    main()
