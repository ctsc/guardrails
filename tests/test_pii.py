import pii


def test_masks_each_type():
    masked, ents = pii.mask("mail a@b.co, call 555-123-4567, ssn 123-45-6789, card 4111 1111 1111 1111, ip 192.168.1.1")
    types = {e["type"] for e in ents}
    assert types == {"EMAIL", "PHONE", "SSN", "CREDIT_CARD", "IP_ADDRESS"}
    assert "a@b.co" not in masked and "4111" not in masked and "[SSN]" in masked


def test_luhn_rejects_random_digits():
    _, ents = pii.mask("order id 1234 5678 9012 3456")
    assert not any(e["type"] == "CREDIT_CARD" for e in ents)


def test_plain_text_untouched():
    text = "How do I kill a Python process?"
    masked, ents = pii.mask(text)
    assert masked == text and ents == []


def test_types_filter():
    masked, ents = pii.mask("a@b.co 555-123-4567", types=["EMAIL"])
    assert [e["type"] for e in ents] == ["EMAIL"] and "555-123-4567" in masked
