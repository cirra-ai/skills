public with sharing class Sdo_Scom_Order_Grid_Controller{
	//Method to get the list of order products owned by the current community user
	@AuraEnabled(cacheable=true)
	public static Sdo_Scom_Order_Grid_Wrapper getOrderProducts(String communityId, String effectiveAccountId, String productIdTest){
		System.debug('Inside OrderGridController  communityId:{}' + communityId);
		System.debug('Inside OrderGridController  acc id:{}' + effectiveAccountId);
		System.debug('Inside OrderGridController  productIdTest:{}' + productIdTest);
		//Return no results if the component isn't run in a community by a community user
		if((communityId == null || effectiveAccountId == null) && productIdTest == null){
			return null;
		}
		
		Id currentUserId = UserInfo.getUserId();
		System.debug('Inside OrderGridController  currentUserId:{}' + currentUserId);
		
		List<OrderItem> orderProducts = [SELECT Id,
		Order.Id,
		Order.OrderedDate,
		Product2.Id,
		Product2.Name,
		Product2.StockKeepingUnit,
		Quantity
		FROM OrderItem
		WHERE Order.OwnerId = :currentUserId
		AND Order.Status = 'Activated'
		ORDER BY Order.OrderedDate DESC];
		
		System.debug('Inside OrderGridController  list of order products:{}'+orderProducts);
		
		
		//Stores the list of order products returned by the SOQL query. This list doesn't doesn't contain the
		//product image information which requires a connect API call.
		List<Sdo_Scom_Order_Product_Wrapper> orderProductWrappers = new List<Sdo_Scom_Order_Product_Wrapper>();
		
		//Stores the list of order products that have product entitlements with their images.
		List<Sdo_Scom_Order_Product_Wrapper> orderProductWrappersTwo = new List<Sdo_Scom_Order_Product_Wrapper>();
		
		Sdo_Scom_Order_Grid_Wrapper orderGridWrapper = new Sdo_Scom_Order_Grid_Wrapper();
		
		if(orderProducts.size() > 0){
			Set<String> productIds = new Set<String>();
			
			//Loops through the order product list and creates the orderProductWrappers list.
			for(OrderItem op: orderProducts){
				Sdo_Scom_Order_Product_Wrapper opw = new Sdo_Scom_Order_Product_Wrapper();
				opw.Id = op.Id;
				opw.orderId = op.Order.Id;
				opw.orderedDate = op.Order.OrderedDate;
				opw.productId = op.Product2.Id;
				opw.productName = op.Product2.Name;
				opw.productSKU = op.Product2.StockKeepingUnit;
				opw.quantity = op.Quantity;
				opw.productImageURL = null;
				orderProductWrappers.add(opw);
				
				productIds.add((String)op.Product2.Id);
			}
			
			List<String> productIdList = new List<String>(productIds);
			List<ConnectApi.ProductDetail> products = new List<ConnectApi.ProductDetail>();
			Map<String,ConnectApi.ProductPrice> productPriceMap = new Map<String,ConnectApi.ProductPrice>();
			String webstoreId = getStoreId(communityId);
			
			//If this method is run in a test class, use the method from the test utility class to get the ConnectApi products.
			//Else, use the method in this class which actually calls the ConnectApi.
			if(Test.isRunningTest()){
				products = getProductsTest(productIdTest);
			}
			else{
				products = getProducts(productIdList, webstoreId, effectiveAccountId);
			}
			for(String productId : productIdList){
				ConnectApi.ProductPrice productPrice;
				System.debug(' Inside for loop product id  :'+ productId);
				try{productPrice = ConnectApi.CommerceStorePricing.getProductPrice(webstoreId, productId, effectiveAccountId);}
				catch(ConnectApi.ConnectApiException e){System.debug('ConnectApi.CommerceStorePricing.getProductPrice ConnectApiException: ' + e);}
				catch(ConnectApi.NotFoundException e){System.debug('ConnectApi.CommerceStorePricing.getProductPrice NotFoundException: ' + e); }
				catch(ConnectApi.RateLimitException e){System.debug('ConnectApi.CommerceStorePricing.getProductPrice RateLimitException: ' + e);}
				productPriceMap.put(productId,productPrice);
			}
			System.debug(' Map :'+ productPriceMap);
			//Loop through the order product wrappers list and then loop through the ConnectApi products to match the records
			//and create the order product wrappers 2 list with the product image URLs.
			for(Integer i = 0; i < orderProductWrappers.size(); i++){
				Boolean productFound = false;
				Sdo_Scom_Order_Product_Wrapper opw = orderProductWrappers[i];
				for(ConnectApi.ProductDetail product : products){
					System.debug('product :{}'+product);
					if(product.id == opw.productId){
						if(product.defaultImage.url != null){
							opw.productImageURL = product.defaultImage.url;
						}
						if(product.variationAttributeSet != null)
						{
							opw.attributeDeveloperName = product.variationAttributeSet.developerName;
							opw.attributeMap = (Map<String,String>)product.variationAttributeSet.attributes;
							opw.attributeSetInfo = (Map<String,ConnectApi.ProductAttributeSetInfo>)product.attributeSetInfo;
						}
						productFound = true;
						break;
					}
				}
				for (String key : productPriceMap.keySet()) {
					System.debug('Inside map');
					if(key == opw.productId){
						if(productPriceMap.get(key) != null){
							ConnectApi.ProductPrice p = productPriceMap.get(key);
							System.debug('Id match :'+p);
							opw.unitPrice = p.unitPrice;
							opw.currencyIsoCode = p.currencyIsoCode ;
						}
					}
				}
				
				if(productFound == true){
					orderProductWrappersTwo.add(opw);
				}
			}
			orderGridWrapper.orderProducts = orderProductWrappersTwo;
			orderGridWrapper.webstoreId = webstoreId;
		}
		else{
			return null;
		}
		
		return orderGridWrapper;
	}
	
	//Method to grab the items in the current user's cart
	@AuraEnabled(cacheable=true)
	public static Sdo_Scom_Cart_Summary_Wrapper getCartSummary(String webstoreId, String effectiveAccountId){
		if(String.isBlank(webstoreId)){
			return null;
		}
		
		ConnectApi.CartItemCollection cartItemCollection;
		Sdo_Scom_Cart_Summary_Wrapper cartSummary = new Sdo_Scom_Cart_Summary_Wrapper();
		List<Sdo_Scom_Cart_Product_Wrapper> cartItems = new List<Sdo_Scom_Cart_Product_Wrapper>();
		
		//Returns a fake cart summary during a test for code coverage
		if(Test.isRunningTest()){
			cartSummary.cartId = 'testCartId1';
			
			Sdo_Scom_Cart_Product_Wrapper cartItem = new Sdo_Scom_Cart_Product_Wrapper();
			cartItem.productId = 'testProductId1';
			cartItem.quantity = 1;
			cartItem.errorMessage = 'testErrorMessage';
			cartItem.requestStatus = 'testRequestStatus';
			cartItems.add(cartItem);
		}
		else{
			try{cartItemCollection = ConnectApi.CommerceCart.getCartItems(webstoreId, effectiveAccountId, 'active');}
			catch(ConnectApi.ConnectApiException e){System.debug('ConnectApi.CommerceCart.getCartItems ConnectApiException: ' + e); return null;}
			catch(ConnectApi.NotFoundException e){System.debug('ConnectApi.CommerceCart.getCartItems NotFoundException: ' + e); return null;}
			catch(ConnectApi.RateLimitException e){System.debug('ConnectApi.CommerceCart.getCartItems RateLimitException: ' + e); return null;}
			
			cartSummary.cartId = cartItemCollection.cartSummary.cartId;
			cartSummary.currencyIsoCode = cartItemCollection.cartSummary.currencyIsoCode;
			cartSummary.totalPrice = cartItemCollection.cartSummary.totalProductAmount;
			cartSummary.totalAmount = cartItemCollection.cartSummary.grandTotalAmount;
			System.debug('cart items collection :'+cartItemCollection);
			System.debug('cart items collection to string :'+cartItemCollection.toString());
			for(ConnectApi.CartItemResult cartItemResult : cartItemCollection.cartItems){
				if(cartItemResult.cartItem != null){
					Sdo_Scom_Cart_Product_Wrapper cartItem = new Sdo_Scom_Cart_Product_Wrapper();
					cartItem.productId = cartItemResult.cartItem.productId;
					cartItem.quantity = Integer.valueOf(cartItemResult.cartItem.quantity);
					cartItem.errorMessage = cartItemResult.message;
					cartItems.add(cartItem);
				}
			}
		}
		
		cartSummary.cartItems = cartItems;
		return cartSummary;
	}
	
	//Method to add selected products to the current user's cart.
	//Returning wrapper classes because I couldn't figure out a way to pull values from a ConnectApi.BatchInput
	//in my test class. Returning a list of ConnectApi.CartItemInput records causes an error on the client side
	//even though there aren't any Apex errors which makes it so I can't do accurate error handling.
	//Returning a list of wrapper classes solves both problems.
	@AuraEnabled
	public static List<Sdo_Scom_Cart_Product_Wrapper> addToCart(String productsJSON, String communityId, String effectiveAccountId){
		String webstoreId = getStoreId(communityId);
		
		List<Object> cartProducts = (List<Object>)JSON.deserializeUntyped(productsJSON);
		List<ConnectApi.BatchInput> batchInputList = new List<ConnectApi.BatchInput>();
		List<Sdo_Scom_Cart_Product_Wrapper> cartItemWrappers = new List<Sdo_Scom_Cart_Product_Wrapper>();
		System.debug('Inside OrderGridController  addToCart communityId:{}' + communityId);
		System.debug('Inside OrderGridController  addToCart acc id:{}' + effectiveAccountId);
		System.debug('Inside OrderGridController addToCart productsJson:{}' + productsJSON);
		//Create the batch input list for the add to cart ConnectApi call and create the cartItemWrappers list
		//that is returned for error handling.
		for(Object cartProduct : cartProducts){
			Map<String, Object> cpObjectMap = (Map<String, Object>)cartProduct;
			ConnectApi.CartItemInput cartItem = new ConnectApi.CartItemInput();
			Sdo_Scom_Cart_Product_Wrapper cartItemWrapper = new Sdo_Scom_Cart_Product_Wrapper();
			
			cartItem.productId = (String)cpObjectMap.get('productId');
			cartItemWrapper.productId = cartItem.productId;
			
			Integer quantity = (Integer)cpObjectMap.get('quantity');
			cartItem.quantity = quantity.format();
			cartItemWrapper.quantity = quantity;
			
			cartItem.type = ConnectApi.CartItemType.Product;
			
			ConnectApi.BatchInput batchInput = new ConnectApi.BatchInput(cartItem);
			batchInputList.add(batchInput);
			cartItemWrappers.add(cartItemWrapper);
		}
		
		//If the method isn't being called within a test class, use the ConnectApi method to add the products
		//to the current user's cart. If there is an error, return null for error handling.
		if(!Test.isRunningTest()){
			try{List<ConnectApi.BatchResult> batchResults = ConnectApi.CommerceCart.addItemsToCart(webstoreId, effectiveAccountId, 'active', batchInputList);}
			catch(ConnectApi.ConnectApiException e){System.debug('ConnectApi.CommerceCatalog.getProduct ConnectApiException: ' + e); return null;}
			catch(ConnectApi.NotFoundException e){System.debug('ConnectApi.CommerceCatalog.getProduct NotFoundException: ' + e); return null;}
			catch(ConnectApi.RateLimitException e){System.debug('ConnectApi.CommerceCatalog.getProduct RateLimitException: ' + e); return null;}
		}
		
		return cartItemWrappers;
	}
	
	//Method that returns the WebStoreId using the passed in community Id or null if no community Id is provided.
	private static String getStoreId(String communityId){
		if(communityId == null){
			return null;
		}
		
		return [SELECT WebStoreId FROM WebStoreNetwork WHERE NetworkId = :communityId LIMIT 1].WebStoreId;
	}
	
	//Method that uses the ConnectApi to get the ConnectApi product detail records which include
	//product images and entitlement information.
	private static List<ConnectApi.ProductDetail> getProducts(List<String> productIdList, String webstoreId, String effectiveAccountId){
		List<ConnectApi.ProductDetail> products = new List<ConnectApi.ProductDetail>();
		
		for(String productId : productIdList){
			try{
				ConnectApi.ProductDetail product = ConnectApi.CommerceCatalog.getProduct(webstoreId, productId, effectiveAccountId, null, false, null, false, false, true);
				products.add(product);
			}
			catch(ConnectApi.ConnectApiException e){
				System.debug('ConnectApi.CommerceCatalog.getProduct ConnectApiException: ' + e);
			}
			catch(ConnectApi.NotFoundException e){
				System.debug('ConnectApi.CommerceCatalog.getProduct NotFoundException: ' + e);
			}
			catch(ConnectApi.RateLimitException e){
				System.debug('ConnectApi.CommerceCatalog.getProduct RateLimitException: ' + e);
			}
		}
		
		return products;
	}
	
	//Method that determines whether the user can access order products.
	@TestVisible
	private static Boolean canReadOrderProducts(){
		Boolean canReadOrderProducts = false;
		if(Schema.sObjectType.OrderItem.isAccessible() && Schema.sObjectType.OrderItem.fields.Quantity.isAccessible()){
			canReadOrderProducts = true;
		}
		return canReadOrderProducts;
	}
	
	//Method that determines whether the user can access orders.
	@TestVisible
	private static Boolean canReadOrders(){
		Boolean canReadOrders = false;
		if(Schema.sObjectType.Order.isAccessible() &&
		Schema.sObjectType.Order.fields.OrderedDate.isAccessible() &&
		Schema.sObjectType.Order.fields.OwnerId.isAccessible()){
			canReadOrders = true;
		}
		return canReadOrders;
	}
	
	//Method that determines whether the user can access products.
	@TestVisible
	private static Boolean canReadProducts(){
		Boolean canReadProducts = false;
		if(Schema.sObjectType.Product2.isAccessible() &&
		Schema.sObjectType.Product2.fields.Name.isAccessible() &&
		Schema.sObjectType.Product2.fields.StockKeepingUnit.isAccessible()){
			canReadProducts = true;
		}
		return canReadProducts;
	}
	
	//Method that determines whether the user can access wen store networks.
	@TestVisible
	private static Boolean canReadWebStoreNetworks(){
		Boolean canReadWebStoreNetworks = false;
		if(Schema.sObjectType.WebStoreNetwork.isAccessible() &&
		Schema.sObjectType.WebStoreNetwork.fields.WebStoreId.isAccessible() &&
		Schema.sObjectType.WebStoreNetwork.fields.NetworkId.isAccessible()){
			canReadWebStoreNetworks = true;
		}
		return canReadWebStoreNetworks;
	}
	
	//Method to return mocked ConnectApi.ProductDetail records for testing.
	private static List<ConnectApi.ProductDetail> getProductsTest(String productId){
		List<ConnectApi.ProductDetail> products = new List<ConnectApi.ProductDetail>();
		
		ConnectApi.ProductDetail product = new ConnectApi.ProductDetail();
		product.Id = productId;
		ConnectApi.ProductMedia pm = new ConnectApi.ProductMedia();
		pm.url = '';
		product.defaultImage = pm;
		products.add(product);
		
		return products;
	}
}