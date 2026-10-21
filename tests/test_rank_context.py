from phishx.extended_features import analyze_extended
from phishx.ranked_context import lookup_rank


def test_rank_context_does_not_follow_deceptive_brand_text():
    ranks={'google.com':1}
    assert lookup_rank(analyze_extended('https://google.com/'),ranks)==1
    assert lookup_rank(analyze_extended('https://google.com.evil.example/'),ranks)==1000001
    assert lookup_rank(analyze_extended('https://google.com@evil.example/'),ranks)==1000001
    assert lookup_rank(analyze_extended('https://gооgle.com/'),ranks)==1000001
