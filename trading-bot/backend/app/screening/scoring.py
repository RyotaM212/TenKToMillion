from app.models import MarketSnapshot


def clamp(value: float, lower: float = 0, upper: float = 1) -> float:
    return max(lower, min(upper, value))


def score_snapshot(snapshot: MarketSnapshot) -> dict[str, float]:
    price_change_rate = (snapshot.close - snapshot.previous_close) / snapshot.previous_close
    gap_rate = (snapshot.open - snapshot.previous_close) / snapshot.previous_close
    volatility_rate = (snapshot.high - snapshot.low) / max(snapshot.open, 1)

    volume_spike_score = clamp(snapshot.volume / 1_000_000)
    price_change_score = clamp(price_change_rate / 0.15)
    gap_up_score = clamp(gap_rate / 0.08)
    volatility_score = clamp(volatility_rate / 0.12)
    news_score = clamp(snapshot.news_score)
    liquidity_score = clamp(snapshot.volume / 300_000)

    total = (
        volume_spike_score * 30
        + price_change_score * 25
        + gap_up_score * 15
        + volatility_score * 15
        + news_score * 10
        + liquidity_score * 5
    )

    return {
        "score": round(total, 2),
        "volume_spike_score": round(volume_spike_score, 3),
        "price_change_score": round(price_change_score, 3),
        "gap_up_score": round(gap_up_score, 3),
        "volatility_score": round(volatility_score, 3),
        "news_score": round(news_score, 3),
        "liquidity_score": round(liquidity_score, 3),
    }
