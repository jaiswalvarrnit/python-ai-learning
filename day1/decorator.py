def greet():
    print("Hello!")

def execute_function(func):
    print("Before execution")

    func()

    print("After execution")

execute_function(greet)

def my_decorator(func):

    def wrapper():
        print("Before execution")

        func()

        print("After execution")

    return wrapper

@my_decorator
def greet():
    print("Hello Varrnit")

greet()