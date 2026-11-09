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


def test_new_entity_types():
    text = ("I live at 1600 Pennsylvania Avenue NW, Apt 4, my DOB is 03/14/1999, born March 14, 1999, "
            "key AKIAIOSFODNN7EXAMPLE, and the meeting is on 12/01/2025.")
    masked, ents = pii.mask(text)
    types = [e["type"] for e in ents]
    assert "US_ADDRESS" in types and types.count("DATE_OF_BIRTH") == 2 and "AWS_ACCESS_KEY" in types
    assert "12/01/2025" in masked  # a plain date is not PII
    assert "my DOB is [DATE_OF_BIRTH]" in masked  # only the date is masked, not the words around it
