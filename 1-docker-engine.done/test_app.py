from app import is_valid_name


def test_is_valid_name_is_invalid_with_slash():
    assert not is_valid_name('Davide/Setti')
