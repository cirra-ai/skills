public with sharing class SDO_SCOM_B2B_Product_Compare_TestUtils {
    public static List<Product2> getProducts(List<String> productIdList) {
		List<Product2> productList = [
			SELECT Id, Name, Description, StockKeepingUnit
			FROM Product2
			WHERE Id IN :productIdList
		];

		return productList;
	}
    
	public static List<Product2> productList = null;

	// public static ConnectApi.ProductDetail getProductDetailTest(String productId) {
	// 	ConnectApi.ProductDetail pd = new ConnectApi.ProductDetail();

	// 	Product2 productObj = null;

	// 	for (Product2 product : productList) {
	// 		if (product.Id == productId) {
	// 			productObj = product;
	// 			break;
	// 		}
	// 	}

	// 	pd.id = productObj.Id;

	// 	Map<String, String> fieldsMap = new Map<String, String>();

	// 	fieldsMap.put('StockKeepingUnit', productObj.StockKeepingUnit);
	// 	fieldsMap.put('Name', productObj.Name);
	// 	fieldsMap.put('Description', productObj.Description);
	// 	pd.fields = fieldsMap;

	// 	ConnectApi.ProductEntitlement pe = new ConnectApi.ProductEntitlement();
	// 	pe.canViewPrice = true;
	// 	pd.entitlement = pe;

	// 	ConnectApi.ProductMedia pm = new ConnectApi.ProductMedia();
	// 	pm.id = '1';
	// 	pm.alternateText = 'Coolest product image ever';
	// 	pm.mediaType = ConnectApi.ProductMediaType.Image;
	// 	pm.sortOrder = 1;
	// 	pm.thumbnailUrl = null;
	// 	pm.title = 'Some image';
	// 	pm.url = '/image/path/picture.png';

	// 	List<ConnectApi.ProductMedia> mediaItems = new List<ConnectApi.ProductMedia>();
	// 	mediaItems.add(pm);

	// 	ConnectApi.ProductMediaGroup pmg = new ConnectApi.ProductMediaGroup();
	// 	pmg.developerName = 'productDetailImage';
	// 	pmg.id = '1';
	// 	pmg.mediaItems = mediaItems;

	// 	List<ConnectApi.ProductMediaGroup> mediaGroups = new List<ConnectApi.ProductMediaGroup>();
	// 	mediaGroups.add(pmg);

	// 	return pd;
	// }

	public static Map<String, List<PricebookEntry>> pricebookEntryMap = null;

	public static Map<String, List<PricebookEntry>> getPricebookEntries(List<String> productIdList) {
		pricebookEntryMap = new Map<String, List<PricebookEntry>>();

		List<PricebookEntry> allPricebookEntries = [
			SELECT
				Id,
				Name,
				UnitPrice,
				Pricebook2Id,
				Pricebook2.IsStandard,
				Product2Id,
				UseStandardPrice
			FROM PricebookEntry
			WHERE Product2Id IN :productIdList
		];

		for (PricebookEntry pbe : allPricebookEntries) {
			List<PricebookEntry> pricebookEntries = null;
			String productId = pbe.Product2Id;

			if (pricebookEntryMap.containsKey(productId)) {
				pricebookEntries = pricebookEntryMap.get(productId);
			} 
            else {
				pricebookEntries = new List<PricebookEntry>();
			}
			pricebookEntries.add(pbe);
			pricebookEntryMap.put(productId, pricebookEntries);
		}
		return pricebookEntryMap;
	}

	public static ConnectApi.PricingResult getProductPricingTest(List<String> productIdList) {
		ConnectApi.PricingResult result = new ConnectApi.PricingResult();

		List<ConnectApi.PricingResultLineItem> pricingLineItemResults = new List<ConnectApi.PricingResultLineItem>();

		for (String productId : productIdList) {
			if (pricebookEntryMap.containsKey(productId)) {
				ConnectApi.PricingResultLineItem pricingResultLineItem = new ConnectApi.PricingResultLineItem();
				List<PricebookEntry> pricebookEntries = pricebookEntryMap.get(
					productId
				);

				for (PricebookEntry pbe : pricebookEntries) {
					if (pbe.Pricebook2.IsStandard) {
						pricingResultLineItem.ListPrice = String.valueOf(pbe.UnitPrice);
					} 
                    else {
						pricingResultLineItem.UnitPrice = String.valueOf(pbe.UnitPrice);
						pricingResultLineItem.pricebookEntryId = pbe.Id;
					}

					if (productId.length() > 15) {
						pricingResultLineItem.productId = productId.substring(0, 15);
					} 
                    else {
						pricingResultLineItem.productId = productId;
					}
				}

				pricingResultLineItem.error = null;
				pricingResultLineItem.success = true;
				pricingLineItemResults.add(pricingResultLineItem);
			}
		}
		result.error = null;
		result.success = true;
		result.pricingLineItemResults = pricingLineItemResults;

		return result;
	}
}