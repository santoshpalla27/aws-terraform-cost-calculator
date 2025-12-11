import json
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database configuration (should be env vars in production)
DATABASE_URL = "postgresql://postgres:password@localhost:5432/cloudcost"
# adjust for docker internal networking if needed, but 'localhost' works for local dev tools usually if port forwarded
# Inside docker container, it should be 'db'

class PricingService:
    def __init__(self, db_url: str = DATABASE_URL):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def get_price(self, service_code: str, filters: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Query for the best matching price.
        filters e.g. {'instanceType': 't3.micro', 'location': 'US East (N. Virginia)'}
        """
        session = self.Session()
        try:
            # Construct JSON containment query for attributes
            # We want to find a product that has ALL the requested attributes.
            # AND matches the service code.
            
            # Note: We prioritize OnDemand terms for now.
            
            query = text("""
                SELECT 
                    p.sku, 
                    price.price_per_unit, 
                    price.unit, 
                    price.currency,
                    p.attributes
                FROM products p
                JOIN terms t ON p.sku = t.sku
                JOIN prices price ON t.id = price.term_id
                WHERE p.service_code = :service_code
                AND p.attributes @> :filters
                AND t.type = 'OnDemand'
                ORDER BY price.price_per_unit ASC
                LIMIT 1
            """)
            
            # Ensure filters values are strings to match AWS JSON schema usually
            # But sometimes they are not.
            json_filters = json.dumps(filters)
            
            result = session.execute(query, {"service_code": service_code, "filters": json_filters}).fetchone()
            
            if result:
                return {
                    "sku": result.sku,
                    "price": float(result.price_per_unit),
                    "unit": result.unit,
                    "currency": result.currency,
                    "attributes": result.attributes
                }
            return None
        except Exception as e:
            print(f"Error querying price: {e}")
            return None
        finally:
            session.close()
