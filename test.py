def test_print(func):
    def tes(*args, **kwargs):
        print("输入2",*args, **kwargs)
        print(1)
        return func(*args, **kwargs)
    return tes


class aa:
    @test_print
    def test(self):
        print(2)

a = aa()
a.test()