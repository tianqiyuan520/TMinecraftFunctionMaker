from ast import *

Module(body=[
    Assign(targets=[Name(id='x', ctx=Store())], value=Constant(value=3, kind=None), type_comment=None), 
    Assign(targets=[Name(id='a', ctx=Store())], value=Name(id='x', ctx=Load()), type_comment=None), 
    Assign(targets=[Name(id='x', ctx=Store())], value=
    BinOp(
        left=BinOp(
            left=BinOp(
                left=BinOp(
                    left=BinOp(
                        left=Constant(value=1, kind=None), 
                        op=Add(), 
                        right=Constant(value=2, kind=None)), 
                    op=Add(), 
                    right=BinOp(
                        left=Constant(value=3, kind=None), 
                        op=Div(), 
                        right=Constant(value=2, kind=None))
                    ), 
                    op=Sub(),
                    right=Constant(value=55, kind=None)), 
                op=Add(), 
                right=BinOp(left=Constant(value=33, kind=None), 
            op=Mult(), 
            right=Constant(value=3, kind=None))
            ),
        op=Add(),
        right=Name(id='a', ctx=Load())
        ), type_comment=None)], type_ignores=[])


Module(body=[
    Assign(targets=[Name(id='x', ctx=Store())], 
    value=BinOp(
        left=BinOp(
            left=BinOp(
                left=Constant(value=1, kind=None), 
                op=Mult(), 
                right=Constant(value=2, kind=None)), 
            op=Div(), 
            right=Constant(value=3, kind=None)
            ),
        op=Div(),
        right=BinOp(
                left=BinOp(
                    left=BinOp(
                        left=BinOp(
                            left=Constant(value=2, kind=None),
                                op=Sub(),
                                right=Constant(value=55, kind=None)), 
                        op=Add(),
                        right=BinOp(
                            left=Constant(value=33, kind=None),
                            op=Mult(), 
                            right=Constant(value=3, kind=None)
                            )
                        ),
                    op=Sub(),
                    right=Constant(value=2, kind=None)
                    ),
                op=Add(),
                    right=BinOp(
                        left=Constant(value=33, kind=None),
                        op=Div(),
                        right=Constant(value=22, kind=None))
                )
        ), 
        type_comment=None)
    ], type_ignores=[])



Module(
    body=[
        Assign(targets=[Name(id='a', ctx=Store())], value=Constant(value=1, kind=None), type_comment=None), 
        
        If(
            test=BoolOp(
                op=Or(), 
                values=[
                    BoolOp(
                        op=And(), 
                        values=[
                            Compare(
                                left=
                                BinOp(left=Name(id='a', ctx=Load()), op=Add(), right=Constant(value=32, kind=None)), 
                                ops=[Eq()],
                                comparators=[
                                    BinOp(left=Call(func=Name(id='abs', ctx=Load()), args=[Constant(value=33, kind=None)], keywords=[]), op=Add(), right=Constant(value=33, kind=None))
                                    ]), 
                            UnaryOp(
                                op=Not(),
                                operand=Compare(
                                    left=Call(func=Name(id='abs', ctx=Load()), args=[Constant(value=11, kind=None)], keywords=[]), ops=[NotEq()], 
                                    comparators=[Constant(value=3, kind=None)]))]), 

                    BoolOp(
                        op=Or(), 
                        values=[
                            Compare(
                                left=Name(id='a', ctx=Load()), 
                                ops=[Eq()], 
                                comparators=[Constant(value=3, kind=None)]), 
                            Compare(
                                left=Name(id='a', ctx=Load()), 
                                ops=[Eq()], 
                                comparators=[Constant(value=1, kind=None)])])
                    ]), 

            body=[Assign(targets=[Name(id='a', ctx=Store())], value=Constant(value='11', kind=None), type_comment=None)], 
            
            orelse=[
                If(
                    test=BoolOp(
                        op=Or(), 
                        values=[
                            BoolOp(
                                op=And(), 
                                values=[
                                    BoolOp(
                                        op=And(), 
                                        values=[
                                            Compare(left=Name(id='a', ctx=Load()), ops=[GtE()], comparators=[Constant(value=2, kind=None)]), 
                                            Compare(left=Name(id='a', ctx=Load()), ops=[Gt()], comparators=[Constant(value=2, kind=None)]), 
                                            Compare(left=Name(id='a', ctx=Load()), ops=[Lt()], comparators=[Constant(value=2, kind=None)]), 
                                            Compare(left=Name(id='a', ctx=Load()), ops=[LtE()], comparators=[Constant(value=3, kind=None)])
                                            ]
                                    ), 
                                    UnaryOp(
                                        op=Not(), 
                                        operand=
                                        Compare(left=Name(id='a', ctx=Load()), ops=[NotEq()], comparators=[Constant(value=3, kind=None)]))
                                        ]
                                ), 
                            
                            BoolOp(op=Or(), values=[
                                Compare(left=Name(id='a', ctx=Load()), ops=[Eq()], comparators=[Constant(value=3, kind=None)]), Compare(left=Name(id='a', ctx=Load()), ops=[Eq()], comparators=[Constant(value=1, kind=None)])
                                ])
                            ]), 
                    
                    body=[Assign(targets=[Name(id='a', ctx=Store())], value=Constant(value=3, kind=None), type_comment=None)], 
                    
                    orelse=[
                        Assign(targets=[Name(id='a', ctx=Store())], value=Constant(value='ok', kind=None), type_comment=None)])
                ])
        
        
        ], type_ignores=[])



