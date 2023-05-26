
from Astree import Program,Stmt,Expr,Token
from TMCFM import tokenize,TokenType

class Parser:
    def __init__(self) -> None:
        ...

    def parse(self,code:str) -> Program:
        self.tokens = tokenize(code)
        return self.parser_program()
    def parser_program(self) -> Program:
        '''
        Program -> Stmt*
        '''
        program = Program()
        while self.tk() != TokenType.EOF:
            program.body.push(self.parse_stmt())
        
        return program
    def tk(self)->Token:
        return self.tokens[0]
    def parse_stmt(self) -> Stmt:
        '''
            Stmt -> Expr
        '''
        return self.parse_expr()
    def parse_expr(self) -> Expr:
        '''
            Expr -> AdditiveExpr
        '''
        return self.parse_additive_expr()
    def parse_additive_expr(self) -> Expr:
        '''
            AdditiveExpr -> Mul
        '''
        letf = self.parse_mul_expr()
        while self.tk().value == '+' or self.tk().value == '-':
            self.eat()
    def eat(self):
        ...
    def parse_mul_expr(self):
        ...