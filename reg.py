def repeat(num_times,n):
    print(f"aaaaaaaaa{num_times}")
    def decortor(func):
        def test(ss):
            print("ccccccccc")
            def wrappr(*args, **kwargs):
                print("dddddd")
                for _ in range(num_times):
                    func(*args, **kwargs)
            return wrappr
        return test
    print("eeeeeeeeeee")
    return decortor

@repeat(3,9)
def say_hello():
    print("Hello!")

#say_hello()