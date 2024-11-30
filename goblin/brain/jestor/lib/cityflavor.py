import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from brain.jestor.lib.database import QueryResult, DatabaseType

logger = logging.getLogger(__name__)


@dataclass
class QueryContext:
    """
    Stores context about what the query is trying to achieve, helping the AI
    understand how to structure complex queries and combine data effectively.
    """
    main_entity: str  # e.g., 'orders', 'vendors', 'properties'
    related_entities: List[str]  # related tables needed
    time_range: Optional[Dict[str, datetime]] = None
    filters: Dict[str, Any] = None
    metrics: List[str] = None


class CityFlavorQueryTool:
    """
    Provides a flexible interface for AI to query the database system with
    built-in understanding of the data model and relationships.
    """
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._setup_entity_relationships()
        
        # Validate entity map
        required_entities = {'Orders', 'Vendors', 'Locations'}
        actual_entities = set(self.entity_map.keys())
        missing_entities = required_entities - actual_entities
        
        if missing_entities:
            logger.error(f"Missing required entities in entity map: {missing_entities}")
            raise ValueError(f"Entity map is missing required entities: {missing_entities}")
            
        logger.info(f"CityFlavorQueryTool initialized with entities: {actual_entities}")
    def _setup_entity_relationships(self):
        """Define the data model relationships for the AI to understand"""
        self.entity_map = {
            'Orders': {
                'table': 'main_orders',
                'key_fields': ['id', 'created_at', 'total_amount', 'shift_id', 'location_id', 'reference_id', 'customer_id', 'state'],
                'relationships': {
                    'shift': ('main_shifts', 'shift_id', 'id'),
                    'items': ('main_orderitem', 'id', 'order_id'),
                    'vendor': ('main_foodtruck', 'shift__truck_id', 'id'),
                    'location': ('main_location', 'shift__location_id', 'id'),
                    'taxes': ('main_tax', 'id', 'order_id'),
                    'tenders': ('main_tender', 'id', 'order_id'),
                    'refunds': ('main_refund', 'id', 'order_id')
                },
                'time_field': 'created_at'
            },
            'Vendors': {
                'table': 'main_foodtruck',
                'key_fields': ['id', 'name', 'contact_email', 'contact_phone', 'description', 'area_id', 'primary_cuisine'],
                'relationships': {
                    'shifts': ('main_shifts', 'id', 'truck_id'),
                    'orders': ('main_orders', 'shift__truck_id', 'id'), 
                    'locations': ('main_location', 'shift__location_id', 'id'),
                    'menus': ('main_menu', 'id', 'truck_id'),
                    'area': ('main_area', 'area_id', 'id')
                }
            },
            'Locations': {
                'table': 'main_location', 
                'key_fields': ['id', 'name', 'event_planner_id', 'area_id', 'description', 'street_number_and_name'],
                'relationships': {
                    'event_planner': ('main_eventplanner', 'event_planner_id', 'id'),
                    'area': ('main_area', 'area_id', 'id'),
                    'shifts': ('main_shifts', 'id', 'location_id'),
                    'vendors': ('main_foodtruck', 'shift__location_id', 'truck_id')
                }
            },
            'Shifts': {
                'table': 'main_shifts',
                'key_fields': ['id', 'day', 'start_time', 'end_time', 'truck_id', 'location_id', 'confirmed_shift'],
                'relationships': {
                    'vendor': ('main_foodtruck', 'truck_id', 'id'),
                    'location': ('main_location', 'location_id', 'id'), 
                    'orders': ('main_orders', 'id', 'shift_id'),
                    'payments': ('main_payment', 'id', 'shift_id')
                },
                'time_field': 'day'
            },
            'OrderItems': {
                'table': 'main_orderitem',
                'key_fields': ['id', 'name', 'quantity', 'base_price_money_amount', 'total_money_amount'],
                'relationships': {
                    'order': ('main_orders', 'order_id', 'id'),
                    'category': ('main_orderitemcategory', 'order_item_category_id', 'id'),
                    'modifiers': ('main_modifier', 'id', 'orderitem_id'),
                    'taxes': ('main_tax', 'id', 'orderitem_id')
                }
            }
        }
    async def analyze_data(self, query_description: str) -> Dict[str, Any]:
        """
        Main entry point for AI to analyze data based on natural language description.
        Automatically determines appropriate query structure and executes it.
        """
        # Parse the query description to understand what data is needed
        context = self._parse_query_context(query_description)
        
        # Build and execute the appropriate query
        query, parameters = self._build_dynamic_query(context)
        
        result = await self.db_manager.execute_query(
            query=query,
            parameters=parameters,
            db_type=DatabaseType.DB1  # Or appropriate database
        )
        
        # Format the results in a way that's easy for the AI to interpret
        return self._format_results_for_ai(result, context)

    def _parse_query_context(self, description: str) -> QueryContext:
        """
        Analyze the natural language query to determine what data is needed.
        Ensures case-matching with entity map keys.
        """
        context = QueryContext(
            main_entity='',
            related_entities=[]
        )
        
        # Convert description to lowercase for consistent matching
        description_lower = description.lower()
        
        # Map common terms to their proper entity names
        entity_mappings = {
            'vendor': 'Vendors',
            'vendors': 'Vendors',
            'food truck': 'Vendors',
            'food trucks': 'Vendors',
            'order': 'Orders',
            'orders': 'Orders',
            'location': 'Locations',
            'locations': 'Locations',
            'property': 'Locations',
            'properties': 'Locations'
        }
        
        # Find the main entity being queried
        for term, entity in entity_mappings.items():
            if term in description_lower:
                context.main_entity = entity
                # Look for related entities
                for other_term, other_entity in entity_mappings.items():
                    if other_term in description_lower and other_entity != entity:
                        context.related_entities.append(other_entity)
                break
        
        # If no entity was found, default to Orders
        if not context.main_entity:
            context.main_entity = 'Orders'
            
        logger.debug(f"Parsed query context: Main entity: {context.main_entity}, Related entities: {context.related_entities}")
        
        return context

    def _build_dynamic_query(self, context: QueryContext) -> tuple[str, List[Any]]:
        """
        Construct a SQL query based on the analysis context.
        This method handles joining related tables and applying filters.
        """
        entity_info = self.entity_map[context.main_entity]
        select_fields = []
        joins = []
        parameters = []
        
        # Add main entity fields
        for field in entity_info['key_fields']:
            select_fields.append(f"{entity_info['table']}.{field}")
        
        # Add related entity joins
        for related in context.related_entities:
            relation = entity_info['relationships'].get(related)
            if relation:
                table, key = relation
                joins.append(f"LEFT JOIN {table} ON {key}")
                
        # Build the query
        query = f"""
        SELECT {', '.join(select_fields)}
        FROM {entity_info['table']}
        {' '.join(joins)}
        """
        
        return query, parameters

    def _format_results_for_ai(
        self, 
        query_result: QueryResult, 
        context: QueryContext
    ) -> Dict[str, Any]:
        """
        Format the database results in a way that's easy for the AI to understand
        and explain to users.
        """
        if not query_result.is_success:
            return {
                'status': 'error',
                'message': query_result.error,
                'context': vars(context)
            }
        
        return {
            'status': 'success',
            'data': query_result.data,
            'summary': self._generate_data_summary(query_result.data),
            'context': vars(context),
            'metadata': {
                'row_count': query_result.row_count,
                'queried_entities': [context.main_entity] + context.related_entities
            }
        }

    def _generate_data_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of the data for the AI to use in explanations"""
        if not data:
            return {'message': 'No data found'}
            
        return {
            'total_records': len(data),
            'sample_fields': list(data[0].keys()) if data else [],
            'has_more': len(data) >= 1000  # Indicate if results might be truncated
        }
