def test_import_permit_fastmcp():
    import permit_fastmcp

    assert permit_fastmcp is not None


def test_import_example_server():
    import permit_fastmcp.example_server.example as example

    assert example is not None
