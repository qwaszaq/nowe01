"""
Drill-Down Data Aggregation Engine
Hierarchical data navigation from summary to detail
"""

import logging
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any, Callable
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AggregationLevel(str, Enum):
    """Hierarchical aggregation levels"""
    COMPANY = "company"              # Highest level - entire company
    DIVISION = "division"            # Business divisions
    DEPARTMENT = "department"        # Departments within divisions
    CATEGORY = "category"            # Metric categories (liquidity, profitability, etc.)
    METRIC_GROUP = "metric_group"    # Groups of related metrics
    INDIVIDUAL_METRIC = "individual_metric"  # Individual metrics
    TIME_YEAR = "time_year"          # Year-level aggregation
    TIME_QUARTER = "time_quarter"    # Quarter-level aggregation
    TIME_MONTH = "time_month"        # Month-level aggregation
    TIME_WEEK = "time_week"          # Week-level aggregation
    TIME_DAY = "time_day"            # Day-level detail
    DOCUMENT_SET = "document_set"    # Set of documents
    INDIVIDUAL_DOCUMENT = "individual_document"  # Single document
    PAGE_SET = "page_set"            # Pages within document
    INDIVIDUAL_PAGE = "individual_page"  # Single page


class AggregationType(str, Enum):
    """Types of aggregation functions"""
    SUM = "sum"
    AVERAGE = "average"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    WEIGHTED_AVERAGE = "weighted_average"
    FIRST = "first"
    LAST = "last"


class DrillPath(BaseModel):
    """
    Path through drill-down hierarchy
    """
    level: AggregationLevel
    value: str = Field(..., description="Value at this level (e.g., 'Q1 2024')")
    label: str = Field(..., description="Human-readable label")
    parent_path: Optional['DrillPath'] = None

    @property
    def full_path(self) -> str:
        """Get full hierarchical path as string"""
        if self.parent_path:
            return f"{self.parent_path.full_path} > {self.label}"
        return self.label


class AggregatedMetric(BaseModel):
    """
    Aggregated metric at a specific level
    """
    metric_name: str
    aggregation_level: AggregationLevel
    aggregation_type: AggregationType

    # Aggregated value
    value: float
    formatted_value: str
    unit: str

    # Contributing data points
    data_point_count: int = Field(..., description="Number of data points aggregated")
    source_documents: List[str] = Field(default_factory=list, description="Source document IDs")

    # Statistical context
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    std_deviation: Optional[float] = None

    # Drill-down info
    can_drill_down: bool = Field(default=False, description="Whether further drill-down is possible")
    drill_down_levels: List[AggregationLevel] = Field(default_factory=list)

    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.now)


class DrillDownNode(BaseModel):
    """
    Node in drill-down hierarchy tree
    """
    node_id: str
    level: AggregationLevel
    label: str

    # Metrics at this level
    metrics: List[AggregatedMetric] = Field(default_factory=list)

    # Summary statistics for this node
    summary: Dict[str, Any] = Field(default_factory=dict)

    # Child nodes
    children: List['DrillDownNode'] = Field(default_factory=list)
    child_count: int = 0

    # Navigation
    parent_id: Optional[str] = None
    breadcrumb: List[str] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)


class DrillDownResult(BaseModel):
    """
    Result of a drill-down operation
    """
    current_level: AggregationLevel
    current_node_id: str
    current_label: str

    # Current level data
    metrics: List[AggregatedMetric] = Field(default_factory=list)
    summary_stats: Dict[str, Any] = Field(default_factory=dict)

    # Navigation context
    breadcrumb: List[Dict[str, str]] = Field(default_factory=list)
    can_drill_up: bool = Field(default=False)
    can_drill_down: bool = Field(default=False)

    # Available drill-down options
    drill_down_options: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Available next-level drill-downs"
    )

    # Drill-up option
    drill_up_target: Optional[Dict[str, str]] = None

    # Insights at this level
    insights: List[str] = Field(default_factory=list)


DrillPath.model_rebuild()
DrillDownNode.model_rebuild()


