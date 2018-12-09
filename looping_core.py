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
    def wrapper(args = [], kwargs = {}):
        # there may be a better way to do this with custom exceptions
        argspec = getargspec_fn(fn)

        if argspec.args == []:
            return fn()
        else:
            return fn(*args)

    return wrapper

class EnvironmentException(Exception):
    pass

class Environment(object):
    def __init__(self, option_list):
        self.option_list = option_list

    def __getitem__(self, key):
        item = None
        for option in self.option_list:
            try:
                item = option[key]
                return item

            except OptionException:
                pass

        raise EnvironmentException("Key '{}' not found in environment".format(key))

    def __contains__(self, val):
        for option in self.option_list:
            try:
                self.__getitem__(val)
                return True
            except EnvironmentException:
                return False

class OptionException(Exception):
    pass

class Option(object):
    """
    This class defines the name of an option, the function it relates to, and the trigger that
    calls it.

    When you create a new option, you should add it to the option_list.

    Trigger can either be a type like int, a single input like 'A', or a list of inputs like
    ["a", "A"]
    """
    def __init__(self, name, fn, trigger, input_modifier = None):
        self.name = name
        self.fn = fn
        self.trigger = trigger
        self.input_modifier = input_modifier

    def __getitem__(self, val):
        try:
            if val in self.trigger:
                return self.fn
            elif type(val) in self.trigger:
                return self.fn

        except TypeError:
            if val == self.trigger:
                return self.fn
            elif type(val) == self.trigger:
                return self.fn

        raise OptionException("'{}' has no function in triggers: '{}'".format(val, self.trigger))

    def __eq__(self, val):
        if self.input_modifier is not None:
            val = self.input_modifier(val)

        try:
            # if self.__getitem__ does not raise an error then the two are equivalent
            self.__getitem__(val)
            return True

        except OptionException:
            return False

def selection_confirmed(selection):
    def make_lowercase(string):
        try:
            return string.lower()
        except Exception:
            pass

    option_list = [ Option("Yes", lambda x: True, ['y', ''], input_modifier = make_lowercase),
                    Option("No", lambda x: False, 'n', input_modifier = make_lowercase)]

    return loop(option_list = option_list, loop_name = "Is '{}' ok?".format(selection),
        break_val = None, require_return = False, confirm = False, default_value = True,
        allow_nothing = True)

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

        if token in environment:
            tokens.append(token)
        else:
            print("'{}' not in environment".format(token))
            tokens = None
            break

    if tokens is not None:
        return run_command(tokens, environment)

def build_env(option_list, instr_string = None):
    environment = Environment(option_list)

    if instr_string is None:
        instr_string = ""

    for option in option_list:
        name = option.name
        function_name = option.fn
        triggers = option.trigger
        option_string = "{}: {}".format(triggers, name)
        instr_string += '\n' + option_string

    return environment, instr_string

def loop(option_list = [], loop_name = "Default Loop", instr_string = None, break_val = 'q', break_text = 'Quit', require_return = True, confirm = False, default_value = (False, None), allow_nothing = False):

    environment, per_loop_text = build_env(option_list, instr_string)

    if break_val is not None:
        per_loop_text += '\n{}: {} {}'.format(break_val, break_text, loop_name)

    ret_val = None
    while True:

        while True:
            if per_loop_text is not None: print(per_loop_text)

            resp = input_fn("\n> ")
            if resp.strip() != '' or allow_nothing is True:
                if resp.lower() == break_val or break_val is None:
                    if ret_val is not None or require_return is False:
                        if default_value[0] is True:
                            ret_val = default_value[1]

                        break
                    else:
                        print("\nSelection required\n")

                else:
                    ret_val = handle_resp(resp, environment)

            else:
                print("\nInput required\n")

        if confirm is not True or selection_confirmed(ret_val) is True:
            break
        else:
            continue

    return ret_val


# end core loop logic

# example functions called by the loop
def main():
    @loop_fn
    def example_fn(args):
        print("SUCCESS")
        return args

    # define recursive loop
    @loop_fn
    def another_loop():
        option_list = [
            Option("Input a number to call a function and print that number", example_fn, int),
        ]
        ret_val = loop(option_list = option_list, loop_name = "Deeper Loop")
        print("In the Deeper Loop, the example_fn returned: {}".format(ret_val))

    # end functions called by the loop

    option_list = [
        Option("Go a loop deeper", another_loop, 1),
    ]

    # run the main loop
    loop(option_list = option_list, loop_name = "Top Loop")


if __name__ == '__main__':
    main()
