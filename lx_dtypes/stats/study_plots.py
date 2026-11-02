"""Identifier-free plot projections with full-population label summaries."""

from scipy.stats import binomtest

from lx_dtypes.models.contracts.study_analysis import (
    StudyPlotConfiguration,
    StudyPlotPoint,
    StudyPlotRate,
    StudyPlotResult,
)


class StudyPlotAccumulator:
    def __init__(self, config: StudyPlotConfiguration, variables: list[str]) -> None:
        self.config = config
        self.variables = variables
        self.points: list[StudyPlotPoint] = []
        self.counts: dict[tuple[str, str], list[int]] = {}
        self.patients: set[str] = set()
        self.independent = True
        self.total = 0

    def add(self, patient: str, point: StudyPlotPoint) -> None:
        if patient in self.patients:
            self.independent = False
        self.patients.add(patient)
        self.total += 1
        if len(self.points) < self.config.limit:
            self.points.append(point)
        for label in point.labels:
            counts = self.counts.setdefault((point.group, label.name), [0, 0, 0])
            counts[
                0
                if label.state == "positive"
                else 1
                if label.state == "negative"
                else 2
            ] += 1

    def result(self) -> StudyPlotResult:
        rates: list[StudyPlotRate] = []
        for (group, label), (positive, negative, unknown) in self.counts.items():
            denominator = positive + negative
            low = high = None
            if denominator and self.independent:
                interval = binomtest(positive, denominator).proportion_ci(
                    method="wilson"
                )
                low, high = float(interval.low), float(interval.high)
            rates.append(
                StudyPlotRate(
                    group=group,
                    label=label,
                    positive=positive,
                    negative=negative,
                    unknown=unknown,
                    rate=positive / denominator if denominator else None,
                    low=low,
                    high=high,
                )
            )
        return StudyPlotResult(
            labels=self.config.labels,
            variables=self.variables,
            points=self.points,
            total=self.total,
            omitted=self.total - len(self.points),
            independent=self.independent,
            rates=rates,
        )
