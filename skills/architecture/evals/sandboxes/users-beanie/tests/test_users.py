def test_create_user_hides_the_hash(ada):
    assert set(ada) == {"id", "email", "display_name", "bio"}
