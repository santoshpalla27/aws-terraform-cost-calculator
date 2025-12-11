import requests
import json
import psycopg2
import os
from psycopg2.extras import execute_batch

# Configuration
SERVICES = ['AmazonEC2', 'AmazonRDS', 'AmazonS3', 'AWSLambda']
REGION_CODE = 'us-east-1' # Default region for prototype to save bandwidth
DB_HOST = "localhost"
DB_NAME = "cloudcost"
DB_USER = "postgres"
DB_PASS = "password"

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def sync_service(service_code):
    print(f"Syncing {service_code}...")
    
    # 1. Get Region Index to find the URL for the specific region
    # This prevents downloading the massive Global file
    region_index_url = f"https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/{service_code}/current/region_index.json"
    
    try:
        r = requests.get(region_index_url)
        r.raise_for_status()
        data = r.json()
        
        region_data = data['regions'].get(REGION_CODE)
        if not region_data:
            print(f"Region {REGION_CODE} not found for {service_code}")
            return

        current_version_url = "https://pricing.us-east-1.amazonaws.com" + region_data['currentVersionUrl']
        print(f"Downloading {current_version_url}...")
        
        # Stream download
        r_price = requests.get(current_version_url, stream=True)
        r_price.raise_for_status()
        
        # Load JSON (Optimization: In a real giant app, use ijson to stream parse. 
        # For prototype with single region, requests.json() is usually okay ~50-100MB)
        full_data = r_price.json()
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        products = []
        terms_data = []
        prices_data = []
        
        # 2. Process Products
        print("Processing products...")
        for sku, product in full_data['products'].items():
            attributes = product.get('attributes', {})
            # Add service code if missing
            
            products.append((
                sku,
                service_code,
                attributes.get('location'), # e.g. "US East (N. Virginia)" 
                json.dumps(attributes),
                product.get('productFamily'),
                # service_type is flexible
                attributes.get('servicecode', service_code) 
            ))
            
        # Bulk Insert Products
        execute_batch(cur, """
            INSERT INTO products (sku, service_code, region, attributes, family, service_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (sku) DO NOTHING;
        """, products)
        
        # 3. Process Terms
        print("Processing terms...")
        # Structure: terms -> OnDemand -> SKU -> ArbitraryKey -> priceDimensions -> ArbitraryKey -> pricePerUnit
        
        for term_type in ['OnDemand', 'Reserved']:
            term_root = full_data.get('terms', {}).get(term_type, {})
            
            for sku, offers in term_root.items():
                for offer_code, offer in offers.items():
                    # Terms table
                    term_id = f"{sku}-{term_type}" # Simplified ID for this prototype
                    # AWS term IDs are basically the offer_code (e.g. "JRTCKXETXF.6YS6EN2CT7")
                    # but we want to map easily. Let's use the AWS offer SKU (key)
                    
                    real_term_id = str(offer.get('offerTermCode'))
                    if not real_term_id: real_term_id = offer_code # Fallback
                    
                    # We need a unique ID for our table. 
                    # Actually, raw offer_code is unique PER SKU.
                    # Let's use `offer_code` from the JSON (the key like 'JRTCKXETXF.JRTCKXETXF') 
                    # as the term ID.
                    
                    terms_data.append((
                        offer_code,
                        sku,
                        term_type,
                        offer.get('offerTermCode'),
                        json.dumps(offer.get('termAttributes', {}))
                    ))
                    
                    # Prices
                    for dim_key, dim in offer.get('priceDimensions', {}).items():
                        # price per unit
                        ppu_map = dim.get('pricePerUnit', {})
                        usd_price = ppu_map.get('USD', '0')
                        
                        prices_data.append((
                            dim_key, # rate_code
                            offer_code, # term_id
                            dim.get('unit'),
                            float(usd_price),
                            'USD',
                            dim.get('description'),
                            json.dumps(dim.get('appliesTo', []))
                        ))

        # Bulk Insert Terms
        execute_batch(cur, """
            INSERT INTO terms (id, sku, type, code, attributes)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, terms_data)

        # Bulk Insert Prices
        execute_batch(cur, """
            INSERT INTO prices (id, term_id, unit, price_per_unit, currency, description, applies_to)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, prices_data)
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"Finished {service_code}.")

    except Exception as e:
        print(f"Failed to sync {service_code}: {e}")

if __name__ == "__main__":
    print("Starting Pricing Sync (US-East-1 Only)...")
    for service in SERVICES:
        sync_service(service)
    print("Sync Complete.")
