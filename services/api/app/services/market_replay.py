"""Bounded Decimal-only valuation and paper fills, with no execution adapter."""
from collections import defaultdict
from datetime import timedelta
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, localcontext
from itertools import product
from typing import NamedTuple

from app.schemas.market_intelligence import FXBatch, FXReplay, InvestmentReplay, Quote, SecurityBatch

ZERO = Decimal(0)
ONE = Decimal(1)
BPS = Decimal(10000)


def format_measure(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.00000001")))


def money(amount: Decimal, currency: str) -> Decimal:
    return amount.quantize(Decimal("1" if currency == "JPY" else "0.01"), rounding=ROUND_DOWN)


def research_snapshot(series: SecurityBatch, at) -> dict:
    bars = [bar for bar in series.bars if bar.at <= at]
    if not bars:
        return {"symbol": series.symbol, "status": "NO_OBSERVATION_BY_CUTOFF"}
    close = bars[-1].close
    fundamentals = series.fundamentals
    if fundamentals is not None and fundamentals.available_at > at:
        fundamentals = None
    earnings = fundamentals.earnings_per_share if fundamentals else None
    distribution = fundamentals.annual_distribution if fundamentals else None
    recent = bars[-min(20, len(bars)):]
    return {
        "symbol": series.symbol, "asset_class": series.asset_class, "currency": series.currency,
        "sector": series.sector, "last_bar_at": bars[-1].at.isoformat(),
        "last_close": str(close),
        "simple_moving_average": format_measure(sum(bar.close for bar in recent) / len(recent)),
        "moving_average_samples": len(recent),
        "price_to_earnings": format_measure(close / earnings) if earnings is not None and earnings > 0 else None,
        "indicated_distribution_yield": format_measure(distribution / close) if distribution is not None else None,
        "fundamentals": fundamentals.model_dump(mode="json") if fundamentals else None,
    }


def track_series(series, capital, strategy, lookback, impact, commission):
    cash, shares, costs, dividends, fills = capital, ZERO, ZERO, ZERO, 0
    equity = []
    bars = series.bars
    for index, bar in enumerate(bars):
        if shares:
            distribution = shares * bar.dividend
            dividends += distribution
            cash += distribution
        wants_shares = strategy == "BUY_AND_HOLD"
        if strategy == "CLOSE_ABOVE_MOVING_AVERAGE" and index >= lookback:
            closes = [item.close for item in bars[index - lookback:index]]
            wants_shares = closes[-1] > sum(closes) / lookback
        if wants_shares and not shares:
            price = bar.open * (ONE + impact)
            shares = max(ZERO, (cash - commission) // price)
            if shares:
                cash -= shares * price + commission
                costs += shares * (price - bar.open) + commission
                fills += 1
        elif shares and not wants_shares:
            price = bar.open * (ONE - impact)
            if shares * price > commission:
                cash += shares * price - commission
                costs += shares * (bar.open - price) + commission
                shares = ZERO
                fills += 1
        equity.append(cash + shares * bar.close)
    return equity, costs, fills, dividends, shares * bars[-1].close


def statistics(equity, capital):
    peak, drawdown = capital, ZERO
    changes = []
    previous = capital
    for value in equity:
        peak = max(peak, value)
        drawdown = max(drawdown, (peak - value) / peak)
        changes.append(value / previous - ONE)
        previous = value
    mean = sum(changes) / len(changes)
    volatility = (sum((change - mean) ** 2 for change in changes) / len(changes)).sqrt()
    return {
        "return_fraction": format_measure(equity[-1] / capital - ONE),
        "max_drawdown_fraction": format_measure(drawdown),
        "per_observation_volatility": format_measure(volatility),
        "per_observation_sharpe_zero_risk_free": format_measure(mean / volatility) if volatility else None,
    }


def investment_replay(request: InvestmentReplay, portfolio: list[SecurityBatch], benchmark: SecurityBatch) -> dict:
    weights = [holding.weight_bp for holding in request.portfolio]
    if sum(weights) != BPS or len({series.symbol for series in portfolio}) != len(portfolio):
        raise ValueError("Portfolio must contain unique symbols with weights totaling 10000 bp")
    dates = [bar.at.date() for bar in benchmark.bars]
    if any(series.currency != benchmark.currency or [bar.at.date() for bar in series.bars] != dates
           for series in portfolio):
        raise ValueError("Replay requires aligned observation dates in a single currency")
    if any(bar.at > request.as_of for series in [*portfolio, benchmark] for bar in series.bars):
        raise ValueError("Replay cutoff cannot precede source observations")
    if request.strategy == "CLOSE_ABOVE_MOVING_AVERAGE" and request.lookback >= len(dates):
        raise ValueError("Replay window does not contain a tradable observation after warm-up")
    capital = request.capital
    impact = (request.half_spread_bp + request.slippage_bp) / BPS
    with localcontext() as context:
        context.prec = 48
        sleeves = [track_series(series, capital * weight / BPS, request.strategy, request.lookback,
                                impact, request.commission) for series, weight in zip(portfolio, weights)]
        benchmark_values, benchmark_costs, _, _, _ = track_series(
            benchmark, capital, "BUY_AND_HOLD", request.lookback, impact, request.commission,
        )
        values = [sum(items) for items in zip(*(sleeve[0] for sleeve in sleeves))]
        sectors = defaultdict(lambda: ZERO)
        asset_classes = defaultdict(lambda: ZERO)
        symbols = {}
        for series, sleeve in zip(portfolio, sleeves):
            sectors[series.sector] += sleeve[4]
            asset_classes[series.asset_class] += sleeve[4]
            symbols[series.symbol] = format_measure(sleeve[4] / values[-1])
        return {
            "status": "SIMULATED", "currency": benchmark.currency, "strategy": request.strategy,
            "observations": len(dates), "from": dates[0].isoformat(), "through": dates[-1].isoformat(),
            "portfolio": statistics(values, capital), "benchmark": statistics(benchmark_values, capital),
            "benchmark_symbol": benchmark.symbol,
            "benchmark_relative_return_fraction": format_measure((values[-1] - benchmark_values[-1]) / capital),
            "marked_equity": format_measure(values[-1]),
            "estimated_execution_costs": format_measure(sum(sleeve[1] for sleeve in sleeves)),
            "benchmark_execution_costs": format_measure(benchmark_costs),
            "paper_fills": sum(sleeve[2] for sleeve in sleeves),
            "paper_distributions": format_measure(sum(sleeve[3] for sleeve in sleeves)),
            "final_marked_exposure_by_sector": {key: format_measure(amount / values[-1])
                                                for key, amount in sorted(sectors.items())},
            "final_marked_exposure_by_asset_class": {key: format_measure(amount / values[-1])
                                                     for key, amount in sorted(asset_classes.items())},
            "final_marked_exposure_by_symbol": symbols,
            "final_cash_fraction": format_measure(ONE - sum(sectors.values()) / values[-1]),
            "input_weight_concentration": format_measure(sum((weight / BPS) ** 2 for weight in weights)),
        }


class Leg(NamedTuple):
    quote: Quote
    source: str
    target: str


@dataclass(frozen=True)
class Fill:
    before_fee: Decimal
    after_fee: Decimal


def fx_fill(leg: Leg, amount: Decimal, slippage_bp: int) -> Fill | None:
    quote = leg.quote
    if leg.source == quote.base:
        base_debit = amount
        gross = amount * quote.bid * (ONE - slippage_bp / BPS)
        depth = quote.bid_depth_base
    else:
        base_debit = amount / (quote.ask * (ONE + slippage_bp / BPS))
        gross = base_debit
        depth = quote.ask_depth_base
    if base_debit > depth:
        return None
    after_fee = money(gross * (ONE - quote.fee_bp / BPS), leg.target)
    return Fill(gross, after_fee) if after_fee > 0 else None


def route_output(route, amount, request):
    elapsed = 0
    for leg in route:
        simulated_at = request.as_of + timedelta(seconds=elapsed)
        if (simulated_at >= leg.quote.expires_at
                or simulated_at - leg.quote.at > timedelta(seconds=request.max_age_seconds)):
            return None
        elapsed += leg.quote.settlement_seconds
        if elapsed > request.max_settlement_seconds:
            return None
        fill = fx_fill(leg, amount, request.slippage_bp)
        if fill is None:
            return None
        amount = fill.after_fee
    return amount


def find_routes(batch: FXBatch, request: FXReplay):
    edges = defaultdict(list)
    start = request.start_currency
    for quote in sorted(batch.quotes, key=lambda item: str(item.quote_id)):
        if quote.at <= request.as_of < quote.expires_at:
            edges[quote.base, quote.counter].append(Leg(quote, quote.base, quote.counter))
            edges[quote.counter, quote.base].append(Leg(quote, quote.counter, quote.base))
    if request.mode == "BEST_DIRECT":
        yield from ((leg,) for leg in edges[start, request.target_currency])
        return
    middle = sorted({target for source, target in edges if source == start})
    for first in middle:
        if request.mode == "CROSS_VENUE_LOOP":
            for a, b in product(edges[start, first], edges[first, start]):
                if a.quote.venue != b.quote.venue:
                    yield a, b
            continue
        terminal = sorted({target for source, target in edges if source == first} - {start})
        for second in terminal:
            yield from product(edges[start, first], edges[first, second], edges[second, start])


def fx_replay(request: FXReplay, batch: FXBatch) -> dict:
    start = request.start_currency
    amount = money(request.amount, start)
    if amount != request.amount:
        raise ValueError("Amount exceeds the supported precision for starting currency")
    with localcontext() as context:
        context.prec = 48
        candidates = []
        for route in find_routes(batch, request):
            output = route_output(route, amount, request)
            if output is not None:
                candidates.append((output, route))
        if not candidates:
            return {"status": "NO_FEASIBLE_ROUTE", "starting_currency": start,
                    "paper_balances": {start: str(amount)}, "paper_legs": [], "paper_loop_pnl": None}
        expected, best = max(candidates, key=lambda item: item[0])
        balances = {start: amount}
        steps = []
        for index, leg in enumerate(best, start=1):
            debit = balances[leg.source]
            interrupted = index == request.failure_at_leg
            if interrupted:
                debit = money(debit * (request.partial_fill_bp or 0) / BPS, leg.source)
            if debit:
                fill = fx_fill(leg, debit, request.slippage_bp)
                if fill is not None:
                    balances[leg.source] -= debit
                    balances[leg.target] = balances.get(leg.target, ZERO) + fill.after_fee
                    steps.append({
                        "quote_id": str(leg.quote.quote_id), "observed_at": leg.quote.at.isoformat(),
                        "origin_ref": leg.quote.origin_ref, "venue": leg.quote.venue, "leg": index,
                        "debit_currency": leg.source, "debit": str(debit),
                        "credit_currency": leg.target, "credit": str(fill.after_fee),
                        "fee_and_rounding_in_credit_currency": format_measure(fill.before_fee - fill.after_fee),
                        "settlement_seconds": leg.quote.settlement_seconds,
                    })
            if interrupted:
                break
        complete = len(steps) == len(best) and request.failure_at_leg is None
        loop_pnl = balances[start] - amount if complete and request.mode != "BEST_DIRECT" else None
        return {
            "status": "SIMULATED" if complete else "INTERRUPTED", "starting_currency": start,
            "planned_terminal_currency": best[-1].target, "planned_terminal_amount": str(expected),
            "planned_settlement_seconds": sum(leg.quote.settlement_seconds for leg in best),
            "eligible_routes": len(candidates), "paper_legs": steps,
            "paper_balances": {key: str(value) for key, value in sorted(balances.items())},
            "paper_loop_pnl": str(loop_pnl) if loop_pnl is not None else None,
            "interrupted_at_leg": request.failure_at_leg,
        }
