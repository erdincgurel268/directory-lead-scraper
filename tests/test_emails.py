from leadscraper.emails import email_matches_site, pick_best_email, site_root


def test_site_root_strips_www():
    assert site_root("https://www.example-builder.com.au/contact") == "example-builder.com.au"


def test_placeholder_emails_are_rejected():
    assert pick_best_email(["john@doe.com", "email@example.com"], "doe.com") == ""


def test_prefers_exact_domain_role_mailbox():
    emails = ["owner@gmail.com", "info@tndesignconsult.com", "sales@other.com"]
    assert pick_best_email(emails, "tndesignconsult.com") == "info@tndesignconsult.com"


def test_other_domains_are_rejected():
    assert pick_best_email(["press@google.com"], "randmachining.com") == ""
    assert not email_matches_site("press@google.com", "randmachining.com")


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


def test_find_email_uses_company_domain(monkeypatch):
    import leadscraper.emails as emails

    pages = {
        "http://acme-build.com.au": FakeResponse("Call us. john@doe.com"),
        "http://acme-build.com.au/contact": FakeResponse("Email: Office@Acme-Build.com.au"),
    }
    monkeypatch.setattr(emails, "polite_get", lambda url, delay=0.5, timeout=8: pages.get(url))
    assert emails.find_email("http://acme-build.com.au") == "office@acme-build.com.au"


def test_social_links_are_never_company_sites():
    from leadscraper.emails import find_email
    assert find_email("https://www.google.com/search?q=acme") == ""
    assert find_email("https://facebook.com/acme") == ""
