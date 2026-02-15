from parser import parse_prompt, normalize_tag
from aggregator import aggregate_tags
from editor import delete_tags, rename_tag, merge_tags

def test_normalization():
    assert normalize_tag("a girl") == "a girl"
    assert normalize_tag("(a girl:1.2)") == "a girl"
    assert normalize_tag("((a girl))") == "a girl"
    assert normalize_tag("[a girl]") == "a girl"
    assert normalize_tag("  A Girl  ") == "a girl"
    assert normalize_tag("(masterpiece: 1.2)") == "masterpiece"
    print("test_normalization passed")

def test_parsing():
    prompt = "a girl drinking syrup, (white dress:1.2), [blue eyes], ((pigtails))"
    expected = ["a girl drinking syrup", "white dress", "blue eyes", "pigtails"]
    assert parse_prompt(prompt) == expected
    print("test_parsing passed")

def test_aggregation():
    tag_lists = [
        ["a girl", "white dress"],
        ["a girl", "blue eyes"]
    ]
    expected = {"a girl": 2, "white dress": 1, "blue eyes": 1}
    assert aggregate_tags(tag_lists) == expected
    print("test_aggregation passed")

if __name__ == "__main__":
    test_normalization()
    test_parsing()
    test_aggregation()
    print("All tests passed!")
