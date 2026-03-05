public with sharing class SDO_SCOM_B2B_Product_Compare_Controller {
    @AuraEnabled
    public static Map<String, String> fetchInitValues(String communityId, String effectiveAccountId) {
        Map<String, String> responseMap = new Map<String, String>();
        String webstoreId = resolveCommunityIdToWebstoreId(communityId);

        responseMap.put('webstoreId', webstoreId);
        responseMap.put('effectiveAccountId', effectiveAccountId);

        return responseMap;
    }

    @AuraEnabled
    public static String resolveCommunityIdToWebstoreId(String communityId) {
        if(communityId == null || communityId == '') {
            return null;
        }
        
        String webstoreId = null;
        List<WebStoreNetwork> wsnList = new List<WebStoreNetwork>();

        if(Schema.sObjectType.WebStoreNetwork.fields.WebStoreId.isAccessible()
            && Schema.sObjectType.WebStoreNetwork.fields.NetworkId.isAccessible()) {
                wsnList = [SELECT WebStoreId FROM WebStoreNetwork WHERE NetworkId = :communityId];
        }

        if(wsnList.size() > 0) {
            WebStoreNetwork wsn = wsnList.get(0);
            webstoreId = wsn.WebStoreId;
        }
        return webstoreId;
    }

    @AuraEnabled
	public static Map<String, Object> getProducts(
		List<String> productIdList,
		Boolean displayPrices,
		String webstoreId,
		String effectiveAccountId,
		List<String> facetFields
	) {
		System.debug('productIdList: ' + productIdList);
		System.debug('displayPrices: ' + displayPrices);
		System.debug('webstoreId: ' + webstoreId);
		System.debug('effectiveAccountId: ' + effectiveAccountId);

		Map<String, Object> responseMap = new Map<String, Object>();
        List<Object> productList = null;

		try {
			if (productIdList.size() > 0) {
				List<Map<String, Object>> facetableAttributeList = getFacetableFieldList(facetFields);

				responseMap.put('facetableAttributeSettings', facetableAttributeList);
				productList = getProductDetails(productIdList, webstoreId, effectiveAccountId, facetFields);

				System.debug('productList: ' + JSON.serialize(productList));
				if (displayPrices) {
					getProductPrices(productList, webstoreId, effectiveAccountId);
				}
			}
		} catch (Exception e) {
			System.debug('Exception: ' + e.getMessage());
            System.debug('Line #: ' + e.getLineNumber());
            System.debug(e.getStackTraceString());

			throw new AuraHandledException(e.getMessage());
		}
        responseMap.put('products', productList);
		return responseMap;
	}

	private static List<Object> getProductDetails(
		List<String> productIdList,
		String webstoreId,
		String effectiveAccountId,
		List<String> facetFields
	) {
		System.debug('getProductDetails() - begin');

		Boolean excludeFields = false;
		List<String> mediaGroups = new List<String>();
		Boolean excludeMedia = false;
		Boolean excludeEntitlementDetails = true;
		Boolean excludePrimaryProductCategory = true;
		Boolean excludeVariationInfo = true;
		Boolean excludeAttributeSetInfo = true;

		List<String> fields = new List<String>();
		fields.add('StockKeepingUnit');
		fields.add('Name');
		fields.add('Description');

		for(String facetField : facetFields) {
			fields.add(facetField);
		}

		List<Map<String, Object>> productList = new List<Map<String, Object>>();

		for (String productId : productIdList) {

			ConnectApi.ProductDetail detail = null;

			if (Test.isRunningTest() == false) {
				detail = ConnectApi.CommerceCatalog.getProduct(
					webstoreId,
					productId,
					effectiveAccountId,
					fields,
					excludeFields,
					mediaGroups,
					excludeMedia,
					excludeEntitlementDetails,
					excludePrimaryProductCategory,
					excludeVariationInfo, excludeAttributeSetInfo
				);
			} 
            else {
				if (SDO_SCOM_B2B_Product_Compare_TestUtils.productList == null) {
					SDO_SCOM_B2B_Product_Compare_TestUtils.productList = SDO_SCOM_B2B_Product_Compare_TestUtils.getProducts(productIdList);
				}
				// detail = SDO_SCOM_B2B_Product_Compare_TestUtils.getProductDetailTest(productId);
			}

			Map<String, Object> productMap = new Map<String, Object>();
			productMap.put('productDetail', detail);
			productList.add(productMap);
		}
		return productList;
	}

	private static void getProductPrices(
		List<Object> productList,
		String webstoreId,
		String effectiveAccountId
	) {
		System.debug('getProductPrices() - begin');

		List<ConnectApi.PricingLineItemInput> pricingLineItems = new List<ConnectApi.PricingLineItemInput>();
		ConnectApi.PricingInput pricingInput = new ConnectApi.PricingInput();

		for (Object obj : productList) {
			Map<String, Object> productMap = (Map<String, Object>) obj;
            ConnectApi.ProductDetail productDetail = (ConnectApi.ProductDetail)productMap.get('productDetail');
			String productId = productDetail.id;

			System.debug('productId: ' + productId);

			ConnectApi.PricingLineItemInput lineItem = new ConnectApi.PricingLineItemInput();
            
			lineItem.productId = productId;
			pricingLineItems.add(lineItem);
		}

		System.debug('pricingLineItems size = ' + pricingLineItems.size());

		pricingInput.pricingLineItems = pricingLineItems;
		ConnectApi.PricingResult result = null;

		if (Test.isRunningTest() == false) {
			result = ConnectApi.CommerceStorePricing.getProductPrices(webstoreId, effectiveAccountId, pricingInput);
		} 
        else {
			List<String> productIdList = new List<String>();

			for (ConnectApi.PricingLineItemInput lineItem : pricingLineItems) {
				String productId = lineItem.productId;
				productIdList.add(productId);
			}

			if (SDO_SCOM_B2B_Product_Compare_TestUtils.pricebookEntryMap == null) {
				SDO_SCOM_B2B_Product_Compare_TestUtils.pricebookEntryMap = SDO_SCOM_B2B_Product_Compare_TestUtils.getPricebookEntries(productIdList);
			}

			result = SDO_SCOM_B2B_Product_Compare_TestUtils.getProductPricingTest(productIdList);
		}

		List<ConnectApi.PricingResultLineItem> pricingLineItemResults = result.pricingLineItemResults;
		Map<String, ConnectApi.PricingResultLineItem> pricingMap = new Map<String, ConnectApi.PricingResultLineItem>();

		for (ConnectApi.PricingResultLineItem resultLineItem : pricingLineItemResults) {
			String productId = resultLineItem.productId;
			pricingMap.put(productId, resultLineItem);
		}

		for (Object obj : productList) {
			Map<String, Object> productMap = (Map<String, Object>) obj;
			ConnectApi.ProductDetail productDetail = (ConnectApi.ProductDetail)productMap.get('productDetail');
			String productId = productDetail.id;

			if (pricingMap.containsKey(productId)) {
				ConnectApi.PricingResultLineItem resultLineItem = pricingMap.get(productId);
				productMap.put('productPrice', resultLineItem);
			}
		}
	}

	@AuraEnabled
    public static ConnectApi.CartItem addToCart(String webstoreId, String productId, String quantity, String effectiveAccountId) {
  
        System.debug('productId: ' + productId);
        System.debug('quantity: ' + quantity);
        System.debug('effectiveAccountId: ' + effectiveAccountId);
        System.debug('webstoreId: ' + webstoreId);
  
        ConnectApi.CartItemInput cartInput = new ConnectApi.CartItemInput();
        cartInput.productId = productId;
        cartInput.quantity = quantity;
        cartInput.type = ConnectApi.CartItemType.PRODUCT;
  
        ConnectApi.CartItem cartItem = null;
  
        if(Test.isRunningTest() == false) {
            cartItem = ConnectApi.CommerceCart.addItemToCart(webstoreId, effectiveAccountId, 'active', cartInput);
        }
  
        return cartItem;
    }

	private static Map<String, Map<String, Object>> getFacetableFieldMap(List<String> facetFields) {
		Map<String, Map<String, Object>> facetableAttributeSettings = new Map<String, Map<String, Object>>();
		Set<String> facetFieldSet = new Set<String>();
		facetFieldSet.addAll(facetFields);

		String[] types = new String[]{'Product2'};

		Schema.DescribeSobjectResult[] results = Schema.describeSObjects(types);
		System.debug('Got describe information for ' + results.size() + ' sObjects.');

		for(Schema.DescribeSobjectResult res : results) {
			Map<String, SObjectField> fields = res.fields.getMap();
			
            for(String key : fields.keySet()) {
				Map<String, Object> facetField = new Map<String, Object>();
				SObjectField field = fields.get(key);
				Schema.DescribeFieldResult dfr = field.getDescribe();

				String name = dfr.getName();

				if(facetFieldSet.contains(name) == false) {
					continue;
				}

				String label = dfr.getLabel();
				String type = null;

				Schema.DisplayType dt = dfr.getType();

				switch on dfr.getType() {
					when MultiPicklist {
						type = 'MultiPicklist';
					}
					when Picklist {
						type = 'Picklist';
					}
					when Boolean {
						type = 'Boolean';
					}
					when String {
						type = 'String';
					}
					when Long {
						type = 'Long';
					}
					when Integer {
						type = 'Integer';
					}
					when else {
						System.debug('default');
					}
				}

				System.debug('sObject Label: ' + res.getLabel());
				System.debug('Number of fields: ' + res.fields.getMap().size());
				System.debug(res.isCustom() ? 'This is a custom object.' : 'This is a standard object.');

				facetField.put('label', label);
				facetField.put('name', name);
				facetField.put('type', type);
				facetableAttributeSettings.put(name, facetField);
			}
		}
		return facetableAttributeSettings;
	}

	private static List<Map<String, Object>> getFacetableFieldList(List<String> facetFields) {
		List<Map<String, Object>> facetableAttributeList = new List<Map<String, Object>>();
		Set<String> facetFieldSet = new Set<String>();
		facetFieldSet.addAll(facetFields);

		String[] types = new String[]{'Product2'};
		Schema.DescribeSobjectResult[] results = Schema.describeSObjects(types);

		System.debug('Got describe information for ' + results.size() + ' sObjects.');

		for(Schema.DescribeSobjectResult res : results) {
			Map<String, SObjectField> fields = res.fields.getMap();
			
            for(String key : fields.keySet()) {
				Map<String, Object> facetField = new Map<String, Object>();
				SObjectField field = fields.get(key);
				Schema.DescribeFieldResult dfr = field.getDescribe();
				String name = dfr.getName();

				if(facetFieldSet.contains(name) == false) {
					continue;
				}

				String label = dfr.getLabel();
				String type = null;

				Schema.DisplayType dt = dfr.getType();

				switch on dfr.getType() {
					when MultiPicklist {
						type = 'MultiPicklist';
					}
					when Picklist {
						type = 'Picklist';
					}
					when Boolean {
						type = 'Boolean';
					}
					when String {
						type = 'String';
					}
					when Long {
						type = 'Long';
					}
					when Integer {
						type = 'Integer';
					}
					when else {
						System.debug('default');
					}
				}

				System.debug('sObject Label: ' + res.getLabel());
				System.debug('Number of fields: ' + res.fields.getMap().size());
				System.debug(res.isCustom() ? 'This is a custom object.' : 'This is a standard object.');

				facetField.put('label', label);
				facetField.put('name', name);
				facetField.put('type', type);

				facetableAttributeList.add(facetField);
			}
	    }

		return facetableAttributeList;
    }
    public class CustomException extends Exception {}
}