class DrillDownEngine:
    """
    Drill-Down Data Aggregation Engine
    Enables hierarchical navigation through data from summary to detail
    """

    def __init__(self):
        """Initialize drill-down engine"""
        self.hierarchy_definitions: Dict[str, List[AggregationLevel]] = {}
        self._initialize_default_hierarchies()
        logger.info("DrillDownEngine initialized with default hierarchies")

    def _initialize_default_hierarchies(self):
        """Initialize standard drill-down hierarchies"""

        # Time hierarchy
        self.hierarchy_definitions['time'] = [
            AggregationLevel.TIME_YEAR,
            AggregationLevel.TIME_QUARTER,
            AggregationLevel.TIME_MONTH,
            AggregationLevel.TIME_WEEK,
            AggregationLevel.TIME_DAY
        ]

        # Organizational hierarchy
        self.hierarchy_definitions['organization'] = [
            AggregationLevel.COMPANY,
            AggregationLevel.DIVISION,
            AggregationLevel.DEPARTMENT
        ]

        # Metric hierarchy
        self.hierarchy_definitions['metrics'] = [
            AggregationLevel.CATEGORY,
            AggregationLevel.METRIC_GROUP,
            AggregationLevel.INDIVIDUAL_METRIC
        ]

        # Document hierarchy
        self.hierarchy_definitions['documents'] = [
            AggregationLevel.DOCUMENT_SET,
            AggregationLevel.INDIVIDUAL_DOCUMENT,
            AggregationLevel.PAGE_SET,
            AggregationLevel.INDIVIDUAL_PAGE
        ]

        logger.debug(f"Initialized {len(self.hierarchy_definitions)} drill-down hierarchies")

    def aggregate_metrics(
        self,
        metric_name: str,
        data_points: List[Dict[str, Any]],
        aggregation_type: AggregationType = AggregationType.AVERAGE,
        level: AggregationLevel = AggregationLevel.COMPANY,
        group_by: Optional[str] = None
    ) -> List[AggregatedMetric]:
        """
        Aggregate metrics at specified level

        Args:
            metric_name: Name of metric to aggregate
            data_points: List of data points with 'value' and optional metadata
            aggregation_type: How to aggregate (sum, average, etc.)
            level: Aggregation level
            group_by: Optional field to group by before aggregating

        Returns:
            List of aggregated metrics (one per group if group_by specified)
        """
        if not data_points:
            return []

        # Group data if needed
        if group_by:
            groups = self._group_data_points(data_points, group_by)
            results = []
            for group_value, group_points in groups.items():
                agg_metric = self._aggregate_group(
                    metric_name, group_points, aggregation_type, level, group_value
                )
                results.append(agg_metric)
            return results
        else:
            # Single aggregation
            agg_metric = self._aggregate_group(
                metric_name, data_points, aggregation_type, level, "All"
            )
            return [agg_metric]

    def drill_down(
        self,
        current_node: DrillDownNode,
        target_child: str,
        hierarchy_type: str = 'time'
    ) -> DrillDownResult:
        """
        Perform drill-down operation to next level

        Args:
            current_node: Current position in hierarchy
            target_child: Which child to drill into
            hierarchy_type: Type of hierarchy ('time', 'organization', 'metrics', 'documents')

        Returns:
            DrillDownResult for the target child level
        """
        # Find target child node
        target_node = None
        for child in current_node.children:
            if child.node_id == target_child or child.label == target_child:
                target_node = child
                break

        if not target_node:
            raise ValueError(f"Child '{target_child}' not found in node '{current_node.node_id}'")

        # Build breadcrumb
        breadcrumb = current_node.breadcrumb + [
            {"level": current_node.level.value, "label": current_node.label}
        ]

        # Determine drill-down options
        drill_down_options = [
            {"id": child.node_id, "label": child.label}
            for child in target_node.children
        ]

        # Determine drill-up target
        drill_up_target = {
            "id": current_node.node_id,
            "label": current_node.label
        } if current_node.node_id else None

        # Generate insights
        insights = self._generate_drill_insights(target_node, current_node)

        return DrillDownResult(
            current_level=target_node.level,
            current_node_id=target_node.node_id,
            current_label=target_node.label,
            metrics=target_node.metrics,
            summary_stats=target_node.summary,
            breadcrumb=breadcrumb,
            can_drill_up=drill_up_target is not None,
            can_drill_down=len(drill_down_options) > 0,
            drill_down_options=drill_down_options,
            drill_up_target=drill_up_target,
            insights=insights
        )

    def drill_up(
        self,
        current_node: DrillDownNode
    ) -> Optional[DrillDownResult]:
        """
        Perform drill-up operation to parent level

        Args:
            current_node: Current position in hierarchy

        Returns:
            DrillDownResult for parent level, or None if at top
        """
        if not current_node.parent_id:
            return None

        # Would need to reconstruct parent node from storage
        # For now, return None - in real implementation, fetch from storage
        logger.warning("Drill-up requires parent node reconstruction - not implemented")
        return None

    def build_hierarchy_tree(
        self,
        metrics_by_level: Dict[AggregationLevel, List[AggregatedMetric]],
        hierarchy_type: str = 'time'
    ) -> DrillDownNode:
        """
        Build complete hierarchy tree from aggregated metrics

        Args:
            metrics_by_level: Metrics organized by aggregation level
            hierarchy_type: Type of hierarchy to build

        Returns:
            Root node of hierarchy tree
        """
        hierarchy = self.hierarchy_definitions.get(hierarchy_type, [])

        if not hierarchy:
            raise ValueError(f"Unknown hierarchy type: {hierarchy_type}")

        # Build from top level down
        root_level = hierarchy[0]
        root_metrics = metrics_by_level.get(root_level, [])

        root_node = DrillDownNode(
            node_id=f"{hierarchy_type}_root",
            level=root_level,
            label=f"All {hierarchy_type.title()}",
            metrics=root_metrics,
            breadcrumb=[]
        )

        # Recursively build child levels
        if len(hierarchy) > 1:
            self._build_children(root_node, metrics_by_level, hierarchy, 1, hierarchy_type)

        return root_node

    # ============================================
    # PRIVATE HELPER METHODS
    # ============================================

    def _group_data_points(
        self,
        data_points: List[Dict[str, Any]],
        group_by: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group data points by specified field"""
        groups: Dict[str, List[Dict[str, Any]]] = {}

        for point in data_points:
            group_value = point.get(group_by, 'Unknown')
            if group_value not in groups:
                groups[group_value] = []
            groups[group_value].append(point)

        return groups

    def _aggregate_group(
        self,
        metric_name: str,
        data_points: List[Dict[str, Any]],
        aggregation_type: AggregationType,
        level: AggregationLevel,
        group_label: str
    ) -> AggregatedMetric:
        """Aggregate a single group of data points"""
        values = [p['value'] for p in data_points if 'value' in p]

        if not values:
            return AggregatedMetric(
                metric_name=metric_name,
                aggregation_level=level,
                aggregation_type=aggregation_type,
                value=0.0,
                formatted_value="N/A",
                unit="",
                data_point_count=0,
                can_drill_down=False
            )

        # Calculate aggregated value
        if aggregation_type == AggregationType.SUM:
            agg_value = sum(values)
        elif aggregation_type == AggregationType.AVERAGE:
            agg_value = sum(values) / len(values)
        elif aggregation_type == AggregationType.MEDIAN:
            sorted_values = sorted(values)
            mid = len(sorted_values) // 2
            agg_value = sorted_values[mid] if len(sorted_values) % 2 == 1 else (sorted_values[mid-1] + sorted_values[mid]) / 2
        elif aggregation_type == AggregationType.MIN:
            agg_value = min(values)
        elif aggregation_type == AggregationType.MAX:
            agg_value = max(values)
        elif aggregation_type == AggregationType.COUNT:
            agg_value = len(values)
        elif aggregation_type == AggregationType.FIRST:
            agg_value = values[0]
        elif aggregation_type == AggregationType.LAST:
            agg_value = values[-1]
        else:
            agg_value = sum(values) / len(values)  # Default to average

        # Calculate statistics
        min_val = min(values)
        max_val = max(values)

        std_dev = None
        if len(values) > 1:
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
            std_dev = variance ** 0.5

        # Extract source documents
        source_docs = list(set(p.get('document_id', '') for p in data_points if 'document_id' in p))

        # Determine if can drill down (if we have groupable fields)
        can_drill = any('category' in p or 'period' in p or 'document_id' in p for p in data_points)

        return AggregatedMetric(
            metric_name=metric_name,
            aggregation_level=level,
            aggregation_type=aggregation_type,
            value=agg_value,
            formatted_value=f"{agg_value:.2f}",
            unit="",
            data_point_count=len(values),
            source_documents=source_docs,
            min_value=min_val,
            max_value=max_val,
            std_deviation=std_dev,
            can_drill_down=can_drill,
            drill_down_levels=[]
        )

    def _build_children(
        self,
        parent_node: DrillDownNode,
        metrics_by_level: Dict[AggregationLevel, List[AggregatedMetric]],
        hierarchy: List[AggregationLevel],
        current_index: int,
        hierarchy_type: str
    ):
        """Recursively build child nodes"""
        if current_index >= len(hierarchy):
            return

        current_level = hierarchy[current_index]
        level_metrics = metrics_by_level.get(current_level, [])

        # Group metrics by some identifier (simplified - would need better logic)
        for i, metric in enumerate(level_metrics):
            child_node = DrillDownNode(
                node_id=f"{hierarchy_type}_{current_level.value}_{i}",
                level=current_level,
                label=f"{current_level.value.title()} {i+1}",
                metrics=[metric],
                parent_id=parent_node.node_id,
                breadcrumb=parent_node.breadcrumb + [
                    {"level": parent_node.level.value, "label": parent_node.label}
                ]
            )

            parent_node.children.append(child_node)

            # Recurse to next level
            if current_index + 1 < len(hierarchy):
                self._build_children(
                    child_node, metrics_by_level, hierarchy, current_index + 1, hierarchy_type
                )

        parent_node.child_count = len(parent_node.children)

    def _generate_drill_insights(
        self,
        current_node: DrillDownNode,
        parent_node: DrillDownNode
    ) -> List[str]:
        """Generate insights when drilling down"""
        insights = []

        # Compare child metrics to parent
        if parent_node.metrics and current_node.metrics:
            parent_avg = sum(m.value for m in parent_node.metrics) / len(parent_node.metrics)
            current_avg = sum(m.value for m in current_node.metrics) / len(current_node.metrics)

            if parent_avg > 0:
                diff_pct = ((current_avg - parent_avg) / parent_avg) * 100
                if abs(diff_pct) > 10:
                    direction = "higher" if diff_pct > 0 else "lower"
                    insights.append(
                        f"📊 This {current_node.level.value} shows {abs(diff_pct):.1f}% {direction} values than parent average"
                    )

        # Insights about data distribution
        if len(current_node.children) > 0:
            insights.append(f"🔍 {len(current_node.children)} sub-levels available for further analysis")

        return insights
