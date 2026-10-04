# Third-party typing limits

Pyright checks every application module and test in strict mode. MLX, NumPy, Pydantic, PyTorch, and pytest use their published types. These local stubs cover only the Brian2 and PyArrow APIs used here; they do not supply runtime code.

Brian2 creates unit-bearing arrays and state attributes from equation strings at runtime. Its quantity arithmetic and dynamic views use `Any` inside this stub. Names, constructors, schedules, and configuration remain typed. The independent adapter converts monitored values into NumPy trace arrays before returning them. Numerical qualification verifies units, shapes, phases, and values. The stub does not prove dimensional correctness.

PyArrow file/table operations have typed signatures here. Column values enter the application as NumPy arrays; the reader checks required columns, nulls, and finite times. Real Parquet tests verify these operations and the supported time-column contracts. This stub does not prove the physical type of arbitrary input files.

The MLX array bridge contains two specific typing suppressions: the published `eval` signature has an untyped variadic parameter, and its constructor annotation rejects NumPy 1.26 Boolean arrays that the runtime accepts. Qualification exercises both operations on Metal. Host trace conversion uses a numeric/Boolean array union. PyTorch's frozen surrogate gradient contains two specific suppressions for the untyped `Function.apply` dispatcher and its variadic base-class gradient signature. No package, application file, or test is excluded to conceal these limitations.
