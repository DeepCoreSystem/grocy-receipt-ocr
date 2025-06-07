import requests
import json
import os
import sys
from stdnum import ean
from datetime import date, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

class GrocyClient:
    """
    Client for interacting with the Grocy API to manage products, barcodes, purchases,
    and inventory data.
    """

    def __init__(self, api_url=None, api_key=None):
        """
        Initialize the Grocy client with API credentials.
        
        Args:
            api_url (str, optional): Grocy API URL. If not provided, tries to get from 
                                    GROCY_API_URL environment variable.
            api_key (str, optional): Grocy API key. If not provided, tries to get from 
                                    GROCY_API_KEY environment variable.
                                    
        Raises:
            ValueError: If both arguments and environment variables are missing.
        """
        self.api_url = api_url or os.environ.get('GROCY_API_URL')
        self.api_key = api_key or os.environ.get('GROCY_API_KEY')
        
        if not self.api_url or not self.api_key:
            logger.error("Grocy API URL and API key must be provided")
            raise ValueError("Grocy API URL and API key must be provided")
        
        logger.info(f"Initializing Grocy client with API URL: {self.api_url}")
        
        self.headers = {
            'GROCY-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def find_product_by_barcode(self, barcode):
        """
        Find a product by its barcode.
        
        Args:
            barcode (str): The product barcode to search for.
            
        Returns:
            dict: Product data if found, None otherwise.
        """
        logger.info(f"Finding product by barcode: {barcode}")
        url = f"{self.api_url}/stock/products/by-barcode/{barcode}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json() or None
        except Exception as e:
            logger.error(f"Error finding product by barcode: {e}")
            return None
        
    def products_for_group(self, product_group_id):
        """
        Get all products belonging to a specific product group.
        
        Args:
            product_group_id (int): The ID of the product group.
            
        Returns:
            list: List of products in the group, empty list if none found or error occurs.
        """
        logger.info(f"Finding products by group: {product_group_id}")
        url = f"{self.api_url}/objects/products?query%5B%5D=product_group_id%3D{product_group_id}&order=name%3Aasc"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json() or []
        except Exception as e:
            logger.error(f"Error finding products by group: {e}")
            return []
    
    def get_product_categories(self):
        """
        Retrieve all product categories/groups from Grocy.
        
        Returns:
            list: List of product categories, empty list if error occurs.
        """
        url = f"{self.api_url}/objects/product_groups"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting product categories: {e}")
            return []

    def get_locations(self):
        """
        Retrieve all storage locations from Grocy.
        
        Returns:
            list: List of locations, empty list if error occurs.
        """
        url = f"{self.api_url}/objects/locations"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting locations: {e}")
            return []

    def get_quantity_units(self):
        """
        Retrieve all quantity units from Grocy.
        
        Returns:
            list: List of quantity units, empty list if error occurs.
        """
        url = f"{self.api_url}/objects/quantity_units"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting quantity units: {e}")
            return []

    def get_shopping_locations(self):
        """
        Retrieve all shopping locations from Grocy.
        
        Returns:
            list: List of shopping locations, empty list if error occurs.
        """
        url = f"{self.api_url}/objects/shopping_locations"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting shopping locations: {e}")
            return []
        
    def external_lookup(self, barcode):
        """
        Perform an external barcode lookup.
        
        Args:
            barcode (str): The barcode to look up.
            
        Returns:
            dict: External product data if found, empty dict if error occurs.
        """
        url = f"{self.api_url}/stock/barcodes/external-lookup/{barcode}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error performing external barcode lookup: {e}")
            return {}

    def create_product(self, product_data):
        """
        Create a new product in Grocy.
        
        Args:
            product_data (dict): Dictionary containing product data including:
                - name (str): Product name
                - description (str, optional): Product description
                - product_group_id (int): Category ID
                - location_id (int): Storage location ID
                - qu_id_purchase (int): Purchase quantity unit ID
                - qu_id_stock (int): Stock quantity unit ID
                - barcode (str, optional): Product barcode
                - out_of_stock_default (bool, optional): Treat opened as out of stock
                
        Returns:
            dict: Created product data if successful, error dict otherwise.
        """
        url = f"{self.api_url}/objects/products"
        logger.info(f"Creating product with data: {product_data}")
        
        grocy_product = {
            'name': product_data['name'],
            'description': product_data.get('description', ''),
            'product_group_id': product_data.get('product_group_id'),
            'location_id': product_data.get('location_id'),
            'qu_id_purchase': product_data.get('qu_id_purchase'),
            'qu_id_stock': product_data.get('qu_id_stock'),
            'treat_opened_as_out_of_stock': product_data.get('out_of_stock_default', False),
        }

        try:
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(grocy_product)
            )
            
            if response.status_code == 400:
                error_msg = response.json().get('error')
                logger.error(f"Error creating product: {error_msg}")
                return {'error': error_msg}
            
            product_id = response.json().get('created_object_id')
            product = self.get_product(product_id)
        except Exception as e:
            logger.error(f"Error creating product, trying to find by name: {e}")
            product = self.get_product_by_name(product_data['name'])
            
        if product and 'barcode' in product_data:
            barcode_response = self.add_barcode_to_product(
                product['id'],
                product_data['barcode'],
                {'note': product_data['name']}
            )
            if 'error' in barcode_response:
                return {'error': barcode_response['error']}

        return product or None

    def add_barcode_to_product(self, product_id, barcode, assignments):
        """
        Add a barcode to an existing product.
        
        Args:
            product_id (int): ID of the product to add barcode to
            barcode (str): Barcode to add
            assignments (dict): Additional barcode data including:
                - shopping_location_id (int, optional)
                - note (str, optional)
                - display_amount (float, optional): Defaults to 1
                
        Returns:
            dict: Barcode data if successful, error dict otherwise.
        """
        url = f"{self.api_url}/objects/product_barcodes"
        standardized_barcode = self.normalize_receipt_barcode(barcode)
        
        grocy_barcode = {
            'shopping_location_id': assignments.get('shopping_location_id', ''),
            'note': assignments.get('note', ''),
            'barcode': standardized_barcode,
            'product_id': product_id,
            'amount': assignments.get('display_amount', 1),
        }
        logger.info(f"Adding barcode: {grocy_barcode}")

        try:
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(grocy_barcode)
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error adding barcode to product: {e}")
            return {'error': str(e)}
    
    def get_product(self, product_id):
        """
        Get product details by ID.
        
        Args:
            product_id (int): The product ID to retrieve.
            
        Returns:
            dict: Product data if found, None otherwise.
        """
        url = f"{self.api_url}/objects/products/{product_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting product: {e}")
            return None
    
    def get_product_details(self, product_id):
        """
        Get detailed stock information for a product.
        
        Args:
            product_id (int): The product ID to retrieve details for.
            
        Returns:
            dict: Detailed product data if found, None otherwise.
        """
        url = f"{self.api_url}/stock/products/{product_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return None
        
    def get_all_products(self):
        """
        Retrieve all products from Grocy.
        
        Returns:
            list: List of all products, None if error occurs.
        """
        url = f"{self.api_url}/objects/products"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting all products: {e}")
            return None
        
    def get_product_by_name(self, product_name):
        """
        Find a product by its exact name.
        
        Args:
            product_name (str): The exact product name to search for.
            
        Returns:
            dict: Product data if found, None otherwise.
        """
        products = self.get_all_products()
        return next((p for p in products if p.get('name') == product_name), None)
    
    def get_quantity_unit_conversions(self):
        """
        Retrieve all quantity unit conversion factors.
        
        Returns:
            list: List of unit conversions, empty list if error occurs.
        """
        url = f"{self.api_url}/objects/quantity_unit_conversions"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting quantity unit conversions: {e}")
            return []

    def add_purchase(self, purchase_data):
        """
        Record a product purchase in Grocy.
        
        Args:
            purchase_data (dict): Dictionary containing:
                - product_id (int): ID of purchased product
                - amount (float): Purchase amount
                - days_out (int): Days until expiration
                - shopping_location_id (int): Purchase location ID
                - price (float, optional): Purchase price
                
        Returns:
            dict: Purchase data if successful, error dict otherwise.
        """
        product_data = self.get_product_details(purchase_data['product_id'])
        logger.info(f"Adding purchase for product {product_data} with data {purchase_data}")

        url = f"{self.api_url}/stock/products/{purchase_data['product_id']}/add"
        
        expiration_date = (date.today() + timedelta(days=purchase_data['days_out'])).isoformat()
        calc_amount = purchase_data['amount'] * product_data['qu_conversion_factor_purchase_to_stock']
        calc_price = purchase_data.get('price', 0) / product_data['qu_conversion_factor_purchase_to_stock']
        
        grocy_purchase = {
            'amount': calc_amount,
            'transaction_type': 'purchase',
            'best_before_date': expiration_date,
            'price': calc_price,
            'shopping_location_id': purchase_data['shopping_location_id'],
        }

        try:
            response = requests.post(
                url,
                headers=self.headers,
                data=json.dumps(grocy_purchase)
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error adding purchase: {e}")
            return {'error': str(e)}
    
    def calculate_upc_check_digit(self, code11):
        """
        Calculate the 12th check digit for an 11-digit UPC code.
        
        Args:
            code11 (str): 11-digit UPC code without check digit.
            
        Returns:
            str: The calculated check digit.
            
        Raises:
            ValueError: If input is not 11 digits.
        """
        if len(code11) != 11 or not code11.isdigit():
            raise ValueError("Input must be an 11-digit string")
        
        total = sum(int(digit) * (3 if i % 2 == 0 else 1) 
                  for i, digit in enumerate(code11))
        return str((10 - (total % 10)) % 10)

    def build_upc_from_receipt(self, receipt_code):
        """
        Convert a 10-digit receipt code to valid 12-digit UPC-A format.
        
        Args:
            receipt_code (str): 10-digit numeric receipt code.
            
        Returns:
            str: 12-digit UPC-A code with leading zero and check digit.
            
        Raises:
            ValueError: If input is not 10 digits.
        """
        if len(receipt_code) != 10 or not receipt_code.isdigit():
            raise ValueError("Expected a 10-digit numeric receipt code")
        
        base_code = "0" + receipt_code
        return base_code + self.calculate_upc_check_digit(base_code)

    def normalize_receipt_barcode(self, receipt_code):
        """
        Normalize a receipt barcode to standard format.
        
        Args:
            receipt_code (str): The barcode to normalize.
            
        Returns:
            str: Normalized barcode (12-digit UPC if input is 10 digits).
        """
        if len(receipt_code) == 10 and receipt_code.isdigit():
            return self.build_upc_from_receipt(receipt_code)
        return receipt_code
        
    def convert_purchase_quantities_to_stock(self, purchase_id, stock_id, amount):
        """
        Convert purchase quantities to stock quantities using conversion factors.
        
        Args:
            purchase_id (int): Purchase unit ID
            stock_id (int): Stock unit ID
            amount (float): Amount to convert
            
        Returns:
            float: Converted amount, or error dict if conversion fails.
        """
        conversions = self.get_quantity_unit_conversions()
        try:
            for conversion in conversions:
                if conversion['from_qu_id'] == purchase_id and conversion['to_qu_id'] == stock_id:
                    return amount * conversion['factor']
            return amount
        except Exception as e:
            logger.error(f"Error converting quantities: {e}")
            return {'error': str(e)}
