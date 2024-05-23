from hoodmane_coderunner import CodeRunner, eval_code, should_quiet
import pytest


def test_code_runner():
    assert should_quiet("1+1;")
    assert not should_quiet("1+1#;")
    assert not should_quiet("5-2  # comment with trailing semicolon ;")

    # Normal usage
    assert CodeRunner("1+1").compile().run() == 2
    assert CodeRunner("1+1\n1+1").compile().run() == 2
    assert CodeRunner("x + 7").compile().run({"x": 3}) == 10
    cr = CodeRunner("x + 7")

    # Ast transform
    import ast

    l = cr.ast.body[0].value.left  # type: ignore[attr-defined]
    cr.ast.body[0].value.left = ast.BinOp(  # type: ignore[attr-defined]
        left=l, op=ast.Mult(), right=ast.Constant(value=2)
    )
    assert cr.compile().run({"x": 3}) == 13

    # Code transform
    assert cr.code
    cr.code = cr.code.replace(co_consts=(0, 3, 5, None))
    assert cr.run({"x": 4}) == 17


def test_code_runner_mode():
    from codeop import PyCF_DONT_IMPLY_DEDENT  # type: ignore[attr-defined]

    assert CodeRunner("1+1\n1+1", mode="exec").compile().run() == 2
    with pytest.raises(SyntaxError, match="invalid syntax"):
        CodeRunner("1+1\n1+1", mode="eval").compile().run()
    with pytest.raises(
        SyntaxError,
        match="multiple statements found while compiling a single statement",
    ):
        CodeRunner("1+1\n1+1", mode="single").compile().run()
    with pytest.raises(SyntaxError, match="invalid syntax"):
        CodeRunner(
            "def f():\n  1", mode="single", flags=PyCF_DONT_IMPLY_DEDENT
        ).compile().run()


def test_eval_code():
    ns: dict[str, Any] = {}
    assert (
        eval_code(
            """
        def f(x):
            return 2*x + 5
        f(77)
    """,
            ns,
        )
        == 2 * 77 + 5
    )
    assert ns["f"](7) == 2 * 7 + 5

    assert eval_code("(x:=4)", ns) == 4
    assert ns["x"] == 4
    assert eval_code("x=7", ns) is None
    assert ns["x"] == 7

    # default return_mode ('last_expr'), semicolon
    assert eval_code("1+1;", ns) is None
    assert eval_code("1+1#;", ns) == 2
    assert eval_code("5-2  # comment with trailing semicolon ;", ns) == 3
    assert eval_code("4//2\n", ns) == 2
    assert eval_code("2**1\n\n", ns) == 2
    assert eval_code("4//2;\n", ns) is None
    assert eval_code("2**1;\n\n", ns) is None

    # 'last_expr_or_assign' return_mode, semicolon
    assert eval_code("1 + 1", ns, return_mode="last_expr_or_assign") == 2
    assert eval_code("x = 1 + 1", ns, return_mode="last_expr_or_assign") == 2
    assert eval_code("a = 5 ; a += 1", ns, return_mode="last_expr_or_assign") == 6
    assert eval_code("a = 5 ; a += 1;", ns, return_mode="last_expr_or_assign") is None
    assert (
        eval_code("l = [1, 1, 2] ; l[0] = 0", ns, return_mode="last_expr_or_assign")
        is None
    )
    assert eval_code("a = b = 2", ns, return_mode="last_expr_or_assign") == 2

    # 'none' return_mode, (useless) semicolon
    assert eval_code("1 + 1", ns, return_mode="none") is None
    assert eval_code("x = 1 + 1", ns, return_mode="none") is None
    assert eval_code("a = 5 ; a += 1", ns, return_mode="none") is None
    assert eval_code("a = 5 ; a += 1;", ns, return_mode="none") is None
    assert eval_code("l = [1, 1, 2] ; l[0] = 0", ns, return_mode="none") is None

    # with 'quiet_trailing_semicolon' set to False
    assert eval_code("1+1;", ns, quiet_trailing_semicolon=False) == 2
    assert eval_code("1+1#;", ns, quiet_trailing_semicolon=False) == 2
    assert (
        eval_code(
            "5-2  # comment with trailing semicolon ;",
            ns,
            quiet_trailing_semicolon=False,
        )
        == 3
    )
    assert eval_code("4//2\n", ns, quiet_trailing_semicolon=False) == 2
    assert eval_code("2**1\n\n", ns, quiet_trailing_semicolon=False) == 2
    assert eval_code("4//2;\n", ns, quiet_trailing_semicolon=False) == 2
    assert eval_code("2**1;\n\n", ns, quiet_trailing_semicolon=False) == 2
