def test_repository_skeleton_imports() -> None:
    import harness
    import nodehost

    assert harness is not None
    assert nodehost is not None
