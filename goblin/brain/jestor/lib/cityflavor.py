import logging
import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from brain.jestor.lib.database import QueryResult, DatabaseType

logger = logging.getLogger(__name__)


@dataclass
class QueryContext:
    """Stores context about what the query is trying to achieve"""

    main_entity: str  # e.g., 'orders', 'vendors', 'properties'
    related_entities: List[str]
    time_range: Optional[Dict[str, datetime]] = None
    filters: Dict[str, Any] = None
    metrics: List[str] = None
    vendor_name: Optional[str] = None


class CityFlavorQueryTool:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._setup_entity_relationships()

        required_entities = {"Orders", "Vendors"}
        actual_entities = set(self.entity_map.keys())
        missing_entities = required_entities - actual_entities

        if missing_entities:
            logger.error(f"Missing required entities: {missing_entities}")
            raise ValueError(f"Missing required entities: {missing_entities}")

        logger.info(f"CityFlavorQueryTool initialized with: {actual_entities}")

    def _setup_entity_relationships(self):
        """Define the core fields and relationships needed for analysis"""
        self.entity_map = {
            "Orders": {
                "table": "main_order",
                "essential_fields": [
                    "id",
                    "created_at_dt",
                    "total_money_amount",
                    "state",
                ],
                "optional_fields": [
                    "shift_id",
                    "location_id",
                    "reference_id",
                    "customer_id",
                ],
                "relationships": {
                    "vendor": ("main_foodtruck", "shift__truck_id", "id", ["name"]),
                    "location": ("main_location", "shift__location_id", "id", ["name"]),
                },
                "time_field": "created_at_dt",
            },
            "Vendors": {
                "table": "main_foodtruck",
                "essential_fields": ["id", "name", "primary_cuisine"],
                "optional_fields": ["email", "phone", "description", "area_id"],
                "relationships": {"area": ("main_area", "area_id", "id", ["name"])},
            },
            # 'Locations': {
            #     'table': 'main_location',
            #     'essential_fields': ['id', 'name', 'street_number_and_name'],
            #     'optional_fields': ['event_planner_id', 'area_id', 'description'],
            #     'relationships': {
            #         'area': ('main_area', 'area_id', 'id', ['name'])
            #     }
            # }
        }

    def _parse_time_reference(self, text: str) -> Optional[Dict[str, datetime]]:
        """Parse time references from natural language"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if "yesterday" in text.lower():
            yesterday = today - timedelta(days=1)
            return {"start": yesterday, "end": today}
        elif "today" in text.lower():
            return {"start": today, "end": today + timedelta(days=1)}
        return None

    def _extract_vendor_name(self, text: str) -> Optional[str]:
        """Extract vendor name from the query text."""
        # Patterns to identify vendor names
        patterns = [
            r"how many orders did ([\w\s]+)",  # E.g., "how many orders did Akita Sushi"
            r"orders for ([\w\s]+)",  # E.g., "orders for Akita Sushi"
            r"([\w\s]+) orders yesterday",  # E.g., "Akita Sushi orders yesterday"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _parse_query_context(self, description: str) -> QueryContext:
        """Parse the query and determine relevant entities and fields"""
        description_lower = description.lower()

        # Map common terms to entities
        entity_mappings = {
            "vendor": "Vendors",
            "vendors": "Vendors",
            "food truck": "Vendors",
            "food trucks": "Vendors",
            "order": "Orders",
            "orders": "Orders",
            "sales": "Orders",
            "revenue": "Orders",
            "location": "Locations",
            "locations": "Locations",
            "property": "Locations",
            "properties": "Locations",
        }

        main_entity = None
        related_entities = []

        # Find main entity and related entities
        for term, entity in entity_mappings.items():
            if term in description_lower:
                if main_entity is None:
                    main_entity = entity
                elif entity not in related_entities and entity != main_entity:
                    related_entities.append(entity)

        # Default to Orders if no entity found
        if not main_entity:
            main_entity = "Orders"

        # Extract vendor name and time range
        vendor_name = self._extract_vendor_name(description)
        time_range = self._parse_time_reference(description)

        return QueryContext(
            main_entity=main_entity,
            related_entities=related_entities,
            time_range=time_range,
            vendor_name=vendor_name,
            metrics=["sales"] if "sales" in description_lower else ["orders"],
        )

    def _build_dynamic_query(self, context: QueryContext) -> Tuple[str, List[Any]]:
        """Build optimized SQL query for Akita Sushi 1 order analysis."""
        entity_info = self.entity_map["Orders"]  # We're focused on orders
        select_fields = []
        joins = []
        where_clauses = []
        parameters = []

        # Essential fields from the Orders table
        table_alias = "main"
        for field in entity_info["essential_fields"]:
            select_fields.append(f"{table_alias}.{field}")

        # Add joins for vendor and location (optional but useful)
        joins.append("LEFT JOIN main_foodtruck ON main.vendor_id = main_foodtruck.id")
        select_fields.append("main_foodtruck.name AS vendor_name")

        # Add filter for Akita Sushi 1 by name
        if context.vendor_name:
            where_clauses.append("LOWER(main_foodtruck.name) = LOWER(%s)")
            parameters.append(context.vendor_name)

        # Add time range filter for 'yesterday'
        if context.time_range:
            where_clauses.append(f"{table_alias}.{entity_info['time_field']} >= %s")
            where_clauses.append(f"{table_alias}.{entity_info['time_field']} < %s")
            parameters.extend([context.time_range["start"], context.time_range["end"]])

        # Construct the final SQL query
        query = f"""
        SELECT {', '.join(select_fields)}
        FROM {entity_info['table']} AS {table_alias}
        {' '.join(joins)}
        {'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}
        ORDER BY {entity_info.get('time_field', 'id')} DESC
        LIMIT 50
        """

        return query, parameters

    def _format_results_for_ai(
        self, query_result: QueryResult, context: QueryContext
    ) -> Dict[str, Any]:
        """Format results with summaries and statistics"""
        if not query_result.is_success:
            return {"status": "error", "message": query_result.error}

        data = query_result.data
        if not data:
            return {
                "status": "success",
                "message": f"No orders found for {context.vendor_name} on the given date.",
                "summary": {
                    "total_records": 0,
                    "total_sales": 0,
                    "average_order": 0.0,
                    "vendor_name": context.vendor_name,
                    "time_range": {
                        "start": context.time_range["start"].isoformat()
                        if context.time_range
                        else None,
                        "end": context.time_range["end"].isoformat()
                        if context.time_range
                        else None,
                    },
                },
            }

        # Generate appropriate summary based on entity type
        summary = self._generate_entity_summary(data, context)

        return {
            "status": "success",
            "data": data,
            "summary": summary,
            "message": f"Analysis completed for {context.main_entity}",
        }

    def _generate_entity_summary(
        self, data: List[Dict[str, Any]], context: QueryContext
    ) -> Dict[str, Any]:
        """Generate entity-specific summaries"""
        if not data:
            return {
                "total_records": 0,
                "total_sales": 0,
                "average_order": 0.0,
                "vendor_name": context.vendor_name,
                "time_range": {
                    "start": context.time_range["start"].isoformat()
                    if context.time_range
                    else None,
                    "end": context.time_range["end"].isoformat()
                    if context.time_range
                    else None,
                },
            }

        summary = {"total_records": len(data)}

        if context.main_entity == "Orders":
            total_amount = sum(
                float(record["total_money_amount"])
                for record in data
                if record.get("total_money_amount")
            )
            summary.update(
                {
                    "total_sales": round(total_amount, 2),
                    "average_order": round(total_amount / len(data), 2) if data else 0,
                    "vendor_name": context.vendor_name,
                    "time_range": {
                        "start": context.time_range["start"].isoformat()
                        if context.time_range
                        else None,
                        "end": context.time_range["end"].isoformat()
                        if context.time_range
                        else None,
                    },
                }
            )

        elif context.main_entity == "Vendors":
            cuisines = {}
            for record in data:
                cuisine = record.get("primary_cuisine")
                if cuisine:
                    cuisines[cuisine] = cuisines.get(cuisine, 0) + 1
            summary["cuisine_distribution"] = cuisines

        elif context.main_entity == "Locations":
            active_locations = len(data)
            summary["active_locations"] = active_locations

        return summary

    async def analyze_data(self, query_description: str) -> Dict[str, Any]:
        try:
            context = self._parse_query_context(query_description)
            query, parameters = self._build_dynamic_query(context)

            result = await self.db_manager.execute_query(
                query=query, parameters=parameters, db_type=DatabaseType.DEFAULT
            )

            # Always format and return the result
            return self._format_results_for_ai(result, context)
        except Exception as e:
            return {"status": "error", "message": f"Failed to analyze data: {str(e)}"}
