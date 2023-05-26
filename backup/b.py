Module(body=[
    Assign(
        targets=[Name(id='x', ctx=Store())],
        value=Constant(value=3, kind=None), 
        type_comment=None), 
    Assign(
        targets=[Name(id='x', ctx=Store())], 
        value=BinOp(



            left=BinOp(eft=BinOp(left=BinOp(left=BinOp(left=Constant(value=1, kind=None),op=Add(),right=Constant(value=2, kind=None)),op=Add(),right=BinOp(left=Constant(value=3, kind=None),op=Div(), right=Constant(value=2, kind=None))), op=Sub(), right=Constant(value=55, kind=None)), op=Add(), right=BinOp(left=Constant(value=33, kind=None), op=Mult(), right=Constant(value=3, kind=None))),
            op=Add(),
            right=Name(id='x', ctx=Load())



            )
            , type_comment=None)], type_ignores=[])