Module(body=[
    For(
        target=Name(id='i', ctx=Store()), 
        iter=Call(
            func=Name(id='range', ctx=Load()), args=[Constant(value=2, kind=None), Constant(value=33, kind=None)], keywords=[]
            ), 
        body=[Assign(targets=[Name(id='a', ctx=Store())], value=Constant(value=1, kind=None), type_comment=None)], orelse=[], type_comment=None)], type_ignores=[])

Module(body=[
    While(
        test=BinOp(
            left=Name(id='a', ctx=Load()), op=Add(), right=Constant(value=3, kind=None)), 
        body=[Assign(targets=[Name(id='a', ctx=Store())], value=Constant(value=1, kind=None), type_comment=None)], orelse=[])], type_ignores=[])

Module(
    body=[
        Assign(targets=[Name(id='a', ctx=Store())], value=Constant(value=2, kind=None), type_comment=None), 
        While(
            test=Name(id='a', ctx=Load()), body=[Expr(value=Call(func=Name(id='print', ctx=Load()), args=[Name(id='x', ctx=Load())], keywords=[]))], orelse=[])], type_ignores=[])
Module(body=[
    For(
        target=Name(id='i', ctx=Store()), 
        iter=Call(func=Name(id='range', ctx=Load()), args=[Constant(value=0, kind=None), Constant(value=10, kind=None), Constant(value=2, kind=None)], keywords=[]), 
        body=[
            Expr(value=Call(func=Name(id='print', ctx=Load()), args=[Name(id='i', ctx=Load())], keywords=[]))], orelse=[], type_comment=None
            )
    
    
    ], type_ignores=[])

Module(body=[
    ImportFrom(module='math', names=[
        alias(name='cos', asname=None)], level=0), 
    For(target=Name(id='i', ctx=Store()), iter=Call(func=Name(id='range', ctx=Load()), args=[Constant(value=0, kind=None), Constant(value=10, kind=None), Constant(value=1, kind=None)], keywords=[]), body=[Expr(value=Call(func=Name(id='cos', ctx=Load()), args=[Name(id='i', ctx=Load())], keywords=[]))], orelse=[], type_comment=None)], type_ignores=[])

Module(body=[
    FunctionDef(name='fn', args=arguments(posonlyargs=[], args=[arg(arg='i', annotation=None, type_comment=None)], vararg=None, kwonlyargs=[], kw_defaults=[],
kwarg=None, defaults=[]), body=[
    If(
        test=Compare(left=Name(id='i', ctx=Load()), ops=[Lt()], comparators=[Constant(value=2, kind=None)]), 
        body=[Return(value=Constant(value=1, kind=None))],
        orelse=[
            Assign(targets=[Name(id='a', ctx=Store())], value=Call(func=Name(id='fn', ctx=Load()), args=[BinOp(left=Name(id='i', ctx=Load()), op=Sub(), right=Constant(value=2, kind=None))], keywords=[]), type_comment=None), 
            Assign(targets=[Name(id='b', ctx=Store())], value=Call(func=Name(id='fn', ctx=Load()), args=[BinOp(left=Name(id='i', ctx=Load()), op=Sub(), right=Constant(value=1, kind=None))], keywords=[]), type_comment=None), Assign(targets=[Name(id='c', ctx=Store())], value=BinOp(left=Name(id='a', ctx=Load()), op=Add(), right=Name(id='b', ctx=Load())), type_comment=None), Expr(value=Call(func=Name(id='print', ctx=Load()), args=[Name(id='a', ctx=Load()), Name(id='b', ctx=Load()), Name(id='c', ctx=Load())], keywords=[])), Return(value=Name(id='c', ctx=Load()))])
    
    
    
    
    ], decorator_list=[], returns=None, type_comment=None), Assign(targets=[Name(id='x', ctx=Store())], value=Call(func=Name(id='fn', ctx=Load()), args=[Constant(value=10, kind=None)], keywords=[]), type_comment=None)],
type_ignores=[])


Module(body=[
    ClassDef(name='A', bases=[], keywords=[], body=[Expr(value=Constant(value=Ellipsis, kind=None))], decorator_list=[]), Import(names=[alias(name='math', asname=None)]),
    Assign(targets=[Name(id='a', ctx=Store())], value=Name(id='A', ctx=Load()), type_comment=None), 
    Expr(value=Call(func=Attribute(value=Name(id='a', ctx=Load()), attr='prit', ctx=Load()), args=[Constant(value=1, kind=None)], keywords=[])), 
    Expr(
        value=Call(
            func=Attribute(value=Name(id='math', ctx=Load()), attr='cos', ctx=Load()), args=[], keywords=[]
            ))], type_ignores=[])

Module(body=[
    Expr(value=Attribute(value=Name(id='a', ctx=Load()), attr='a', ctx=Load())), 
    Expr(value=Call(func=Attribute(value=Name(id='a', ctx=Load()), attr='print', ctx=Load()), args=[Name(id='x', ctx=Load())], keywords=[]))], type_ignores=[])

# BinOp Constant Name BoolOp Compare UnaryOp Subscript List Tuple Dict Call Attribute

Module(body=[
    Import(names=[alias(name='system.t_algorithm_lib', asname='t_algorithm_lib')]), 
    Import(names=[alias(name='system.mc', asname='mc')]), 
    ImportFrom(module='system.mc_nbt', names=[alias(name='RawJsonText', asname=None)], level=0), 
    Expr(value=Call(func=Name(id='print', ctx=Load()), 
    args=[Call(func=Name(id='RawJsonText', ctx=Load()), args=[], keywords=[keyword(arg='file', value=Constant(value='a.josn', kind=None))])], keywords=[]))], type_ignores=[])